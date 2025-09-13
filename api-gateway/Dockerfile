FROM python:3.9-slim
WORKDIR /app
RUN pip install flask requests
COPY gateway_complete.py .
EXPOSE 8080
CMD ["python", "gateway_complete.py"]

