FROM python:3.12.3-slim

WORKDIR /app

COPY . .

# cần cho envsubst (render .env)
RUN apt-get update && apt-get install -y gettext-base \
    && pip install --no-cache-dir -r requirements.txt

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "app.py"]