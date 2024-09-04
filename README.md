# Cost Management using Python and GPT

## About this project

This is part of a bigger project that researches the best way of organizing a multi-cloud environment. This part focuses on cost management and data-driven solutions using artificial intelligence.

## Features

- Time series analysis: predicts future cost values, based on the previous reports from the cloud providers.
- Anomaly detection: sets cost limits based on past spending.
- Monitoring: monitors all service activity from the cloud providers to see what may cause overspending.
- Natural Language Understanding: using NLP the project lets the user know about what causes overspending and provides detailed solutions.

## Full overview of the process

We started by collecting the existing data to determine trends and patterns and choosing an appropriate forecasting model. By analyzing and visualizing the cost reports we obtained a clear view of how the cloud budget evolves to inform the user of possible problems within the cloud provider services.

Continuously monitored cloud usage and expenses to help detect any possible irregularities using anomaly detection algorithms. Based on the patterns, AI can provide data-driven recommendations for cost optimization, such as identifying underutilized resources and providing instructions on how to fix them.

### 01 Collecting data
For this project, it is essential to have a constant stream of new data getting to the project.

For Amazon Web Services, the AWS Cost and Usage Report has to be enabled to access the cost reports. These reports can be customized, from what columns we want to include in the file to the timeframe we want. The reports are scheduled daily and stored in an Amazon S3.

For GCP the data is collected using BigQuery from the Billing Exports section of Billing. The user needs the Billing Account Administrator and BigQuery User roles to start. After enabling the Cloud Billing export to BigQuery, Google automatically adds a service account as an owner to the dataset you specify.

The data is selected from the cost reports with a query using the BigQuery studio. This query is part of a Python script that sends the information to a GCP storage bucket. The script is created in Cloud Function, along with the requirements.txt file.
```
from google.cloud import bigquery
from google.cloud import storage
import os
def export_billing_data(request):
 project = "project-name" 
 dataset_id = "dataset_id"
 table_id = "table_id" 
 bucket_name = "bucket_name" 
 destination_uri =
f"gs://{bucket_name}/destination_name.csv"
 dataset_ref = bigquery.DatasetReference(project,
dataset_id)
 table_ref = dataset_ref.table(table_id)
 extract_job = client.extract_table(
 table_ref,
 destination_uri,
 # Location must match that of the source table.
 location="EU",
 ) # API request
 extract_job.result() # Waits for job to complete.
 return f"Exported {project}:{dataset_id}.{table_id} to
{destination_uri}"
```

### 02 Storing the data
After the reports are stored in the buckets from each cloud provider, we create a CI/CD pipeline that takes these reports and keeps them into a pipeline artifact. The artifact is pushed to the main branch to keep adding and updating the data and forecasts.
```
deploy_aws:
 tags:
 - ff-acs-gitlab-runner
 stage: deploy
 image:
 name: amazon/aws-cli
 entrypoint: [""]
 only:
 - main
 script:
 - aws configure set aws_access_key_id
$AWS_ACCESS_KEY_ID
 - aws configure set aws_secret_access_key
$AWS_SECRET_ACCESS_KEY
 - aws s3 sync s3://bucket-name
./resources
 artifacts:
 paths:
 - resources/
deploy_gcp:
 stage: deploy
 image:
 name: google/cloud-sdk
 entrypoint: [""]
 only:
 - main
 script:
 - echo $GCP_SERVICE_KEY > /tmp/gcp-key.json
 - gcloud auth activate-service-account --key-file
/tmp/gcp-key.json
 - mkdir -p ./resources
 - gsutil rsync -r gs://billing-ff2024/
./resources
 - rm /tmp/gcp-key.json
 artifacts:
 paths:
 - resources/
push_reports:
 stage: commit
 tags:
 - ff-acs-gitlab-runner
 script:
 - git config --global user.email
"email@gmail.com"
 - git config --global user.name "User Name"
 - git clone
https://oauth2:$ACCESS_TOKEN@gitlab.com/rest_of_url.git temp_repo
 - cp -r resources/* temp_repo/
 - cd temp_repo
 - git add .
 - git commit -m "Adding new cost reports"
 - git push origin main
 only:
 - main
 when: on_success
```
These CSV files are used to analyze the evolution of data over time and to gather enough data to get accurate forecasting.

### 03 Anomaly detection
For anomaly detection, we chose a machine learning model called Isolation Forest. It is a model used to detect anomalies in data. It works by randomly splitting the data multiple times, isolating different points (anomalies) quickly, and requiring more splits to isolate normal points.

The model measures how fast each point gets isolated: anomalies get isolated quickly (shorter path), while normal points take longer (longer path). Anomalies are identified based on their short path lengths in the isolation process. The values are split into two categories: anomaly (-1) and normal value (1).

The values are saved in a CSV file and passed over to the API repository to implement the alarms for the user.

### 04 Forecasting
After collecting enough data, it is clear to see the patterns and trends in the evolution of the costs, so a time series model is the best for this data.

