import os
import re
import gzip 
import pandas as pd
import os

directory = 'budget/daily_costs/data/' 
directory_prefix = 'BILLING_PERIOD='   
folder_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}\.\d{3}Z-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
prefix = 'daily_costs-00001' 

def update_csv_aws():
    def find_matching_files(directory, directory_prefix, pattern): 
        matching_directories = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path) and item.startswith(directory_prefix):
                for sub_item in os.listdir(item_path):
                    sub_item_path = os.path.join(item_path, sub_item)
                    if os.path.isdir(sub_item_path) and pattern.match(sub_item):
                        matching_directories.append(sub_item_path)
        return matching_directories

    matching_directories = find_matching_files(directory, directory_prefix, folder_pattern)
        
    data_frames = []
    for dir_path in matching_directories:
        for file in os.listdir(dir_path):
            if file.startswith(prefix) and file.endswith('.gz'):
                file_path = os.path.join(dir_path, file)
                with gzip.open(file_path, 'rt') as f:
                    df = pd.read_csv(f)
                data_frames.append(df)

    combined_df = pd.concat(data_frames, ignore_index=True)
    combined_df.to_csv('cost-and-usage-report-aws.csv', index=False)