import pandas as pd    
from methods import * 

def amazon_vpc():
    aws_report = pd.read_csv('clean-cost-and-usage-report-aws.csv', delimiter=',', low_memory=False) 

    ### Split the dataframe into 7 for each service ###
    dfs_by_service_code = {service_code: df for service_code, df in aws_report.groupby('product_servicecode')}

    amazonVPC = dfs_by_service_code['AmazonVPC']
    amazonVPC.drop(['product_to_location', 'product_to_region_code'], axis=1, inplace=True)

    ### ANOMALY DETECTION USING ISOLATION FOREST ### 
    outlier_threshold, achieved_accuracy = anomaly_detection(amazonVPC, 'cost', 0.1, 95, 100) 
    with open('outliers.csv', 'a') as f:
        f.write(f'AmazonVPC, {outlier_threshold}\n')

    ### FORECASTING USING ARIMA ###
    amazonVPC['date'] = pd.to_datetime(amazonVPC['date'])
    ARIMA_model(amazonVPC, 'cost', 'date', 'product_servicecode', amazonVPC['date'], 'amazonVPC')
 