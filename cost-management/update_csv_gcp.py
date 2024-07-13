import pandas as pd
import os

prefix = 'Flowfactor - GC innovate NV_Reports'

def update_csv_gcp():
    files_to_merge = [f for f in os.listdir('.') if f.startswith(prefix) and f.endswith('.csv')]
    
    data_frames = []
    for file in files_to_merge:
        df = pd.read_csv(file)
        data_frames.append(df)
 
        combined_df = pd.concat(data_frames, ignore_index=True)
        combined_df.to_csv('cost-and-usage-report-gcp.csv', index=False) 
