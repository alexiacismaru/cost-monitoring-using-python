from flask import Flask, jsonify
import pandas as pd 
from metrics_amazoncloudwatch import check_amazoncloudwatch
from metrics_amazonec2 import check_amazonec2
from metrics_amazoneks import check_amazoneks
from metrics_amazons3 import check_amazons3
from metrics_amazonvpc import check_amazonvpc
from metrics_awsconfig import check_awsconfig
from metrics_awskms import check_awskms
# from metrics_compute_engine import check_compute_engine
# # from metrics_kubernetes_engine import check_kubernetes_engine
# from metrics_networking import check_networking 

# Import the forecasted values from the cost-management repository
amazon_cloud_watch_forecasts = pd.read_csv('forecasted_amazoncloudwatch_costs.csv')
amazonEC2_forecasts = pd.read_csv('forecasted_amazonEC2_costs.csv')
amazonEKS_forecasts = pd.read_csv('forecasted_amazonEKS_costs.csv')
amazonS3_forecasts = pd.read_csv('forecasted_amazonS3_costs.csv')
amazonVPC_forecasts = pd.read_csv('forecasted_amazonVPC_costs.csv')
awsConfig_forecasts = pd.read_csv('forecasted_awsConfig_costs.csv')
awskms_forecasts = pd.read_csv('forecasted_awskms_costs.csv')
compute_engine_forecasts = pd.read_csv('forecasted_compute_engine_costs.csv')
kubernetes_forecasts = pd.read_csv('forecasted_kubernetes_engine_costs.csv')
networking_forecasts = pd.read_csv('forecasted_networking_costs.csv')
# Import the ouliers calculated from the cost-management repository
outliers = pd.read_csv('outliers.csv') 

# Get the outlier value for each service
amazon_cloud_watch_threshold = outliers['AmazonCloudWatch'].iloc[-1]
amazonEC2_threshold = outliers['AmazonEC2'].iloc[-1]
amazonEKS_threshold = outliers['AmazonEKS'].iloc[-1]
amazonS3_threshold = outliers['AmazonS3'].iloc[-1]
amazonVPC_threshold = outliers['AmazonVPC'].iloc[-1]
awsConfig_threshold = outliers['AwsConfig'].iloc[-1]
awskms_threshold = outliers['AWSKMS'].iloc[-1]
compute_engine_threshold = outliers['ComputeEngine'].iloc[-1]
kubernetes_threshold = outliers['KubernetesEngine'].iloc[-1]
networking_threshold = outliers['Networking'].iloc[-1]

app = Flask(__name__)

@app.route('/', methods=['GET'])
def compare_values():
    '''
    Check if there are any values that exceed the threshold for each service.
    If there are, run the code to check the metrics for that service.
    Depending on the results of the monitoring, the API will display
    the reason why the service is overspending and the solution to the problem
    by using an OpenAI client to answer a prompt regarding how to fix the issue.
    '''
    
    results = {}

    if any(amazon_cloud_watch_forecasts['forecast'] > amazon_cloud_watch_threshold):
        print("Overspending on Amazon CloudWatch") 
        results['AmazonCloudWatch'] = check_amazoncloudwatch()
     
    if any(amazonEC2_forecasts['forecast'] > amazonEC2_threshold):
        print("Overspending on Amazon EC2") 
        results['AmazonEC2'] = check_amazonec2()
 
    if any(amazonEKS_forecasts['forecast'] > amazonEKS_threshold):
        print("Overspending on Amazon EKS") 
        results['AmazonEKS'] = check_amazoneks()
 
    if any(amazonS3_forecasts['forecast'] > amazonS3_threshold):
        print("Overspending on Amazon S3") 
        results['AmazonS3'] = check_amazons3()

    if any(amazonVPC_forecasts['forecast'] > amazonVPC_threshold):
        print("Overspending on Amazon VPC") 
        results['AmazonVPC'] = check_amazonvpc()
    
    if any(awsConfig_forecasts['forecast'] > awsConfig_threshold):  
        print("Overspending on AWS Config") 
        results['AWSConfig'] = check_awsconfig()
        
    if any(awskms_forecasts['forecast'] > awskms_threshold):
        print("Overspending on AWS KMS") 
        results['AWSKMS'] = check_awskms() 
    
    # if any(compute_engine_forecasts['forecast'] > compute_engine_threshold):
    #     print("Overspending on Compute Engine") 
    #     results['ComputeEngine'] = check_compute_engine()
    
    # # if any(kubernetes_forecasts['forecast'] > kubernetes_threshold):
    # #     print("Overspending on Kubernetes Engine") 
    # #     results['KubernetesEngine'] = check_kubernetes_engine()

    # if any(networking_forecasts['forecast'] > networking_threshold):
    #     print("Overspending on Networking") 
    #     results['Networking'] = check_networking()

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)