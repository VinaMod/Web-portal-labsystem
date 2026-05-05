FROM python:3.12.3-slim

WORKDIR /app

# Copy trước requirements để tận dụng cache
COPY requirements.txt .

# Fix apt + cài envsubst
RUN apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && apt-get update --allow-releaseinfo-change \
 && apt-get install -y --no-install-recommends \
    gettext-base \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy phần còn lại
COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "app.py"]