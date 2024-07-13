import pandas as pd    
from methods import *  

def kubernetes_engine():
    gcp_report = pd.read_csv('clean-cost-and-usage-report-gcp.csv', delimiter=',', low_memory=False)

    ### Split the dataframe into 3 for each service ###
    dfs_by_service_description = {service_description: df for service_description, df in gcp_report.groupby('Service description')}
    kubernetes = dfs_by_service_description['Kubernetes Engine']

    ### ANOMALY DETECTION USING ISOLATION FOREST ### 
    outlier_threshold, achieved_accuracy = anomaly_detection(kubernetes, 'Cost', 5.35, 95, 100) 
    with open('outliers.csv', 'a') as f:
        f.write(f'Kubernetes Engine, {outlier_threshold}\n')
        
    ### FORECASTING USING ARIMA ###
    kubernetes['Date'] = pd.to_datetime(kubernetes['Date'])
    ARIMA_model(kubernetes, 'Cost', 'Date', 'Service description', kubernetes['Date'], 'kubernetes_engine')
