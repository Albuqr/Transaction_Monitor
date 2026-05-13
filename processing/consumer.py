print("consumer.py: script started", flush=True)

import os
import sys
import sqlite3
import json
from confluent_kafka import Consumer
import redis
from dotenv import load_dotenv

load_dotenv()

print(f"ENV KAFKA_BOOTSTRAP_SERVERS={os.getenv('KAFKA_BOOTSTRAP_SERVERS')}", flush=True)
print(f"ENV KAFKA_TOPIC={os.getenv('KAFKA_TOPIC')}", flush=True)
print(f"ENV REDIS_HOST={os.getenv('REDIS_HOST')}", flush=True)
print(f"ENV REDIS_PORT={os.getenv('REDIS_PORT')}", flush=True)

_kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
_kafka_topic = os.getenv('KAFKA_TOPIC')

if not _kafka_servers:
    sys.exit("ERROR: KAFKA_BOOTSTRAP_SERVERS environment variable is required")
if not _kafka_topic:
    sys.exit("ERROR: KAFKA_TOPIC environment variable is required")

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_db = int(os.getenv("REDIS_DB", 0))

r = redis.Redis(host=redis_host, port=redis_port, db=redis_db,
                decode_responses=True)

config = {
    'bootstrap.servers': _kafka_servers,
    'group.id': 'transaction_monitor',
    'auto.offset.reset': 'earliest',
}

consumer = Consumer(config)

consumer.subscribe([_kafka_topic])


db_conn = sqlite3.connect("alerts.db")
db_cursor = db_conn.cursor()

db_cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        transaction_id TEXT PRIMARY KEY,
        cost_center TEXT,
        amount REAL,
        mean REAL,
        timestamp REAL,
        deviation REAL,
        reviewed BOOL
    )
""")

db_conn.commit()


try:
    while True:
        message = consumer.poll(timeout=1.0)
        if message is None:
            continue
        elif message.error():
            print(message.error(), flush=True)
            continue
        else:
            decoded_string = message.value().decode('utf-8')
            data = json.loads(decoded_string)

            cost_center = data.get('cost_center')
            amount = data.get('amount')

            baseline_data = r.hgetall(f"baseline:{cost_center}")

            if baseline_data:
                mean = float(baseline_data.get('mean', 0))
                count = int(baseline_data.get('count', 0))
                total_sum = float(baseline_data.get('sum', 0))

                is_anomaly = amount < (mean * 0.8) or amount > (mean * 1.2)

                if is_anomaly:
                    deviation = (amount - mean) / mean

                    transaction_id = data.get('transaction_id')
                    timestamp = data.get('timestamp')
                    reviewed = False

                    db_cursor.execute("""
                                            INSERT INTO alerts (
                                                transaction_id, 
                                                cost_center, 
                                                amount, 
                                                mean, 
                                                timestamp, 
                                                deviation, 
                                                reviewed
                                            )
                                            VALUES (?, ?, ?, ?, ?, ?, ?)
                                        """,
                                      (transaction_id, cost_center, amount, mean, timestamp, deviation, reviewed)) ## personal note, use ??? to prevent sql injection dipshit

                    db_conn.commit()
                    print(f"ANOMALY DETECTED: {cost_center}  Amount: {amount}  Mean: {mean} (Outside 20% range)", flush=True)
                else:

                    new_count = count + 1
                    new_sum = total_sum + amount
                    new_mean = new_sum / new_count

                    r.hset(f"baseline:{cost_center}", mapping={
                        "count": new_count,
                        "sum": new_sum,
                        "mean": new_mean
                    })
                    print(f"Update on {cost_center} new mean is {new_mean:.2f}", flush=True)

            else:

                print(f"NEW COST CENTER: {cost_center} not found. Creating initial baseline.", flush=True)
                r.hset(f"baseline:{cost_center}", mapping={
                    "count": 1,
                    "sum": amount,
                    "mean": amount
                })

            consumer.commit(message=message, asynchronous=False)

finally:
    consumer.close()