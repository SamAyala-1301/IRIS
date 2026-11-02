FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY iris_events_exporter.py .

CMD ["python", "iris_events_exporter.py"]
