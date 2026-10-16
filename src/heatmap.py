import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

def generate_spatial_heatmap(df_kills, selected_map="ERANGEL", selected_weapon="Tất cả", max_points=8000):
    """
    Vẽ lớp phủ mật độ giao tranh lên hình ảnh bản đồ game thực tế.
    Kích thước chuẩn Unreal Engine của PUBG: 800,000 x 800,000 units.
    """
    map_filename = "erangel.jpg" if selected_map == "ERANGEL" else "miramar.jpg"
    img_path = os.path.join(DATASET_DIR, map_filename)

    # Lọc dữ liệu theo bản đồ
    df_filtered = df_kills[df_kills['map'] == selected_map].copy()
    if selected_weapon != "Tất cả":
        df_filtered = df_filtered[df_filtered['killed_by'] == selected_weapon]

    # Lọc các tọa độ hợp lệ
    df_filtered = df_filtered.dropna(subset=['victim_position_x', 'victim_position_y'])
    df_filtered = df_filtered[
        (df_filtered['victim_position_x'] >= 0) & (df_filtered['victim_position_x'] <= 800000) &
        (df_filtered['victim_position_y'] >= 0) & (df_filtered['victim_position_y'] <= 800000)
    ]

    # Lấy mẫu tối ưu hiệu năng hiển thị
    if len(df_filtered) > max_points:
        df_filtered = df_filtered.sample(max_points, random_state=42)

    # Khởi tạo khung vẽ Matplotlib
    fig, ax = plt.subplots(figsize=(9, 9), dpi=130)

    # Nạp ảnh vệ tinh bản đồ
    if os.path.exists(img_path):
        bg_img = Image.open(img_path)
        ax.imshow(bg_img, extent=[0, 800000, 800000, 0])
    else:
        ax.set_facecolor("#1e293b")
        ax.set_xlim(0, 800000)
        ax.set_ylim(800000, 0)

    # Vẽ lớp điểm nhiệt mật độ giao tranh
    ax.scatter(
        df_filtered['victim_position_x'], 
        df_filtered['victim_position_y'], 
        c='red', 
        s=4, 
        alpha=0.35, 
        edgecolors='none',
        label='Vị trí nạn nhân bị hạ gục'
    )

    ax.set_title(f"Bản đồ nhiệt khu vực giao tranh nóng ({selected_map}) - {len(df_filtered):,} điểm sự kiện", fontsize=12, pad=12)
    ax.set_xlabel("Tọa độ không gian X (West - East)", fontsize=9)
    ax.set_ylabel("Tọa độ không gian Y (North - South)", fontsize=9)
    ax.grid(False)
    plt.tight_layout()

    return fig
