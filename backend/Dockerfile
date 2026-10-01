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

# Install dependencies in stages to avoid timeout
# First install the large ML packages
RUN pip install --no-cache-dir --timeout=1000 \
    torch>=2.2 \
    numpy \
    pandas \
    scikit-learn \
    scipy

# Then install the rest
RUN pip install --no-cache-dir --timeout=1000 \
    fastapi>=0.110 \
    uvicorn[standard]>=0.27 \
    sqlalchemy>=2.0 \
    geoalchemy2>=0.14 \
    psycopg2-binary>=2.9 \
    pydantic>=2.6 \
    python-dotenv \
    joblib \
    reportlab>=4.0 \
    pillow>=10.0 \
    matplotlib>=3.7

COPY backend/app ./app
COPY ml ./ml
ENV PYTHONPATH=/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
