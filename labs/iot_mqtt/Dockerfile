FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y mosquitto mosquitto-clients tzdata && \
    pip install paho-mqtt flask && \
    rm -rf /var/lib/apt/lists/*

COPY mosquitto.conf /etc/mosquitto/mosquitto.conf
COPY entrypoint.sh /entrypoint.sh
COPY src/ /app/

RUN chmod +x /entrypoint.sh

WORKDIR /app
ENTRYPOINT ["/entrypoint.sh"]
