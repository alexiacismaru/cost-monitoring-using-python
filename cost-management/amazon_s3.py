import pandas as pd    
from methods import *  

def amazon_s3():
    aws_report = pd.read_csv('clean-cost-and-usage-report-aws.csv', delimiter=',', low_memory=False) 

    ### Split the dataframe into 7 for each service ###
    dfs_by_service_code = {service_code: df for service_code, df in aws_report.groupby('product_servicecode')}

    amazonS3 = dfs_by_service_code['AmazonS3']
    amazonS3.drop(['product_to_location', 'product_to_region_code'], axis=1, inplace=True)

    ### ANOMALY DETECTION USING ISOLATION FOREST ### 
    outlier_threshold, achieved_accuracy = anomaly_detection(amazonS3, 'cost', 0.00001, 95, 100) 
    with open('outliers.csv', 'a') as f:
        f.write(f'AmazonS3, {outlier_threshold}\n')

    ### FORECASTING USING ARIMA ###
    amazonS3['date'] = pd.to_datetime(amazonS3['date'])
    ARIMA_model(amazonS3, 'cost', 'date', 'product_servicecode', amazonS3['date'], 'amazonS3')
 