from amazon_cloud_watch import amazon_cloud_watch
from amazon_eks import amazon_eks
from amazon_vpc import amazon_vpc
from amazon_s3 import amazon_s3
from amazon_ec2 import amazon_ec2
from aws_config import aws_config
from awskms import awskms
from compute_engine import compute_engine
from kubernetes_engine import kubernetes_engine
from networking import networking
from update_csv_gcp import update_csv_gcp
from update_csv_aws import update_csv_aws
from data_processing import data_processing
import warnings
warnings.filterwarnings("ignore")

def main(): 
    update_csv_gcp()
    update_csv_aws()
    data_processing()
    amazon_cloud_watch()
    amazon_eks()
    amazon_vpc()
    amazon_s3()
    amazon_ec2()
    aws_config()
    awskms()
    compute_engine()
    kubernetes_engine()
    networking()

if __name__ == '__main__':
    main()