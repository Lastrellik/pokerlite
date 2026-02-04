# Dockerfile for Game Service

FROM python:3.11-slim

WORKDIR /app

# Copy shared module first (from parent context)
COPY services/shared /app/shared

# Install shared module
RUN pip install --no-cache-dir -e /app/shared

# Copy game service requirements
COPY services/game/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy game service code
COPY services/game/app ./app

# Expose port
EXPOSE 8001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8001

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
