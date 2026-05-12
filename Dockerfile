FROM python:3.12.3-slim
# VULN-039: Using unpinned base image tag - Trivy will flag this

WORKDIR /app

COPY requirements.txt .

RUN apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && apt-get update --allow-releaseinfo-change \
 && apt-get install -y --no-install-recommends \
    debian-archive-keyring \
    gettext-base \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "lab_management_app.py"]