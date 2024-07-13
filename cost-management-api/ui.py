import streamlit as st
import requests

  
url = 'http://127.0.0.1:5000'
response = requests.get(url)
data = response.json()
st.write(data)



# def get_api_response(url):
#     response = requests.get(url)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         return st.write("Failed to fetch data from the API.")

# st.title("API Response Display in Streamlit")

# data = get_api_response(url)

# if data:
#     st.write("API Response:")
#     st.json(data)
# else:
#     st.write("Failed to fetch data from the API.")