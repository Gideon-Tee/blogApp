# Stage 1: Build dependencies
FROM python:3.10-slim AS builder

WORKDIR /app

# Install system dependencies only for build
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime image
FROM python:3.10-slim

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /root/.local /root/.local
COPY . .

# Ensure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Install runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# Entrypoint script
RUN echo '#!/bin/sh\n\
flask db init || true\n\
flask db migrate || true\n\
flask db upgrade || true\n\
gunicorn --bind 0.0.0.0:5000 app:app' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]