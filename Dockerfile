FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
# Alternative if using poetry
# COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Alternative for poetry
# RUN pip install poetry && \
#     poetry config virtualenvs.create false && \
#     poetry install --no-dev

# Copy application code
COPY . .

# Expose port for Streamlit
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the Streamlit application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"] 