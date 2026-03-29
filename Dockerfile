# Multi-stage build for educational-equity-flow dashboard
# Final image: Python 3.11 slim (40MB base)

FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and project metadata
COPY pyproject.toml README.md ./
COPY src/ src/

# Install Python dependencies to virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --no-deps -e .

# Install production dependencies from pyproject.toml
RUN pip install --no-cache-dir \
    duckdb==1.1.3 \
    polars==1.9.0 \
    pandas==2.2.3 \
    openpyxl==3.1.5 \
    pyarrow==17.0.0 \
    dbt-duckdb==1.8.2 \
    great-expectations==0.18.21 \
    scikit-learn==1.5.2 \
    prophet==1.1.5 \
    streamlit==1.39.0

# ============= Runtime stage =============
FROM python:3.11-slim

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_HEADLESS=true

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p warehouse/artifacts data/bronze && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import streamlit; print('healthy')" || exit 1

# Run Streamlit dashboard
CMD ["streamlit", "run", "app/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--logger.level=info"]
