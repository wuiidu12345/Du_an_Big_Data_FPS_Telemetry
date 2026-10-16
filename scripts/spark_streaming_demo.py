import os
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, window, rand

print("==================================================================================================================")
print("[-] KHỞI ĐỘNG MÔ PHỎNG LUỒNG DỮ LIỆU THỜI GIAN THỰC VỚI SPARK STRUCTURED STREAMING")
print("==================================================================================================================")

spark = SparkSession.builder \
    .appName("PUBG_RealTime_Streaming_Analytics") \
    .master("local[*]") \
    .config("spark.driver.memory", "1g") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

rate_stream = spark.readStream.format("rate").option("rowsPerSecond", 5).load()

weapons = ["M416", "AKM", "SCAR-L", "Kar98k", "AWM", "UMP9"]
simulated_events = rate_stream.withColumn("timestamp", current_timestamp()) \
                              .withColumn("weapon_id", (rand() * len(weapons)).cast("int"))

streaming_counts = simulated_events.groupBy(
    window(col("timestamp"), "10 seconds", "5 seconds")
).count()

print("[-] Đang lắng nghe và tính toán dòng sự kiện... Nhấn Ctrl + C để dừng.")
query = streaming_counts.writeStream \
    .outputMode("complete") \
    .format("console") \
    .option("truncate", "false") \
    .start()

try:
    query.awaitTermination(timeout=30)
    query.stop()
    print("[OK] Đã hoàn thành phiên mô phỏng Spark Streaming.")
except KeyboardInterrupt:
    query.stop()
    print("[OK] Đã dừng tiến trình Streaming.")
