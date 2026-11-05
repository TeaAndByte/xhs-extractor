FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    XHS_DATA_DIR=/app/user_data \
    XHS_ENABLE_BROWSER_LOGIN=false

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/user_data && chmod 700 /app/user_data

EXPOSE 5000
VOLUME ["/app/user_data"]

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 90 --access-logfile - --error-logfile - app:app"]
