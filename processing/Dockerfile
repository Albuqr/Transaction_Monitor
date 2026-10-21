FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY consumer.py .
# Runs as root for now: the consumer writes alerts.db on a host bind mount.
# Switch to a non-root USER once the ownership of that file is sorted out.
# nosemgrep: dockerfile.security.missing-user.missing-user
CMD ["python3", "-u", "consumer.py"]