import os
import boto3
import pymysql
import pika
import requests
from elasticsearch.helpers import bulk
import pandas as pd
from io import StringIO
from elasticsearch import Elasticsearch

#CREDENCIALES BUCKET
BUCKET= os.getenv("BUCKET")
ACCESS_KEY= os.getenv("ACCESS_KEY")
SECRET_KEY= os.getenv("SECRET_KEY")
PREFIX = os.getenv("PREFIX")

#HUGGING-FACE-API
HUGGING_FACE_API = os.getenv('HUGGING_FACE_API')
HUGGING_FACE_API_PORT = os.getenv("HUGGING_FACE_PORT")
print(HUGGING_FACE_API)
print(HUGGING_FACE_API_PORT)

#Credenciales RabbitMQ
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS')  
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE')
RABBITMQ = os.getenv('RABBITMQ')
print(RABBITMQ_USER)
print(RABBITMQ_PASS)
print(RABBITMQ_QUEUE)
print(RABBITMQ)

#credenciales MariaDB
MARIADB_USER = os.getenv('MARIADB_USER')
MARIADB_PASS = os.getenv('MARIADB_PASS')
MARIADB = os.getenv('MARIADB')
MARIADB_DB = os.getenv('MARIADB_DB')
MARIADB_TABLE = os.getenv('MARIADB_TABLE')


# Utilizar la contraseña en la conexión a Elasticsearch
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASS") # O el puerto que se mapea
ELASTIC_USER = os.getenv("ELASTIC_USER")
# Crear la URL de conexión a Elasticsearch
ELASTIC_SERVICE = os.getenv("ELASTIC")
ELASTIC_PORT = os.getenv("ELASTIC_PORT")

es_url = f"http://{ELASTIC_SERVICE}:{ELASTIC_PORT}"


