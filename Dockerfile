# Use a lightweight Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Git for cloning, and others if needed)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script and .env
COPY main.py .
COPY .env .  # Ensure .env is in the build context (or handle secrets securely)

# Default command
CMD ["python", "main.py"]