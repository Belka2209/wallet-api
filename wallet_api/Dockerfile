FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Create alembic.ini if it doesn't exist
RUN if [ ! -f alembic.ini ]; then \
    echo "[alembic]" > alembic.ini && \
    echo "script_location = migrations" >> alembic.ini && \
    echo "prepend_sys_path = ." >> alembic.ini; \
    fi

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]