import pika
import json
import time
import sys
import redis
import datetime

redis_client = redis.Redis(host="redis", port=6379, password="redis123", decode_responses=True)

def callback(ch, method, properties, body):
    data = json.loads(body)
    
    log_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": data
    }
    
    redis_client.lpush("system_logs", json.dumps(log_entry))
    redis_client.ltrim("system_logs", 0, 49)
    
    print(f" [x] PROCESSED: {data}", flush=True)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    time.sleep(15) 
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='notifications', durable=True)
    
    print(' [*] Notification service waiting for messages...', flush=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='notifications', on_message_callback=callback)
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)