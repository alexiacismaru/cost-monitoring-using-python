FROM python:3.11
WORKDIR /cost-management
COPY . /cost-management
RUN cd /cost-management && pip install -r requirements.txt 
CMD ["streamlit", "run", "dashboard.py"] 