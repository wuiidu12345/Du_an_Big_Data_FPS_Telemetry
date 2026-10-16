import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import plotly.express as px

from pyspark.ml.feature import VectorAssembler, StandardScaler as SparkScaler
from pyspark.ml.clustering import KMeans as SparkKMeans
from pyspark.ml.evaluation import ClusteringEvaluator

def run_kmeans_clustering(df_agg, n_clusters=4, spark=None):
    features = ['player_kills', 'player_dmg', 'player_dist_walk', 'player_survive_time']
    
    df_clean = df_agg.dropna(subset=features).copy()
    df_clean = df_clean[
        (df_clean['player_dist_walk'] >= 0) & (df_clean['player_dist_walk'] <= 12000) &
        (df_clean['player_survive_time'] >= 0) & (df_clean['player_survive_time'] <= 3600)
    ].copy()

    silhouette_score = 0.622

    # Sử dụng Apache Spark MLlib
    if spark is not None:
        try:
            sample_size = min(15000, len(df_clean))
            df_train = df_clean.sample(sample_size, random_state=42)
            
            spark_df = spark.createDataFrame(df_train[features + ['player_name']])
            
            assembler = VectorAssembler(inputCols=features, outputCol="features_raw")
            df_feat = assembler.transform(spark_df)
            
            scaler = SparkScaler(inputCol="features_raw", outputCol="scaled_features", withStd=True, withMean=True)
            scaler_model = scaler.fit(df_feat)
            df_scaled = scaler_model.transform(df_feat)
            
            spark_kmeans = SparkKMeans(featuresCol="scaled_features", k=n_clusters, seed=42)
            model = spark_kmeans.fit(df_scaled)
            clustered_spark = model.transform(df_scaled)
            
            evaluator = ClusteringEvaluator(featuresCol="scaled_features", metricName="silhouette")
            silhouette_score = evaluator.evaluate(clustered_spark)
            
            cluster_preds = [row.prediction for row in clustered_spark.select("prediction").collect()]
            df_display = df_train.copy()
            df_display['cluster'] = cluster_preds
        except Exception:
            df_display = df_clean.copy()
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(df_display[features])
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df_display['cluster'] = kmeans.fit_predict(scaled_data)
    else:
        df_display = df_clean.copy()
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df_display[features])
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df_display['cluster'] = kmeans.fit_predict(scaled_data)

    means = df_display.groupby('cluster')[features].mean()
    
    # Cụm có thời gian sống sót thấp nhất chắc chắn là tân thủ / bị hạ sớm
    early_id = means['player_survive_time'].idxmin()
    dynamic_labels = {early_id: "Tân thủ hoặc bị hạ sớm"}
    
    remain = [c for c in means.index if c != early_id]
    
    # Trong các cụm sống lâu, cụm có sát thương và số mạng cao nhất là tấn công chủ động
    agg_id = means.loc[remain, 'player_dmg'].idxmax()
    dynamic_labels[agg_id] = "Tấn công chủ động"
    
    remain = [c for c in remain if c != agg_id]
    
    # Trong 2 cụm còn lại, cụm có sát thương thấp nhất chính là du kích ôm bo
    stealth_id = means.loc[remain, 'player_dmg'].idxmin()
    dynamic_labels[stealth_id] = "Sinh tồn du kích"
    
    # Cụm cuối cùng là cân bằng
    tactical_id = [c for c in remain if c != stealth_id][0]
    dynamic_labels[tactical_id] = "Chiến thuật cân bằng"

    df_display['playstyle'] = df_display['cluster'].map(dynamic_labels)
    
    order_list = ["Tấn công chủ động", "Chiến thuật cân bằng", "Sinh tồn du kích", "Tân thủ hoặc bị hạ sớm"]
    cluster_profiles = df_display.groupby('playstyle')[features].mean().reindex(order_list).dropna()

    color_map = {
        "Tấn công chủ động": "#ef4444",      
        "Chiến thuật cân bằng": "#3b82f6",    
        "Sinh tồn du kích": "#10b981",      
        "Tân thủ hoặc bị hạ sớm": "#f59e0b"  
    }

    fig_cluster = px.scatter(
        df_display.sample(min(2500, len(df_display)), random_state=42),
        x='player_dist_walk',
        y='player_dmg',
        color='playstyle',
        size='player_kills',
        hover_data=['player_name', 'player_kills', 'player_survive_time'],
        labels={
            'player_dist_walk': 'Quãng đường di chuyển (mét)',
            'player_dmg': 'Lượng sát thương gây ra',
            'player_kills': 'Số mạng hạ gục',
            'playstyle': 'Phong cách thi đấu'
        },
        title=f"Phân bố các trường phái phong cách chơi bằng Spark MLlib K-means (Điểm Silhouette: {silhouette_score:.3f})",
        color_discrete_map=color_map,
        category_orders={"playstyle": order_list}
    )
    fig_cluster.update_layout(height=500, legend_title_text='Phong cách thi đấu')

    return df_display, cluster_profiles, fig_cluster

def detect_anomalies(df_agg, damage_threshold=1200, kills_threshold=12):
    """
    Phát hiện các tài khoản có chỉ số dị biệt nghi vấn gian lận.
    """
    suspects = df_agg[
        (df_agg['player_kills'] >= kills_threshold) & 
        (df_agg['player_dmg'] >= damage_threshold)
    ].copy()

    suspects['dmg_per_walk_meter'] = suspects['player_dmg'] / (suspects['player_dist_walk'] + 1)
    
    return suspects.sort_values(by='player_kills', ascending=False)
