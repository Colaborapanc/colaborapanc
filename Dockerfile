# ColaboraPANC — Backend Dockerfile
# Python 3.11 + GDAL + Django
#
# Build:  docker build -t colaborapanc .
# Run:    docker compose up  (see docker-compose.yml)

FROM python:3.11-slim AS base

# System dependencies: GDAL, PostgreSQL client, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    libpq-dev \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

# Install Python dependencies before copying source (layer cache)
COPY requirements_core.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements_core.txt

# Copy source code
COPY . .

# Collect static files (requires SECRET_KEY at build time — provide via ARG or override at runtime)
ARG SECRET_KEY=build-time-placeholder-not-for-production
ARG DEBUG=False
RUN python manage.py collectstatic --noinput || true

# Create non-root user for production safety
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

# Default: gunicorn. Override in docker-compose for dev (runserver)
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
