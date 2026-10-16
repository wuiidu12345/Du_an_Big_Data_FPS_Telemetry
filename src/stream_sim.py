import time
import pandas as pd

def get_stream_batch(df_kills, batch_size=15):
    batch = df_kills.sample(batch_size)[
        ['time', 'killed_by', 'killer_name', 'victim_name', 'combat_distance', 'map']
    ].copy()
    
    batch['alert'] = batch.apply(
        lambda row: "⚠️ Nghi vấn tầm xa" if row['combat_distance'] > 400 and "Sniper" not in row['killed_by'] and "AWM" not in row['killed_by'] else "Bình thường",
        axis=1
    )
    return batch
