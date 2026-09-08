FROM python:3.12-slim

# libgomp1 is required by the lightgbm / xgboost native libraries and is NOT
# part of the slim base image - without this line, importing lightgbm fails
# with "libgomp.so.1: cannot open shared object file".
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# exact versions the bundled models were pickled with
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# app code + trained models + SQLite DB + built frontend + panel data
COPY backend /app/backend
COPY data /app/data

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 7860

# Hugging Face Spaces uses app_port (7860); Render/Railway inject $PORT
CMD ["sh", "/app/start.sh"]
