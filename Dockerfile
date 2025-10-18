# BDO Data Extraction Pipeline - Docker Image
# Multi-stage build for optimized image size

FROM python:3.13-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements_minimal.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements_minimal.txt

# Final stage
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application files
COPY *.py .
COPY meta_prompt.txt .

# Create directories for data
RUN mkdir -p /app/data /app/output /app/logs

# Update PATH to include user packages
ENV PATH=/root/.local/bin:$PATH

# Set Python to run in unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "data_extraction.py"]
