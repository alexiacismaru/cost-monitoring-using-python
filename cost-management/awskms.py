import pandas as pd    
from methods import *  

def awskms():
    aws_report = pd.read_csv('clean-cost-and-usage-report-aws.csv', delimiter=',', low_memory=False) 

    ### Split the dataframe into 7 for each service ###
    dfs_by_service_code = {service_code: df for service_code, df in aws_report.groupby('product_servicecode')}

    awskms = dfs_by_service_code['awskms']
    awskms.drop(['product_to_location', 'product_to_region_code'], axis=1, inplace=True)

    ### ANOMALY DETECTION USING ISOLATION FOREST ### 
    outlier_threshold, achieved_accuracy = anomaly_detection(awskms, 'cost', 0.05, 95, 100) 
    with open('outliers.csv', 'a') as f:
        f.write(f'awskms, {outlier_threshold}\n')

    ### FORECASTING USING ARIMA ###
    awskms['date'] = pd.to_datetime(awskms['date'])
    ARIMA_model(awskms, 'cost', 'date', 'product_servicecode', awskms['date'], 'awskms')
 