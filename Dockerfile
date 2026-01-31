# Multi-stage build for PokerLite

# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/poker-client

# Copy package files
COPY poker-client/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY poker-client/ ./

# Build the frontend for production
RUN npm run build

# Stage 2: Python backend with static files
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY server/ ./

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/poker-client/dist ./static

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
