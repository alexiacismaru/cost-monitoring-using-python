import pandas as pd    
from methods import *  

def compute_engine():
    gcp_report = pd.read_csv('clean-cost-and-usage-report-gcp.csv', delimiter=',', low_memory=False)

    ### Split the dataframe into 3 for each service ###
    dfs_by_service_description = {service_description: df for service_description, df in gcp_report.groupby('Service description')}
    compute_engine = dfs_by_service_description['Compute Engine']

    ### ANOMALY DETECTION USING ISOLATION FOREST ### 
    outlier_threshold, achieved_accuracy = anomaly_detection(compute_engine, 'Cost', 14, 95, 100) 
    with open('outliers.csv', 'a') as f:
        f.write(f'Compute Engine, {outlier_threshold}\n')
        
    ### FORECASTING USING ARIMA ###
    compute_engine['Date'] = pd.to_datetime(compute_engine['Date'])
    ARIMA_model(compute_engine, 'Cost', 'Date', 'Service description', compute_engine['Date'], 'compute_engine')
 