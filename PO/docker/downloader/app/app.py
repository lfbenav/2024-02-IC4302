import os
import pika
import pymysql
import requests
import hashlib
import json
from datetime import datetime
from dotenv import load_dotenv

# Cargar las variables de entorno del archivo .env
load_dotenv()

# Variables de entorno
BUCKET = os.getenv('BUCKET')
ACCESS_KEY = os.getenv('ACCESS_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')

RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE')
RABBITMQ = os.getenv('RABBITMQ')

MARIADB_USER = os.getenv('MARIADB_USER')
MARIADB_PASS = os.getenv('MARIADB_PASS')
MARIADB = os.getenv('MARIADB')
MARIADB_DB = os.getenv('MARIADB_DB')
MARIADB_TABLE = os.getenv('MARIADB_TABLE')

JOB_SIZE = 10

PATH = os.getenv('PATH')
API_BASE = os.getenv('API_BASE', 'https://api.crossref.org/works/')
# Conectar a RabbitMQ
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ, credentials=credentials))
channel = connection.channel()

# Declarar la cola
channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

# Conectar a MariaDB

def get_db_connection():
    return pymysql.connect(user=MARIADB_USER, password=MARIADB_PASS, host=MARIADB, database=MARIADB_DB)

# Procesar mensaje
def process_message(ch, method, properties, body):
    job_id = body.decode()
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Actualizar el estado del job a "in-progress"
        cursor.execute(f"UPDATE {MARIADB_TABLE} SET status='in-progress' WHERE id=%s", (job_id,))
        connection.commit()

        # Obtener la lista de DOIs del job
        cursor.execute(f"SELECT dois FROM {MARIADB_TABLE} WHERE id=%s", (job_id,))
        result = cursor.fetchone()
        if result:
            dois = json.loads(result[0])
            omitted = []
            
            for doi_info in dois:
                doi = doi_info.split(',')[0]  # Extraer el DOI del string completo
                print(doi)
                url = f"{API_BASE}{doi}"
                response = requests.get(url)

                if response.status_code == 200:
                    document = response.json()
                    filename = hashlib.md5(doi.encode()).hexdigest() + ".json"
                    with open(os.path.join(PATH, filename), 'w') as f:
                        json.dump(document, f)
                else:
                    print("El doi: ", doi, " no es valido")
                    omitted.append(doi)

            # Actualizar el estado del job a "done" y establecer fecha_fin
            cursor.execute(f"UPDATE {MARIADB_TABLE} SET status='done', fecha_fin=%s, omitted=%s WHERE id=%s",
                            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), json.dumps(omitted), job_id))
            connection.commit()

    except Exception as e:
        print(f"Error procesando el job {job_id}: {e}")
    finally:
        cursor.close()
        connection.close()
        ch.basic_ack(delivery_tag=method.delivery_tag)



# Configurar el consumidor
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=process_message)

print('Esperando mensajes. Presiona CTRL+C para salir')
channel.start_consuming()
