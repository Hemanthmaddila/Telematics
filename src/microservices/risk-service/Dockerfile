FROM python:3.9-slim
WORKDIR /app
RUN pip install flask
COPY app_simple.py .
EXPOSE 8082
CMD ["python", "app_simple.py"]

