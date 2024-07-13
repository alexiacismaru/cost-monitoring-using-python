import numpy as np
from sklearn.ensemble import IsolationForest
import pandas as pd
from statsmodels.tsa.stattools import adfuller, pacf, acf
from statsmodels.tsa.arima.model import ARIMA

####### ANOMALY DETECTION USING ISOLATION FOREST #######
def anomaly_detection(dataset, column, initial_outlier, target_accuracy, max_iterations):
    # Initialize
    random_state = np.random.RandomState(42)
    model_aws = IsolationForest(n_estimators=100, max_samples='auto', contamination=0.2, random_state=random_state)
    model_aws.fit(dataset[[column]])

    dataset['scores'] = model_aws.decision_function(dataset[[column]])
    dataset['anomaly'] = model_aws.predict(dataset[[column]])
    
    def evaluate_accuracy(outlier_value):
        # Determine which points are considered outliers
        predicted_outliers = dataset[dataset['scores'] < outlier_value]
        if len(predicted_outliers) == 0:
            return 0
        true_outliers = dataset[dataset['anomaly'] == -1]
        accuracy_percentage = 100 * len(predicted_outliers) / len(true_outliers)
        return accuracy_percentage
    
    # Initialize variables
    outlier = initial_outlier
    accuracy = evaluate_accuracy(outlier)
    iterations = 0
    
    # Iterate to adjust outlier value
    while accuracy < target_accuracy and iterations < max_iterations:
        outlier -= 0.0001  # Decrease the outlier threshold to capture more anomalies
        accuracy = evaluate_accuracy(outlier)
        iterations += 1
    return outlier, accuracy

###### CREATE A BIG METHOD THAT INCLUDES ALL OF THE STEPS NECESSARY FOR AN ARIMA MODEL TO USE ON ALL SCRIPTS ######
def ARIMA_model(dataset, column, date, servicecode, time_series, servicecode_name):
    # Check for stationarity
    result = adfuller(dataset[column])

    if result[1] > 0.05:
        df_log = np.sqrt(dataset[column])
        df_diff = df_log.diff().dropna()
        result = adfuller(df_diff)
        if result[1] > 0.05:
            df_diff = df_diff.diff().dropna()
            result = adfuller(df_diff)
    else:
        df_diff = dataset[column]
        result = adfuller(df_diff)
    
    df_diff = df_diff.to_frame(name='Cost')

    # Calculate p, d, q
    def adf_test(series):
        result = adfuller(series, autolag='AIC')
        return result[1]
    
    d = 0
    p_value = adf_test(time_series)
    
    while p_value > 0.05 and d < 2:
        d += 1
        time_series = time_series.diff().dropna()
        p_value = adf_test(time_series)
    
    nlags = int((len(dataset) / 2) - 1)
    
    pacf_values = pacf(time_series, nlags=nlags, method='ols')
    p = np.argmax(pacf_values < (1.96 / np.sqrt(len(time_series)))) - 1
    p = max(0, p)
    
    acf_values = acf(time_series, nlags=nlags)
    q = np.argmax(acf_values < (1.96 / np.sqrt(len(time_series)))) - 1
    q = max(0, q)
    
    # ARIMA model
    model = ARIMA(dataset[column], order=(p, d, q))
    model_fit = model.fit()
    dataset['Forecast'] = model_fit.predict()
    forecast = model_fit.forecast(steps=7)
    
    # Get the last date in the original DataFrame
    last_date = dataset[date].max()
    # Create a new DataFrame
    forecast_df = pd.DataFrame({
        'date': pd.date_range(start=last_date + pd.DateOffset(days=1), periods=len(forecast)),
        'product_servicecode': servicecode,
        'forecast': forecast
    })
    forecast_df.to_csv(f'forecasted_{servicecode_name}_costs.csv', index=False)
