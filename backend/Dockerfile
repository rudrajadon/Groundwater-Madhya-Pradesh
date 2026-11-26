FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for Pillow and reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install CPU-only PyTorch first (much smaller than CUDA version)
RUN pip install --no-cache-dir --timeout=1000 \
    torch>=2.2.0 --index-url https://download.pytorch.org/whl/cpu

# Then install remaining dependencies
RUN pip install --no-cache-dir --timeout=1000 -r requirements.txt

COPY backend/app ./app
COPY ml ./ml
ENV PYTHONPATH=/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