# Conexión a Elasticsearch
es = Elasticsearch(es_url, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
print("oayyyy...")
# Definir el cuerpo del índice con el campo 'embeddings' como dense_vector
index_body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1
    },
    "mappings": {
        "properties": {
            "id": { "type": "text" },
            "name": { "type": "text" },
            "album_name": { "type": "text" },
            "artists": { "type": "text" },
            "danceability": { "type": "float" },
            "energy": { "type": "float" },
            "key": { "type": "text" },
            "loudness": { "type": "float" },
            "mode": { "type": "text" },
            "speechiness": { "type": "float" },
            "acousticness": { "type": "float" },
            "instrumentalness": { "type": "float" },
            "liveness": { "type": "float" },
            "valence": { "type": "float" },
            "tempo": { "type": "float" },
            "duration_ms": { "type": "float" },
            "lyrics": { "type": "text", "analyzer": "standard" },
            "embedding": {
                "type": "dense_vector", 
                "dims": 768, 
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}

# Crear el índice con el mapeo correcto
if not es.indices.exists(index="songs"):
    es.indices.create(index="songs", body=index_body)
    print(f"Índice 'songs' creado con éxito.")
else:
    print(f"El índice 'songs' ya existe.")

# Crear el índice si no existe
index_name = "songs"

if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, body=index_body)
    print(f"Índice '{index_name}' creado con éxito.")
else:
    print(f"El índice '{index_name}' ya existe.")

#Conexion al bucket
session = boto3.Session(
    aws_access_key_id= ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)

# Crear un cliente de S3
s3 = session.client('s3')

#getconnection maria db
def get_connection():
    return pymysql.connect(
        host=MARIADB,
        user=MARIADB_USER,
        password=MARIADB_PASS,
        db=MARIADB_DB
    )


# Función para verificar si una canción ya ha sido procesada
def is_song_processed(song_id, connection):
    cursor = connection.cursor()
    query = "SELECT 1 FROM processed_songs WHERE id = %s"
    cursor.execute(query, (song_id,))
    result = cursor.fetchone()
    return result is not None

# Función para verificar si un archivo ya ha sido procesado
def is_file_processed(filename, connection):
    cursor = connection.cursor()
    query = "SELECT 1 FROM processed_files WHERE filename = %s"
    cursor.execute(query, (filename,))
    result = cursor.fetchone()
    return result is not None

# Función para insertar una canción como procesada
def mark_song_as_processed(song_id, connection):
    cursor = connection.cursor()
    insert_query = "INSERT INTO processed_songs (id) VALUES (%s)"
    cursor.execute(insert_query, (song_id,))
    connection.commit()

# Función para insertar un archivo como procesado
def mark_file_as_processed(filename, connection):
    cursor = connection.cursor()
    insert_query = "INSERT INTO processed_files (filename, processed) VALUES (%s, %s)"
    cursor.execute(insert_query, (filename, 1))
    connection.commit()


# Función para descargar un archivo desde S3
def download_from_s3(filename):
    response = s3.get_object(Bucket=BUCKET, Key=filename)
    return response['Body'].read().decode('utf-8')

# Función para generar embedding usando Hugging Face API
def generate_embedding(text):
    response = requests.post(f"http://{HUGGING_FACE_API}:{HUGGING_FACE_API_PORT}/encode", json={"text": text})
    if response.status_code == 200:
        embedding_data = response.json()  # Obtener el JSON completo
        embedding = embedding_data.get("embeddings", None)  # Extraer el embedding
        if embedding:
            return embedding  # Devuelve solo el embedding
        else:
            raise Exception(f"No se encontró el embedding en la respuesta: {embedding_data}")
    else:
        raise Exception(f"Error al generar embedding desde Hugging Face API, Status Code: {response.status_code}")

def process_csv(data, filename, batch_size=1):
    # Leer el CSV usando pandas
    df = pd.read_csv(StringIO(data), delimiter=',', encoding='utf-8')
    connection = pymysql.connect(user=MARIADB_USER, password=MARIADB_PASS, host=MARIADB, database=MARIADB_DB)
    
    # Verificar si el archivo ya ha sido procesado
    if is_file_processed(filename, connection):
        print(f"El archivo {filename} ya ha sido procesado.")
        connection.close()
        return

    # Lista para acumular los documentos por lotes
    documents = []
    total_docs = 0

    # Iterar sobre cada fila, generar el embedding y preparar el documento para Elasticsearch
    for index, row in df.iterrows():
        # Verificar si la canción ya ha sido procesada
        song_id = row['id']  # Asegúrate de tener el identificador de la canción (ajústalo a tu esquema)

        if is_song_processed(song_id, connection):
            print(f"La canción {song_id} ya ha sido procesada. Saltando.")
            continue

        # Procesar las lyrics y otros campos
        if pd.isna(row['album_name']) or row['album_name'] == "":
            row['album_name'] = "Unknown Album"
        if pd.isna(row['lyrics']) or row['lyrics'] == "":
            row['lyrics'] = "No lyrics available"
        if pd.isna(row['name']) or row['name'] == "":
            row['name'] = "Unknown Song"
        if pd.isna(row['artists']) or row['artists'] == "":
            row['artists'] = "Unknown Artist"

        lyrics = row['lyrics']
        embedding = generate_embedding(lyrics)
        row['embedding'] = embedding

        # Convertir la fila a diccionario y añadirla a la lista de documentos
        document = row.to_dict()

        # Preparar el formato necesario para la API Bulk de Elasticsearch
        documents.append({
            "_index": "songs",
            "_source": document
        })

        total_docs += 1

        # Si alcanzamos el tamaño del lote, subir los documentos a Elasticsearch
        if len(documents) >= batch_size:
            success, failed = bulk(es, documents)
            print(f"{success} documentos subidos exitosamente, {failed} documentos fallaron.")
            
            # Marcar la canción como procesada
            mark_song_as_processed(song_id, connection)

            # Vaciar la lista de documentos una vez subidos
            documents = []

    # Subir cualquier documento restante
    if documents:
        success, failed = bulk(es, documents)
        print(f"{success} documentos subidos exitosamente, {failed} documentos fallaron.")

    # Marcar el archivo como procesado
    mark_file_as_processed(filename, connection)
    connection.close()
    
# Función para consumir mensajes desde RabbitMQ
def callback(ch, method, properties, body):
    filename = body.decode('utf-8')
    connection = pymysql.connect(user=MARIADB_USER, password=MARIADB_PASS, host=MARIADB, database=MARIADB_DB)
    print(f"Recibido mensaje: {filename}")
    # Verificar si el archivo ya fue procesado
    if is_file_processed(filename, connection):
        print(f"Archivo {filename} ya fue procesado. Se ignora.")
        return
    connection.close()
    # Descargar archivo desde S3 y procesarlo
    data = download_from_s3(filename)
    process_csv(data, filename)
    print(f"Archivo {filename} procesado correctamente.")

# Conexión a RabbitMQ y configuración de consumo
def start_rabbitmq_consumer():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE)

    # Consumir mensajes de la cola
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback, auto_ack=True)
    print('Esperando mensajes. Presiona CTRL+C para salir.')
    channel.start_consuming()

if __name__ == '__main__':
    print("Iniciando el consumidor de RabbitMQ...")
    start_rabbitmq_consumer()