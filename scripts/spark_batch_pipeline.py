import os
import time
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

print("==================================================================================================================")
print("[-] KHỞI ĐỘNG ĐƯỜNG ỐNG XỬ LÝ DỮ LIỆU LỚN VỚI APACHE SPARK")
print("==================================================================================================================")

start_time = time.time()

spark = SparkSession.builder \
    .appName("PUBG_BigData_Batch_Pipeline") \
    .master("local[*]") \
    .config("spark.driver.memory", "2g") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

print("[-] Đang nạp dữ liệu thi đấu vào Spark DataFrame...")
agg_path = os.path.join(DATASET_DIR, "agg_match_stats_300k.csv")
kills_path = os.path.join(DATASET_DIR, "kill_match_stats_300k.csv")

df_agg_spark = spark.read.csv(agg_path, header=True, inferSchema=True)
df_kills_spark = spark.read.csv(kills_path, header=True, inferSchema=True)

df_agg_spark = df_agg_spark.toDF(*[c.strip() for c in df_agg_spark.columns])
df_kills_spark = df_kills_spark.toDF(*[c.strip() for c in df_kills_spark.columns])

print("[-] Đang làm sạch và chuẩn hóa dữ liệu phân tán...")
df_agg_clean = df_agg_spark.select(
    F.col("match_id"),
    F.col("player_name"),
    F.col("player_kills").cast("double"),
    F.col("player_dmg").cast("double"),
    F.col("player_dist_walk").cast("double"),
    F.col("player_survive_time").cast("double")
).dropna()

print("[-] Đang huấn luyện mô hình K-means phân tán bằng Spark MLlib...")
feature_cols = ['player_kills', 'player_dmg', 'player_dist_walk', 'player_survive_time']
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw")
df_features = assembler.transform(df_agg_clean)

scaler = StandardScaler(inputCol="features_raw", outputCol="features", withStd=True, withMean=True)
scaler_model = scaler.fit(df_features)
df_scaled = scaler_model.transform(df_features)

kmeans = KMeans(featuresCol="features", k=4, seed=42)
model = kmeans.fit(df_scaled)
predictions = model.transform(df_scaled)

evaluator = ClusteringEvaluator(featuresCol="features", metricName="silhouette", distanceMeasure="squaredEuclidean")
silhouette = evaluator.evaluate(predictions)
print(f"[OK] Huấn luyện hoàn tất! Hệ số Silhouette của mô hình Spark MLlib: {silhouette:.4f}")

print("[-] Đang tổng hợp hiệu suất vũ khí bằng Spark SQL...")
df_kills_spark.createOrReplaceTempView("kills_table")
weapon_stats = spark.sql("""
    SELECT 
        TRIM(killed_by) AS weapon_name,
        COUNT(*) AS total_kills,
        ROUND(AVG(SQRT(POW(killer_position_x - victim_position_x, 2) + POW(killer_position_y - victim_position_y, 2)) / 100), 2) AS avg_distance_m
    FROM kills_table
    WHERE killed_by NOT IN ('Down and Out', 'Bluezone', 'Redzone', 'Drown', 'Falling', 'Punch')
      AND killer_position_x IS NOT NULL AND victim_position_x IS NOT NULL
    GROUP BY TRIM(killed_by)
    ORDER BY total_kills DESC
    LIMIT 10
""")

print()
print("KẾT QUẢ PHÂN TÍCH VŨ KHÍ TỪ APACHE SPARK:")
weapon_stats.show()

parquet_output = os.path.join(DATASET_DIR, "processed_parquet")
print(f"[-] Đang lưu trữ dữ liệu đã chuẩn hóa sang định dạng Parquet tại: {parquet_output}")
df_agg_clean.limit(200000).write.mode("overwrite").parquet(parquet_output)

elapsed = time.time() - start_time
print("==================================================================================================================")
print(f"[OK] ĐƯỜNG ỐNG APACHE SPARK HOÀN TẤT THÀNH CÔNG TRONG {elapsed:.2f} GIÂY!")
print("==================================================================================================================")

spark.stop()
