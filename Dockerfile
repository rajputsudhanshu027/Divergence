FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir '.[api]'

EXPOSE 8000
CMD ["retail-planner", "serve", "--output-dir", "/app/reports/latest", "--host", "0.0.0.0"]
