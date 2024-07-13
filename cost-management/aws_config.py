import pandas as pd    
from methods import *  

def aws_config():
    aws_report = pd.read_csv('clean-cost-and-usage-report-aws.csv', delimiter=',', low_memory=False) 

    ### Split the dataframe into 7 for each service ###
    dfs_by_service_code = {service_code: df for service_code, df in aws_report.groupby('product_servicecode')}

    aws_config = dfs_by_service_code['AWSConfig']
    aws_config.drop(['product_to_location', 'product_to_region_code'], axis=1, inplace=True)

    ### ANOMALY DETECTION USING ISOLATION FOREST ### 
    outlier_threshold, achieved_accuracy = anomaly_detection(aws_config, 'cost', 0.5, 95, 100) 
    with open('outliers.csv', 'a') as f:
        f.write(f'AWSConfig, {outlier_threshold}\n')
        
    ### FORECASTING USING ARIMA ###
    aws_config['date'] = pd.to_datetime(aws_config['date'])
    ARIMA_model(aws_config, 'cost', 'date', 'product_servicecode', aws_config['date'], 'awsConfig')
