import pika
import json
import time

def send_notification(payment_data):
    # Simulate sending email/SMS
    print(f"📧 Sending notification for payment {payment_data['payment_id']}")
    print(f"   User: {payment_data['user_id']}")
    print(f"   Amount: ${payment_data['amount']}")
    time.sleep(1)  # Simulate sending time
    print(f"✅ Notification sent!")

def callback(ch, method, properties, body):
    try:
        payment_data = json.loads(body)
        print(f"Received payment event: {payment_data}")
        
        send_notification(payment_data)
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing message: {e}")
        # Reject and requeue
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def main():
    print("🚀 Starting notification worker...")
    
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host='rabbitmq',
                    credentials=pika.PlainCredentials('admin', 'admin'),
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue='payment_events', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='payment_events', on_message_callback=callback)
            
            print("✅ Worker ready. Waiting for messages...")
            channel.start_consuming()
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()