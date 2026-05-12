import sys
import os
import json
import uuid
import time  # Added this because you use time.sleep()
from datetime import datetime
from confluent_kafka import Producer
from dotenv import load_dotenv

# 1. Load variables (No leading spaces here)
load_dotenv()

# 2. Access environment variables
broker = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
topic = os.getenv('KAFKA_TOPIC')

# 3. Producer setup
conf = {'bootstrap.servers': broker}
p = Producer(**conf)


def delivery_callback(err, msg):
    if err:
        sys.stderr.write('%% Message failed delivery: %s\n' % err)
    else:
        sys.stderr.write('%% Message delivered to %s [%d] @ %d\n' % (msg.topic(), msg.partition(), msg.offset()))


print(f"Starting test producer. Sending to topic: {topic}")

# 4. The Loop
for i in range(5):
    try:
        # Generate a NEW ID for every single message
        unique_id = str(uuid.uuid4())

        transaction = {
            "transaction_id": unique_id,
            "cost_center": "Producao",
            "amount": 205510,
            "timestamp": datetime.now().isoformat()
        }

        payload = json.dumps(transaction)

        # Produce the message
        p.produce(topic, payload.encode('utf-8'), callback=delivery_callback)

    except BufferError:
        sys.stderr.write('%% Local producer queue is full (%d messages awaiting delivery)\n' % len(p))

    # Trigger callbacks and wait briefly
    p.poll(0)
    time.sleep(0.5)

# 5. Final Cleanup
sys.stderr.write('%% Waiting for %d deliveries\n' % len(p))
p.flush()