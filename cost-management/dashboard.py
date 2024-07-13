import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

aws_report = pd.read_csv('clean-cost-and-usage-report-aws.csv') 
gcp_report = pd.read_csv('clean-cost-and-usage-report-gcp.csv') 
forecast_compute_engine = pd.read_csv('forecasted_compute_engine_costs.csv')
forecast_kubernetes_engine = pd.read_csv('forecasted_kubernetes_engine_costs.csv')
forecast_networking = pd.read_csv('forecasted_networking_costs.csv')
forecast_amazon_ec2 = pd.read_csv('forecasted_amazonEC2_costs.csv')
forecast_amazon_eks = pd.read_csv('forecasted_amazonEKS_costs.csv')
forecast_amazon_vpc = pd.read_csv('forecasted_amazonVPC_costs.csv')
forecast_awsconfig = pd.read_csv('forecasted_awsConfig_costs.csv')
forecast_awskms = pd.read_csv('forecasted_awskms_costs.csv')
forecast_amazon_s3 = pd.read_csv('forecasted_amazonS3_costs.csv')
forecast_amazon_cloud_watch = pd.read_csv('forecasted_amazoncloudwatch_costs.csv')

with st.sidebar:
    selected = option_menu(
    menu_title = "",
    options = ["Amazon Web Services","Google Cloud Platform", "AWS Forecasts", "GCP Forecasts"], 
    default_index = 0, 
) 
    
if selected == "Amazon Web Services":
    st.header('AWS Statistics')
    # Create a row layout
    Cost_by_date , Cost_by_region= st.columns(2)

    with st.container():
        Cost_by_date .write("Cost by date ")
        Cost_by_region.write("Cost by region")

    with Cost_by_date :
        cost_by_date = aws_report.groupby(['date', 'line_item_product_code'])['cost'].sum().unstack()
        st.bar_chart(cost_by_date)

    with Cost_by_region:
        chart_data = aws_report.groupby(['line_item_product_code', 'product_location'])['cost'].sum().unstack()
        st.bar_chart(chart_data)
    
if selected == "Google Cloud Platform":
    st.header('GCP Statistics')
    # Create a row layout
    Cost_by_date, Cost_by_region= st.columns(2)
    c3, c4= st.columns(2)

    with st.container():
        Cost_by_date .write("Cost by date ")

    with Cost_by_date :
        cost_by_date = gcp_report.groupby(['Date', 'Service description'])['Cost'].sum().unstack()
        st.bar_chart(cost_by_date)

    
if selected == "AWS Forecasts":
    st.header('AWS Forecasts')  
    
    Forecast_amazon_EKS, Forecast_amazon_s3 = st.columns(2)
    Forecast_amazon_VPC, Forecast_awsconfig = st.columns(2)
    Forecast_awskms, Forecast_Amazon_cloud_watch = st.columns(2) 
    Forecast_AWS, Forecast_Amazon_EC2= st.columns(2) 

    with st.container():
        Forecast_amazon_EKS.write("Forecast Amazon EKS")
        Forecast_amazon_s3.write("Forecast Amazon S3")
    
    with st.container():
        Forecast_amazon_VPC.write("Forecast Amazon VPC")
        Forecast_awsconfig.write("Forecast AWS Config")
    
    with st.container():
        Forecast_awskms.write("Forecast AWS KMS")
        Forecast_Amazon_cloud_watch.write("Forecast Amazon Cloud Watch") 

    with st.container():
        Forecast_Amazon_EC2.write("Forecast Amazon EC2")

    with Forecast_amazon_EKS:
        forecasts_amazon_eks = forecast_amazon_eks.groupby(['date', 'product_servicecode'])['forecast'].sum().unstack()
        st.bar_chart(forecasts_amazon_eks)

    with Forecast_amazon_s3:
        forecasts_amazon_s3 = forecast_amazon_s3.groupby(['date', 'product_servicecode'])['forecast'].sum().unstack()
        st.bar_chart(forecasts_amazon_s3)
    
    with Forecast_awsconfig:
        forecasts_awsconfig = forecast_awsconfig.groupby(['date', 'product_servicecode'])['forecast'].sum().unstack()
        st.bar_chart(forecasts_awsconfig)

    with Forecast_amazon_VPC:
        forecasts_amazon_vpc = forecast_amazon_vpc.groupby(['date', 'product_servicecode'])['forecast'].sum().unstack()
        st.bar_chart(forecasts_amazon_vpc)
    
    with Forecast_awskms:
        forecasts_awskms = forecast_awskms.groupby(['date', 'product_servicecode'])['forecast'].sum().unstack()
        st.bar_chart(forecasts_awskms)
    
    with Forecast_Amazon_cloud_watch:
        forecasts_amazon_cloud_watch = forecast_amazon_cloud_watch.groupby(['date', 'product_servicecode'])['forecast'].sum().unstack()
        st.bar_chart(forecasts_amazon_cloud_watch)
    
    with Forecast_Amazon_EC2:
        forecasts_amazon_ec2 = forecast_amazon_ec2.groupby(['date', 'product_servicecode'])['forecast'].sum().unstack()
        st.bar_chart(forecasts_amazon_ec2)

if selected == "GCP Forecasts":
    st.header('GCP Forecasts') 

    # Create a row layout 
    Forecast_Kubernetes, Forecast_Networking = st.columns(2) 
    Forecast_GCP, Forecast_Compute_Engine = st.columns(2)

    with st.container():
        Forecast_Kubernetes.write("Forecast Kubernetes")
        Forecast_Networking.write("Forecast Networking") 
    
    with st.container(): 
        Forecast_Compute_Engine.write("Forecast Compute Engine")

    with Forecast_Kubernetes:
        forecast_kubernetes_engine = forecast_kubernetes_engine.groupby(['date', 'product_servicecode'])['forecast'].sum().unstack()
        st.bar_chart(forecast_kubernetes_engine)

    with Forecast_Networking:
        forecast_networking = forecast_networking.groupby(['date', 'product_servicecode'])['forecast'].sum().unstack()
        st.bar_chart(forecast_networking)

    with Forecast_Compute_Engine:
        forecast_compute_engine = forecast_compute_engine.groupby(['date', 'product_servicecode'])['forecast'].sum().unstack()
        st.bar_chart(forecast_compute_engine)
