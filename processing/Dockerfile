FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY consumer.py .
# The consumer writes alerts.db (a bind mount) and its journal next to it in /app. uid 1000 is the
# usual host user; if the mounted file is owned by someone else, chown it to 1000.
RUN useradd --create-home --uid 1000 app && chown app /app
USER app
CMD ["python3", "-u", "consumer.py"]