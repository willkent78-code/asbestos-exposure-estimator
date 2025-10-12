# Use a small official Python image
FROM python:3.11-slim

# Environment: no .pyc files, clean output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Work directory inside the container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your whole project into the container
COPY . .

# Hugging Face Spaces automatically sets $PORT
ENV PORT=7860

# Run your Flask app using Gunicorn (production server)
CMD ["bash", "-lc", "gunicorn -w 2 -k uvicorn.workers.UvicornWorker app_flask_backup:app --bind 0.0.0.0:${PORT} --timeout 120"]
