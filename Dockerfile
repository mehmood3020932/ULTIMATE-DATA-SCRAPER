# Multi-Stage Dockerfile for ULTIMATE-DATA-SCRAPER

# Stage 1: Build the application
FROM python:3.9-slim AS builder

WORKDIR /app

# Copy requirements.txt first to leverage caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Stage 2: Run the application
FROM python:3.9-slim

WORKDIR /app

# Copy the installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /app .

# Command to run the application
CMD ["python", "your_main_script.py"]
