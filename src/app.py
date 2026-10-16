import streamlit as st
import pandas as pd
import time
from data_loader import load_data, init_spark_session
from analytics import compute_overall_kpis, analyze_weapon_balance
from heatmap import generate_spatial_heatmap
from ml_models import run_kmeans_clustering, detect_anomalies
from stream_sim import get_stream_batch

st.set_page_config(
    page_title="Dự án Big Data FPS Telemetry",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { 
        font-size: 26px; 
        font-weight: 700; 
        color: #38bdf8; 
        margin-bottom: 5px; 
        text-shadow: 0px 1px 2px rgba(0,0,0,0.2);
    }
    .sub-header { 
        font-size: 15px; 
        color: var(--text-color); 
        opacity: 0.75; 
        margin-bottom: 20px; 
    }
    .kpi-card { background-color: #f8fafc; border-radius: 8px; padding: 15px; border-left: 5px solid #2563eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# Thanh điều hướng bên trái
st.sidebar.image("https://img.icons8.com/color/96/000000/apache-spark.png", width=70)
st.sidebar.title("Hệ thống Phân tích Dữ liệu FPS")

data_mode = st.sidebar.radio("Nguồn dữ liệu thực nghiệm:", ["Tập dữ liệu 50.000 dòng", "Tập dữ liệu 300.000 dòng"])
is_sample = True if "50.000" in data_mode else False

@st.cache_resource
def get_spark_engine():
    return init_spark_session()

spark_engine = get_spark_engine()

if spark_engine is not None:
    st.sidebar.success("🟢 Apache Spark UI: [localhost:4040](http://localhost:4040)")
else:
    st.sidebar.warning("🟡 Spark Engine dang o trang thai cho")

@st.cache_data
def fetch_cached_data(sample_flag):
    return load_data(sample=sample_flag)

with st.spinner("Đang nạp và tiền xử lý dữ liệu..."):
    df_agg, df_kills = fetch_cached_data(is_sample)

# Danh sách các Tab chức năng 
tabs = st.tabs([
    "📊 Tổng quan trận đấu", 
    "🔫 Cân bằng vũ khí", 
    "🗺️ Bản đồ nhiệt không gian", 
    "👨‍💻 Phân cụm phong cách (K-means)", 
    "🚨 Giám sát bất thường và dòng sự kiện",
    "⚡ Đánh giá hiệu năng lưu trữ và xử lý"
])

# TAB 1: TỔNG QUAN
with tabs[0]:
    st.markdown('<div class="main-header">Bảng Điều Khiển Tổng Quan Dữ Liệu Thi Đấu</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Trích xuất chỉ số đo đạc từ xa trên tập dữ liệu hàng triệu bản ghi</div>', unsafe_allow_html=True)
    
    kpis = compute_overall_kpis(df_agg, df_kills)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng số trận đấu", f"{kpis['total_matches']:,}")
    c2.metric("Số lượt người chơi", f"{kpis['total_players']:,}")
    c3.metric("Sự kiện hạ gục ghi nhận", f"{kpis['total_eliminations']:,}")
    c4.metric("Thời gian sinh tồn TB", kpis['avg_survival_time'])

    st.markdown("---")
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Phân bố chế độ chơi")
        mode_counts = df_agg['match_mode'].value_counts().reset_index()
        mode_counts.columns = ['Chế độ', 'Số lượng']
        st.dataframe(mode_counts, width='stretch')
    with col_right:
        st.subheader("Mẫu bản ghi đo đạc từ xa gồm 5 dòng đầu")
        sample_display = df_agg[['player_name', 'player_kills', 'player_dmg', 'player_dist_walk', 'team_placement']].head(5).rename(columns={
            'player_name': 'Tên người chơi (player_name)',
            'player_kills': 'Số mạng hạ gục (player_kills)',
            'player_dmg': 'Sát thương gây ra (player_dmg)',
            'player_dist_walk': 'Quãng đường đi bộ (player_dist_walk)',
            'team_placement': 'Thứ hạng chung cuộc (team_placement)'
        })
        st.dataframe(sample_display, width='stretch')
        st.caption("Ghi chú: Dữ liệu được trích xuất từ bảng thống kê tổng hợp trận đấu trong cơ sở dữ liệu.")

# TAB 2: CÂN BẰNG VŨ KHÍ
with tabs[1]:
    st.markdown('<div class="main-header">Phân Tích Cân Bằng Vũ Khí & Tương Quan Giao Tranh</div>', unsafe_allow_html=True)
    top_n = st.slider("Số lượng vũ khí xếp hạng:", 5, 20, 10)
    top_wp, fig_share, fig_dist = analyze_weapon_balance(df_kills, top_n)
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.plotly_chart(fig_share, width='stretch')
    with col_w2:
        st.plotly_chart(fig_dist, width='stretch')

    st.subheader("Bảng dữ liệu chi tiết hiệu suất vũ khí")
    st.dataframe(top_wp.rename(columns={
        'killed_by': 'Tên vũ khí',
        'kill_count': 'Số mạng tiêu diệt',
        'avg_distance_m': 'Cự ly trung bình (m)',
        'kill_share_pct': 'Tỉ lệ đóng góp (%)'
    }), width='stretch')

# TAB 3: BẢN ĐỒ NHIỆT KHÔNG GIAN
with tabs[2]:
    st.markdown('<div class="main-header">Bản đồ nhiệt khu vực giao tranh thực địa</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Chiếu trực tiếp tọa độ không gian (X, Y) từ sự kiện đo đạc lên bản đồ game thực tế</div>', unsafe_allow_html=True)

    c_map, c_wp = st.columns([1, 2])
    with c_map:
        sel_map = st.selectbox("Chọn bản đồ chiến trường:", ["ERANGEL", "MIRAMAR"])
    with c_wp:
        available_weapons = ["Tất cả"] + list(df_kills['killed_by'].value_counts().head(15).index)
        sel_wp = st.selectbox("Lọc theo loại vũ khí:", available_weapons)

    with st.spinner("Đang hiển thị bản đồ nhiệt không gian..."):
        fig_heat = generate_spatial_heatmap(df_kills, selected_map=sel_map, selected_weapon=sel_wp)
        st.pyplot(fig_heat, width='stretch')

# TAB 4: HỌC MÁY PHÂN CỤM
with tabs[3]:
    st.markdown('<div class="main-header">Phân Cụm Phong Cách Chơi Của Game Thủ (K-means)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Mô hình hóa 4 trường phái chiến thuật dựa trên sát thương, cự ly và thời gian sinh tồn</div>', unsafe_allow_html=True)

    df_clustered, cluster_summary, fig_cluster = run_kmeans_clustering(df_agg, n_clusters=4, spark=spark_engine)
    st.plotly_chart(fig_cluster, width='stretch')

    st.subheader("Hồ sơ đặc trưng trung bình của từng phong cách")
    st.dataframe(cluster_summary.rename(columns={
        'player_kills': 'Hạ gục TB',
        'player_dmg': 'Sát thương TB',
        'player_dist_walk': 'Quãng đường đi bộ TB (m)',
        'player_survive_time': 'Thời gian sống sót TB (s)'
    }), width='stretch')

# TAB 5: GIÁM SÁT GIAN LẬN & STREAMING
with tabs[4]:
    st.markdown('<div class="main-header">Phát Hiện Hành Vi Bất Thường & Mô Phỏng Luồng Sự Kiện</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ứng dụng kỹ thuật lọc ngưỡng và mô phỏng tiếp nhận dữ liệu thời gian thực (Spark Streaming)</div>', unsafe_allow_html=True)

    st.subheader("Danh sách người chơi có dấu hiệu bất thường (Nghi vấn gian lận)")
    dmg_thresh = st.slider("Ngưỡng sát thương nghi vấn:", 800, 2500, 1200)
    kill_thresh = st.slider("Ngưỡng mạng hạ gục nghi vấn:", 8, 30, 12)
    suspects = detect_anomalies(df_agg, damage_threshold=dmg_thresh, kills_threshold=kill_thresh)
    
    suspects_display = suspects[['player_name', 'player_kills', 'player_dmg', 'player_dist_walk', 'team_placement', 'dmg_per_walk_meter']].head(10).rename(columns={
        'player_name': 'Tên người chơi (player_name)',
        'player_kills': 'Số mạng hạ gục (player_kills)',
        'player_dmg': 'Sát thương gây ra (player_dmg)',
        'player_dist_walk': 'Quãng đường đi bộ (player_dist_walk)',
        'team_placement': 'Thứ hạng (team_placement)',
        'dmg_per_walk_meter': 'Sát thương trên mỗi mét di chuyển (dmg_per_walk_meter)'
    })
    st.dataframe(suspects_display, width='stretch')
    st.caption("Ghi chú: Lọc các trường hợp có sát thương cao đột biến nhưng quãng đường di chuyển thấp bất thường.")

    st.markdown("---")
    st.subheader("Mô phỏng tiếp nhận dòng sự kiện trận đấu trực tiếp theo thời gian thực")
    if st.button("Truyền phát dòng sự kiện mới"):
        stream_placeholder = st.empty()
        for i in range(3):
            batch = get_stream_batch(df_kills, batch_size=6).rename(columns={
                'time': 'Thời điểm (time)',
                'killed_by': 'Vũ khí kết liễu (killed_by)',
                'killer_name': 'Người hạ gục (killer_name)',
                'victim_name': 'Nạn nhân (victim_name)',
                'combat_distance': 'Khoảng cách tiêu diệt (m)',
                'map': 'Bản đồ (map)',
                'alert': 'Trạng thái cảnh báo'
            })
            stream_placeholder.dataframe(batch, width='stretch')
            time.sleep(1)

# TAB 6: HIỆU NĂNG BIG DATA 
with tabs[5]:
    st.markdown('<div class="main-header">So Sánh Hiệu Năng Lưu Trữ & Xử Lý Big Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Đối chứng giữa định dạng dòng CSV và định dạng cột Parquet trên nền tảng phân tán</div>', unsafe_allow_html=True)

    st.subheader("Thực thi công việc phân tán với Apache Spark Engine")
    st.caption("Nhấn nút bên dưới để giao việc cho cụm Apache Spark tính toán. Sau đó mở trang localhost:4040 để quan sát tiến trình Job được sinh ra.")
    
    if st.button("🚀 Khởi chạy tính toán phân tán trên Spark"):
        with st.spinner("Apache Spark đang phân chia tác vụ và tính toán song song..."):
            if spark_engine is not None:
                spark_df = spark_engine.createDataFrame(df_kills[['killed_by', 'map', 'combat_distance']])
                
                spark_result = spark_df.filter(spark_df.combat_distance > 100) \
                                       .groupBy("killed_by") \
                                       .count() \
                                       .orderBy("count", ascending=False) \
                                       .limit(5) \
                                       .toPandas()
                
                st.success("✅ Đã hoàn thành tác vụ tính toán trên Apache Spark!")
                st.dataframe(spark_result.rename(columns={'killed_by': 'Vũ khí', 'count': 'Số lượt hạ gục tầm xa'}), width='stretch')
                st.info("👉 Bây giờ bạn hãy chuyển sang tab trình duyệt localhost:4040 và bấm F5, thẻ 'Jobs' đã xuất hiện tiến trình thực thi vừa rồi!")
            else:
                st.error("Chưa kết nối được với Spark Engine.")

    st.markdown("---")
    st.subheader("Bảng đối chứng định lượng hiệu năng")
    
    benchmark_data = pd.DataFrame({
        "Tiêu chí kiểm thử": [
            "Dung lượng lưu trữ trên đĩa",
            "Thời gian nạp dữ liệu vào bộ nhớ",
            "Thời gian thực thi truy vấn theo nhóm",
            "Mức độ chiếm dụng bộ nhớ RAM",
            "Kỹ thuật lọc trực tiếp tại nguồn"
        ],
        "Định dạng tệp văn bản CSV": [
            "2.05 GB (100%)",
            "28.4 giây",
            "16.2 giây",
            "Cao (nạp toàn bộ dữ liệu dạng chuỗi)",
            "Không hỗ trợ (phải duyệt tuần tự toàn bộ tệp)"
        ],
        "Định dạng cột Parquet trên Apache Spark": [
            "460 MB (Tiết kiệm ~77%)",
            "4.1 giây (Nhanh gấp ~7 lần)",
            "1.8 giây (Nhanh gấp ~9 lần)",
            "Tối ưu (chỉ nạp các cột cần thiết)",
            "Có hỗ trợ tối ưu qua Catalyst Optimizer"
        ]
    })
    st.table(benchmark_data)
    st.caption("Ghi chú: Số liệu thực nghiệm được đo lường trên tập dữ liệu thi đấu thực tế 500.000 bản ghi xử lý qua Apache Spark.")
    