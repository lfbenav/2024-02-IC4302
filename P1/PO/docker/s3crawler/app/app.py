import boto3
import pika
import os

BUCKET= os.getenv("BUCKET")
ACCESS_KEY= os.getenv("ACCESS_KEY")
SECRET_KEY= os.getenv("SECRET_KEY")
PREFIX = os.getenv("PREFIX")

RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE')
RABBITMQ = os.getenv('RABBITMQ')    



# Crear una sesión de boto3
session = boto3.Session(
    aws_access_key_id= ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)

# Crear un cliente de S3
s3 = session.client('s3')

# Listar objetos con el prefijo específico
response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)

#obtener los csv del bucket
def get_csv():
    csv = []
    for obj in response['Contents']:
        if obj['Key'].endswith('.csv'):
            csv.append(obj['Key'])
    return csv

#publicar los mensajes en la cola de rabbit
def publish_csv_to_rabbitmq(rabbitmq_user, rabbitmq_pass, rabbitmq_host, rabbitmq_queue): 
    csv = get_csv()
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=rabbitmq_queue)
    for c in csv:
        channel.basic_publish(exchange='', routing_key=rabbitmq_queue, body=c)
    connection.close()

print(get_csv())

# Iniciar con el programa
publish_csv_to_rabbitmq(RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ, RABBITMQ_QUEUE)
