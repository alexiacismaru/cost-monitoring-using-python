import pandas as pd    
from methods import *  

def amazon_eks():
    aws_report = pd.read_csv('clean-cost-and-usage-report-aws.csv', delimiter=',', low_memory=False) 

    ### Split the dataframe into 7 for each service ###
    dfs_by_service_code = {service_code: df for service_code, df in aws_report.groupby('product_servicecode')}

    amazonEKS = dfs_by_service_code['AmazonEKS']
    amazonEKS.drop(['product_to_location', 'product_to_region_code'], axis=1, inplace=True)

    ### ANOMALY DETECTION USING ISOLATION FOREST ### 
    outlier_threshold, achieved_accuracy = anomaly_detection(amazonEKS, 'cost', 1.5, 95, 100) 
    with open('outliers.csv', 'a') as f:
        f.write(f'AmazpnEKS, {outlier_threshold}\n')

    ### FORECASTING USING ARIMA ##
    amazonEKS['date'] = pd.to_datetime(amazonEKS['date'])
    ARIMA_model(amazonEKS, 'cost', 'date', 'product_servicecode', amazonEKS['date'], 'amazonEKS')
