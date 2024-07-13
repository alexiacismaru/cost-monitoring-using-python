import pandas as pd    
from methods import *  

def amazon_ec2():
    aws_report = pd.read_csv('clean-cost-and-usage-report-aws.csv', delimiter=',', low_memory=False) 

    ### Split the dataframe into 7 for each service ###
    dfs_by_service_code = {service_code: df for service_code, df in aws_report.groupby('product_servicecode')}

    amazonEC2 = dfs_by_service_code['AmazonEC2']
    amazonEC2.drop(['product_to_location', 'product_to_region_code'], axis=1, inplace=True)

    ### ANOMALY DETECTION USING ISOLATION FOREST ### 
    outlier_threshold, achieved_accuracy = anomaly_detection(amazonEC2, 'cost', 0.3, 95, 100) 
    with open('outliers.csv', 'a') as f:
            f.write(f'AmazonEC2, {outlier_threshold}\n')
    ### FORECASTING USING ARIMA ###
    amazonEC2['date'] = pd.to_datetime(amazonEC2['date'])
    ARIMA_model(amazonEC2, 'cost', 'date', 'product_servicecode', amazonEC2['date'], 'amazonEC2')