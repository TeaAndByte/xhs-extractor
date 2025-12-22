# Use official Playwright image (includes Python and Browsers)
# This is much more reliable than installing Chrome manually on a slim image
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the Flask port
EXPOSE 5000

# Command to run the application (host=0.0.0.0 is crucial for Docker)
CMD ["python", "app.py"]
