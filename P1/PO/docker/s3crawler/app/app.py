import boto3
import pika
import os
import time 
from prometheus_client import Counter, Histogram, start_http_server
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()] 
)

logger = logging.getLogger(__name__)

# Variables de entorno
BUCKET = os.getenv("BUCKET")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
PREFIX = os.getenv("PREFIX")

RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE')
RABBITMQ = os.getenv('RABBITMQ')

# Crear métricas de Prometheus
OBJECT_COUNT = Counter('s3_crawler_objects_total', 'Cantidad total de objetos procesados')
PROCESSING_TIME = Histogram('s3_crawler_processing_time_seconds', 'Tiempo total de procesamiento')

# Iniciar servidor de métricas en el puerto 9102
start_http_server(9102)
logger.info("Servidor de métricas de Prometheus iniciado en el puerto 9102")

# Crear una sesión de boto3
session = boto3.Session(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)

# Crear un cliente de S3
s3 = session.client('s3')

# Listar objetos con el prefijo específico
response = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
logger.info(f"Objetos obtenidos del bucket {BUCKET} con prefijo {PREFIX}")

# Obtener los csv del bucket
def get_csv():
    csv = []
    for obj in response['Contents']:
        if obj['Key'].endswith('.csv'):
            csv.append(obj['Key'])
            logger.info(f"CSV encontrado: {obj['Key']}")
    return csv

# Publicar los mensajes en la cola de RabbitMQ
def publish_csv_to_rabbitmq(rabbitmq_user, rabbitmq_pass, rabbitmq_host, rabbitmq_queue): 
    csv = get_csv()
    
    # Contar la cantidad de objetos CSV encontrados
    OBJECT_COUNT.inc(len(csv))
    logger.info(f"{len(csv)} archivos CSV encontrados en el bucket {BUCKET}")

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=rabbitmq_queue)
    logger.info(f"Conexión establecida con RabbitMQ en {rabbitmq_host}")

    with PROCESSING_TIME.time():
        for c in csv:
            logger.info(f"Publicando {c} en la cola {rabbitmq_queue}")
            channel.basic_publish(exchange='', routing_key=rabbitmq_queue, body=c)
            time.sleep(1)
    
    connection.close()
    logger.info("Conexión con RabbitMQ cerrada")

# Iniciar el programa
logger.info("Iniciando el proceso de publicación de CSVs en RabbitMQ")
publish_csv_to_rabbitmq(RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ, RABBITMQ_QUEUE)
logger.info("Proceso finalizado")
