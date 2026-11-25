# ---- Build a small, secure production image ----
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install runtime dependencies first to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY aceest_fitness ./aceest_fitness
COPY wsgi.py ./

# Run as an unprivileged user for security
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Basic container health check hitting the Flask health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:5000/health').status==200 else sys.exit(1)"

# Serve with Gunicorn (production WSGI server)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "wsgi:app"]
