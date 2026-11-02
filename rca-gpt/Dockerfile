FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .
RUN pip install -e .

# Create data directories
RUN mkdir -p data/raw data/training logs models

# Expose Streamlit port
EXPOSE 8501

# Default command: run dashboard
CMD ["streamlit", "run", "dashboard.py", "--server.address", "0.0.0.0"]