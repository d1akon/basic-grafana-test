import time
import threading
import random
import json
from uuid import uuid4
from datetime import datetime
from confluent_kafka import Producer, Consumer, KafkaException, KafkaError
from prometheus_client import start_http_server, Counter, Histogram

#----- Prometheus metrics
MESSAGES_SENT = Counter('kafka_messages_sent', 'Number of messages produced to Kafka')
MESSAGES_CONSUMED = Counter('kafka_messages_consumed', 'Number of messages consumed from Kafka')

SUCCESSFUL_TRANSACTIONS = Counter('successful_transactions', 'Number of successful transactions')
FAILED_TRANSACTIONS = Counter('failed_transactions', 'Number of failed transactions')

TRANSACTION_LATENCY = Histogram(
    'transaction_latency_seconds',
    'Simulated latency for transaction processing (seconds)',
    buckets=[0.05, 0.1, 0.3, 0.5, 1, 2, 5]
)

KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
TOPIC_NAME = 'test-topic'

def delivery_report(err, msg):
    """Callback for delivery report."""
    if err is not None:
        print(f"Delivery failed for {msg.key()}: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] offset {msg.offset()}")
        MESSAGES_SENT.inc()

def produce_messages():
    producer = Producer({'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS})
    while True:
        try:
            status = "failed" if random.random() < 0.1 else "success"  #--- 10% fail rate
            transaction = {
                "transaction_id": f"txn_{uuid4().hex[:8]}",
                "user_id": f"user_{random.randint(1, 1000)}",
                "amount": round(random.uniform(10.0, 500.0), 2),
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            message = json.dumps(transaction)
            producer.produce(TOPIC_NAME, message, callback=delivery_report)
            producer.poll(0)
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("Stopping producer...")
            break

def consume_messages():
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'python-consumer-group',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe([TOPIC_NAME])

    while True:
        try:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"End of partition {msg.topic()} [{msg.partition()}]")
                else:
                    raise KafkaException(msg.error())
            else:
                transaction = json.loads(msg.value().decode('utf-8'))
                print(f"Consumed transaction: {transaction}")

                #----- Simulating some latency
                with TRANSACTION_LATENCY.time():
                    time.sleep(random.uniform(0.05, 1.5))  

                if transaction['status'] == 'success':
                    SUCCESSFUL_TRANSACTIONS.inc()
                else:
                    FAILED_TRANSACTIONS.inc()

                MESSAGES_CONSUMED.inc()

        except KeyboardInterrupt:
            print("Stopping consumer...")
            break

    consumer.close()

if __name__ == '__main__':
    start_http_server(8000)
    producer_thread = threading.Thread(target=produce_messages, daemon=True)
    consumer_thread = threading.Thread(target=consume_messages, daemon=True)

    producer_thread.start()
    consumer_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
