import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def compute_overall_kpis(df_agg, df_kills):
    """Tính toán các chỉ số KPI tổng thể trận đấu"""
    return {
        "total_matches": df_agg['match_id'].nunique(),
        "total_players": len(df_agg),
        "total_eliminations": len(df_kills),
        "avg_survival_time": f"{df_agg['player_survive_time'].mean() / 60:.1f} phút",
        "avg_kills_per_player": f"{df_agg['player_kills'].mean():.2f}",
        "avg_damage_dealt": f"{df_agg['player_dmg'].mean():.1f}"
    }

def analyze_weapon_balance(df_kills, top_n=10):
    """Phân tích mức độ cân bằng và hiệu quả của các vũ khí"""
    
    # Lọc bỏ các trạng thái không phải vũ khí chính quy
    excluded = ['Down and Out', 'Bluezone', 'Redzone', 'Drown', 'Falling', 'Punch']
    df_wp = df_kills[~df_kills['killed_by'].isin(excluded)].copy()

    stats = df_wp.groupby('killed_by').agg(
        kill_count=('killed_by', 'count'),
        avg_distance_m=('combat_distance', 'mean')
    ).reset_index()

    stats['kill_share_pct'] = (stats['kill_count'] / stats['kill_count'].sum()) * 100
    top_weapons = stats.sort_values(by='kill_count', ascending=False).head(top_n)

    # Biểu đồ tỉ lệ sử dụng vũ khí
    fig_share = px.bar(
        top_weapons, 
        x='killed_by', 
        y='kill_count', 
        text='kill_count',
        color='kill_count',
        color_continuous_scale='Reds',
        labels={'killed_by': 'Tên vũ khí', 'kill_count': 'Số lần kết liễu'},
        title="Top 10 Vũ khí có tần suất kết liễu cao nhất"
    )
    fig_share.update_layout(xaxis_tickangle=-45, height=450)

    # Biểu đồ cự ly giao tranh trung bình
    fig_dist = px.scatter(
        top_weapons,
        x='avg_distance_m',
        y='killed_by',
        size='kill_count',
        color='avg_distance_m',
        color_continuous_scale='Viridis',
        labels={'avg_distance_m': 'Cự ly trung bình (mét)', 'killed_by': 'Vũ khí'},
        title="Cự ly giao tranh hiệu quả của từng loại vũ khí"
    )
    fig_dist.update_layout(height=450)

    return top_weapons, fig_share, fig_dist
