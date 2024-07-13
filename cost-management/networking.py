import pandas as pd    
from methods import * 

def networking():
    gcp_report = pd.read_csv('clean-cost-and-usage-report-gcp.csv', delimiter=',', low_memory=False)

    ### Split the dataframe into 3 for each service ###
    dfs_by_service_description = {service_description: df for service_description, df in gcp_report.groupby('Service description')}
    networking = dfs_by_service_description['Networking']

    ### ANOMALY DETECTION USING ISOLATION FOREST ###
    anomaly_detection(networking, 'Cost', 1.4, 100, 50)
    outlier_threshold, achieved_accuracy = anomaly_detection(networking, 'Cost', 1.4, 95, 100) 
    with open('outliers.csv', 'a') as f:
        f.write(f'Networking, {outlier_threshold}\n')
        
    ### FORECASTING USING ARIMA ###
    networking['Date'] = pd.to_datetime(networking['Date'])
    ARIMA_model(networking, 'Cost', 'Date', 'Service description', networking['Date'], 'networking')
