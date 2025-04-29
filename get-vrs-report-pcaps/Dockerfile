FROM python:3.12-bookworm

# Install Chromium and ChromiumDriver
RUN apt-get update && \
    apt-get install -y chromium chromium-driver fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "agent.py"]