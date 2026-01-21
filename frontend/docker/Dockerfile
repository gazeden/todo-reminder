FROM python:3.12-slim AS base

# Install system dependencies commonly needed for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir --upgrade uv

# =============================
# Stage 2 — Runtime environment
# =============================
FROM python:3.12-slim AS runtime

# Copy uv from base image
COPY --from=base /usr/local /usr/local

WORKDIR /app

COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --no-dev --frozen

# Copy application source code
COPY . .

EXPOSE 8501

# Run with uv
ENTRYPOINT [ "uv", "run" ]
CMD [ "streamlit", "run", "🏠_Home.py" ]
