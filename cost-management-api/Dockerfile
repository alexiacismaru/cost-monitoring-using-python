FROM python:3.11 
WORKDIR /cost-management-api 

COPY . /cost-management-api
RUN cd /cost-management-api && pip install -r requirements.txt 

RUN python main.py
CMD ["streamlit", "run", "ui.py"]    