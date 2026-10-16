import os
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

def init_spark_session():
    try:
        spark = SparkSession.builder \
            .appName("PUBG_FPS_Telemetry_Analytics") \
            .master("local[*]") \
            .config("spark.ui.port", "4040") \
            .config("spark.ui.bindAddress", "0.0.0.0") \
            .config("spark.driver.bindAddress", "0.0.0.0") \
            .config("spark.driver.host", "localhost") \
            .config("spark.driver.memory", "1g") \
            .config("spark.driver.extraJavaOptions", "-Duser.timezone=Asia/Ho_Chi_Minh") \
            .config("spark.executor.extraJavaOptions", "-Duser.timezone=Asia/Ho_Chi_Minh") \
            .getOrCreate()
        print("[OK] Khoi tao Apache Spark thanh cong! Spark UI dang mo tai cong 4040.")
        return spark
    except Exception as e:
        print(f"[ERROR] Loi khoi dong Spark: {e}")
        return None

def load_data(sample=True):

    if sample:
        agg_file = os.path.join(DATASET_DIR, "agg_match_stats_50k.csv")
        kills_file = os.path.join(DATASET_DIR, "kill_match_stats_50k.csv")
    else:
        agg_file = os.path.join(DATASET_DIR, "agg_match_stats_300k.csv")
        kills_file = os.path.join(DATASET_DIR, "kill_match_stats_300k.csv")

    # Chỉ chọn lọc các cột cần thiết phục vụ tính toán để tối ưu bộ nhớ RAM
    agg_cols = [
        'match_id', 'match_mode', 'player_name', 'player_kills', 
        'player_dmg', 'player_dist_walk', 'player_survive_time', 'team_placement'
    ]
    kills_cols = [
        'match_id', 'killed_by', 'killer_name', 'killer_position_x', 
        'killer_position_y', 'map', 'time', 'victim_name', 
        'victim_position_x', 'victim_position_y'
    ]

    # Đọc dữ liệu có chọn lọc
    df_agg = pd.read_csv(agg_file)
    df_kills = pd.read_csv(kills_file)

    # Loại bỏ khoảng trắng thừa ở tiêu đề cột
    df_agg.columns = df_agg.columns.str.strip()
    df_kills.columns = df_kills.columns.str.strip()

    # Lọc lại đúng các cột nghiệp vụ cần dùng
    valid_agg_cols = [c for c in agg_cols if c in df_agg.columns]
    valid_kills_cols = [c for c in kills_cols if c in df_kills.columns]
    df_agg = df_agg[valid_agg_cols].copy()
    df_kills = df_kills[valid_kills_cols].copy()

    # Xóa sạch khoảng trắng thừa trong giá trị các cột chuỗi
    for col in df_kills.select_dtypes(include='object').columns:
        df_kills[col] = df_kills[col].astype(str).str.strip()
    for col in df_agg.select_dtypes(include='object').columns:
        df_agg[col] = df_agg[col].astype(str).str.strip()

    # Chuẩn hóa kiểu dữ liệu bản đồ
    df_kills['map'] = df_kills['map'].astype(str).str.strip().str.upper()

    # Ép kiểu dữ liệu số an toàn cho các cột tọa độ
    coord_cols = ['killer_position_x', 'killer_position_y', 'victim_position_x', 'victim_position_y']
    for col in coord_cols:
        if col in df_kills.columns:
            df_kills[col] = pd.to_numeric(df_kills[col], errors='coerce')

    # Tính toán khoảng cách tiêu diệt giữa người bắn và nạn nhân
    df_kills['combat_distance'] = np.sqrt(
        (df_kills['killer_position_x'] - df_kills['victim_position_x'])**2 +
        (df_kills['killer_position_y'] - df_kills['victim_position_y'])**2
    ) / 100.0

    # Ép kiểu số an toàn cho các trường định lượng của bảng agg
    num_agg_cols = ['player_kills', 'player_dmg', 'player_dist_walk', 'player_survive_time', 'team_placement']
    for col in num_agg_cols:
        if col in df_agg.columns:
            df_agg[col] = pd.to_numeric(df_agg[col], errors='coerce').fillna(0)

    df_agg['player_name'] = df_agg['player_name'].fillna("Unknown_Player")

    return df_agg, df_kills
