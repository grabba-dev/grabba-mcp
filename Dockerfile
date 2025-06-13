# Start with a lightweight Python image
FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.1.1 \
    APP_HOME=/app \
    MCP_SERVER_TRANSPORT=streamable-http

# Set working directory
WORKDIR $APP_HOME

# Install Poetry for dependency management
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Copy only the dependency files first for caching
COPY apps/mcp/pyproject.toml apps/mcp/poetry.lock ./

# Install dependencies (only production dependencies)
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the app
COPY apps/mcp/ .

# Expose WebSocket and API ports
EXPOSE 8283

# Run the MCP server
CMD ["poetry", "run", "python", "src/server.py"]
