import pika
from minio import Minio
import io
from datetime import datetime, timedelta
import threading

# RabbitMQ connection settings
RABBITMQ_HOST = "20.77.25.140"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "admin"
RABBITMQ_PASS = "password"
QUEUES = ["battery", "humidity", "temperature"]

# MinIO connection settings
MINIO_HOST = "20.77.25.140:9100"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin123"
BUCKET_NAME = "esp32bucket"

# MinIO client setup
minio_client = Minio(
    MINIO_HOST,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

# Ensure the bucket exists
if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)

# Buffer to store messages grouped by queue
buffer = {queue: [] for queue in QUEUES}

# Mutex lock to avoid concurrent access to the buffer
buffer_lock = threading.Lock()

# Interval for writing data to MinIO (in seconds)
WRITE_INTERVAL = 600  # 10 minutes

def write_to_minio():
    """Writes buffered messages to MinIO at regular intervals."""
    while True:
        # Wait for the next interval
        threading.Event().wait(WRITE_INTERVAL)

        # Acquire the lock to safely access the buffer
        with buffer_lock:
            for queue_name, messages in buffer.items():
                if not messages:
                    continue  # Skip if no messages to write

                # Prepare the file name (e.g., "battery_2025-01-29_15:00.txt")
                current_time = datetime.now()
                file_name = f"{queue_name}_{current_time.strftime('%Y-%m-%d_%H-%M')}.txt"

                # Combine all buffered messages into a single text block
                combined_data = "".join(messages)
                data_stream = io.BytesIO(combined_data.encode("utf-8"))

                # Upload the data to MinIO
                minio_client.put_object(
                    BUCKET_NAME,
                    file_name,
                    data=data_stream,
                    length=len(combined_data),
                    content_type="text/plain"
                )
                print(f"Stored {file_name} in MinIO with {len(messages)} messages.")

                # Clear the buffer for this queue
                buffer[queue_name] = []

# Start the background thread for writing to MinIO
threading.Thread(target=write_to_minio, daemon=True).start()

# RabbitMQ connection setup
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials))
channel = connection.channel()

# Declare all queues with `durable=True` to match existing RabbitMQ queue settings
for queue in QUEUES:
    channel.queue_declare(queue=queue, durable=True)

def callback(ch, method, properties, body):
    """Callback function to handle messages from RabbitMQ."""
    # Extract the queue name (e.g., from "sensor/battery" to "battery")
    queue_name = method.routing_key.split("/")[-1]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] {body.decode('utf-8')}\n"

    # Add the message to the buffer
    with buffer_lock:
        if queue_name in buffer:  # Ensure the extracted name matches a buffer key
            buffer[queue_name].append(message)
            print(f"Buffered message from {queue_name}: {message.strip()}")
        else:
            print(f"Warning: Received message for unknown queue '{queue_name}'. Ignoring.")

# Start consuming messages from all queues
for queue in QUEUES:
    channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=True)

print("Waiting for messages...")
channel.start_consuming()

