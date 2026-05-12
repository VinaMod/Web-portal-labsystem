FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    traceroute \
    iputils-ping \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
RUN pip install flask

# Copy app code
COPY . .

# Compile SUID binary
RUN gcc iot_sys_helper.c -o /usr/bin/iot_sys_helper && \
    chown root:root /usr/bin/iot_sys_helper && \
    chmod 4755 /usr/bin/iot_sys_helper && \
    rm iot_sys_helper.c

# Create low-priv user
RUN useradd -m iot_user
RUN chown -R iot_user:iot_user /app

# Copy entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 5000

# Dùng entrypoint để generate flag runtime
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "app.py"]
