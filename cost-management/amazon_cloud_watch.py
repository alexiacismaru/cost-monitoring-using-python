import pandas as pd    
from methods import *  

def amazon_cloud_watch(): 
    aws_report = pd.read_csv('clean-cost-and-usage-report-aws.csv', delimiter=',', low_memory=False) 

    ### Split the dataframe into 7 dfs for each service ###
    dfs_by_service_code = {service_code: df for service_code, df in aws_report.groupby('product_servicecode')}

    amazoncloudwatch = dfs_by_service_code['AmazonCloudWatch']
    amazoncloudwatch.drop(['product_to_location', 'product_to_region_code'], axis=1, inplace=True)

    ### ANOMALY DETECTION USING ISOLATION FOREST ###  
    outlier_threshold, achieved_accuracy = anomaly_detection(amazoncloudwatch, 'cost', 0.0005, 95, 100) 
    with open('outliers.csv', 'a') as f:
        f.write(f'AmazonCloudWatch, {outlier_threshold}\n') 
           
    ### FORECASTING USING ARIMA ### 
    amazoncloudwatch['date'] = pd.to_datetime(amazoncloudwatch['date'])  
    ARIMA_model(amazoncloudwatch, 'cost', 'date', 'product_servicecode', amazoncloudwatch['date'], 'amazoncloudwatch')
