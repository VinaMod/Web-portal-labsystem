FROM python:3.12.3-slim

WORKDIR /app

COPY . .

# cần cho envsubst (render .env)
RUN apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && apt-get update --allow-releaseinfo-change \
 && apt-get install -y debian-archive-keyring \
 && pip install --no-cache-dir -r requirements.txt

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "app.py"]