We used the ARIMA model also known as an AutoRegressive Integrated Moving Average.

The main feature of this model is that it can work even with non-stationary data by doing a differencing step one or more times to eliminate the non-stationarity

The autoregressive (AR) part of ARIMA indicates that the evolving variable of interest is regressed on its own lagged (i.e., prior) values.

The moving average (MA) part indicates that the regression error is a linear combination of error terms whose values occurred contemporaneously and at various times in the past.

The I (for “integrated”) indicates that the data values have been replaced with the difference between their value and the previous values.

The model is part of the *statsmodels* Python module. It provides classes and functions for the estimations of many different statistical models and for conducting statistical tests or data exploration.

The p, d, and q values are calculated to find the optimal values for the model for each service based on their cost values.

- p: the number of lag observations in the model, also known as the lag order. It represents the number of days you want to look back to predict the data for the next day.

- d: the number of times the raw observations are differenced; also known as the degree of differencing. It is used to see a clearer pattern in your data. You might look at the changes from one day to the next instead of the actual values.

- q: the size of the moving average window, also known as the order of the moving average. It is like taking an average of past errors (differences between actual and predicted values) to smooth out your predictions. If q is 2, you’re using the average of the errors from the last two days to help make today’s prediction more accurate.

The forecasting values are stored in individual CSV files to represent the forecasted values of each service on the dashboard.

### 05 User interface
For the user to access the forecasted values, we made a website using the framework Streamlit to plot and export the forecasting values for the next week.

Streamlit is an open-source Python framework for data scientists and AI/ML engineers to deliver dynamic data apps with only a few lines of code. It enables developers to build attractive user interfaces in no time. Streamlit is the easiest way, especially for people with no front-end knowledge, to put their code into a web application: No front-end (HTML, JS, CSS) experience or knowledge is required.

### 06 Automation
The main idea of this project is to make the user’s work easier by not having to constantly check the cost reports or worry that they’re not using their resources accordingly.

So, we made several CI/CD jobs to automate running the project. First, we used it to create a Docker image into the Container Registry to use it to deploy the forecast website and API on the internet. This docker image downloads the requirements and runs the main Python script.

```
build:
 tags:
 - ff-acs-gitlab-runner
 image:
 name: gcr.io/kaniko-project/executor:v1.14.0-debug
 entrypoint: [""]
 stage: build
 services:
 - docker:dind
 script:
 - /kaniko/executor
 --context "${CI_PROJECT_DIR}"
 --dockerfile "${CI_PROJECT_DIR}/Dockerfile"
 --destination
"${CI_REGISTRY_IMAGE}:${CI_COMMIT_TAG}"
 --destination "${CI_REGISTRY_IMAGE}:latest"
 rules:
 - if: $CI_COMMIT_BRANCH
 exists:
 - Dockerfile
```
### 07 Data-driven recommendations
Before, cost and multi-cloud management were two different projects with nothing in common. So, to fix this issue we created an API that is used on the cluster nodes to alert the user of overspending. The API will search for the possible cause of overspending and instruct the user on how to prevent it. To start, we imported the outlier and forecasted values and compared them. If the values surpass the threshold, an alert will pop up and let the user know what service might cause the overspending. The API is made using Flask.

```
app = Flask(__name__)
@app.route('/', methods=['GET'])
def compare_values():
 problem, answer = None, None
 if any(amazon_cloud_watch_forecasts['forecast'] >
amazon_cloud_watch_threshold):
 print("Overspending on Amazon CloudWatch")
 results = check_amazoncloudwatch()
 problem, answer = "Overspending on Amazon CloudWatch",
results
 return jsonify({"problem": problem, "answer": answer})
if __name__ == '__main__':
 app.run(debug=True)
```
The API knows what is causing the overspending problem by running multiple methods that check the state of the service. The methods are made based on the research done on overspending on each service.

After the code finds what is wrong with the services, it initializes an OpenAI client and sends a prompt that asks how can the user fix the issue. The client’s answer is then displayed on the user interface. We used space and OpenAI gpt-3.5 to generate the answer to the prompt.

```
client = OpenAI()
nlp = spacy.load("en_core_web_sm")
def get_nlp_response(prompt):
  completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[{"role": "user", "content": prompt}]
  )
  return completion.choices[0].message.content
```
After completing the analysis, the answers are transferred to a Stremlit application to make the instructions more readable for the user. Now, the user can go and try to fix the overspending issue.

## Installation

1. Clone the repository
```
git clone https://github.com/alecsiuh/internship.git
cd internship/cost-management # for the Python project
cd internship/cost-management-api # for the user interface
```
2. Create a virtual environment
```
python3 -m venv venv
venv\Scripts activate
```
3. Install the current dependencies
```
pip install -r requirements.txt
```

## Usage

To start the Streamlit interface:
```
streamlit run ./streamlit_app.py
```

## License 
This project was created by Alexia Cismaru.
