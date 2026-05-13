import sys
import os
import json
import uuid
import time
import random
from datetime import datetime
from confluent_kafka import Producer
from dotenv import load_dotenv

load_dotenv()

from google.cloud import bigquery

bq_client = bigquery.Client()

query = """
        SELECT
            cost_center,
            budget_amount_brl
        FROM `factory-lakehouse.factory_lakehouse.silver_budget`
    """
print(f"Starting BigQuery extraction")
query_job = bq_client.query(query)
results = query_job.result()
row_list = list(results)



broker = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
topic = os.getenv('KAFKA_TOPIC')

conf = {'bootstrap.servers': broker}
p = Producer(**conf)


def delivery_callback(err, msg):
    if err:
        sys.stderr.write('%% Message failed delivery: %s\n' % err)
    else:
        sys.stderr.write('%% Message delivered to %s [%d] @ %d\n' % (msg.topic(), msg.partition(), msg.offset()))


print(f"Starting test producer. Sending to topic: {topic}")

for i in range(5):
    select_row = random.choice(row_list)
    cost_center = select_row['cost_center']
    amount = float(select_row['budget_amount_brl'])

    if random.random() < 0.3:
        amount = amount * 2.5
    try:
        unique_id = str(uuid.uuid4())

        transaction = {
            "transaction_id": unique_id,
            "cost_center": cost_center,
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        }

        payload = json.dumps(transaction)

        p.produce(topic, payload.encode('utf-8'), callback=delivery_callback)

    except BufferError:
        sys.stderr.write('%% Local producer queue is full (%d messages awaiting delivery)\n' % len(p))

    p.poll(0)
    time.sleep(0.5)

sys.stderr.write('%% Waiting for %d deliveries\n' % len(p))
p.flush()