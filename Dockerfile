FROM python:3.12-slim
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
EXPOSE 8501
COPY . /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["streamlit", "run", "streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
