import os
import pika
import pymysql
import requests
import hashlib
import json
from datetime import datetime
from dotenv import load_dotenv

# Para los Unit Tests
import unittest
from unittest.mock import ANY, patch, MagicMock
from moto import mock_aws 

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

PATH = os.getenv('XPATH')   #PATH (por si no sirve)
print(PATH)
API_BASE = os.getenv('API_BASE', 'https://api.crossref.org/works/')
# Conectar a RabbitMQ
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ, credentials=credentials))
channel = connection.channel()

# Declarar la cola
channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)



def get_db_connection():
    # Establecer y retornar una conexión a la base de datos MariaDB utilizando las credenciales y parámetros globales
    return pymysql.connect(user=MARIADB_USER, password=MARIADB_PASS, host=MARIADB, database=MARIADB_DB)

# Procesar mensaje recibido de RabbitMQ
def process_message(ch, method, properties, body):
    # Decodificar el cuerpo del mensaje para obtener el ID del trabajo
    job_id = body.decode()
    # Obtener una conexión a la base de datos
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Actualizar el estado del trabajo a "in-progress" en la base de datos
        cursor.execute(f"UPDATE {MARIADB_TABLE} SET status='in-progress' WHERE id=%s", (job_id,))
        connection.commit()

        # Obtener la lista de DOIs del trabajo desde la base de datos
        cursor.execute(f"SELECT dois FROM {MARIADB_TABLE} WHERE id=%s", (job_id,))
        result = cursor.fetchone()
        if result:
            # Convertir la cadena JSON de DOIs a una lista
            dois = json.loads(result[0])
            omitted = [] # Lista para almacenar los DOIs omitidos
            
            for doi_info in dois:
                doi = doi_info.split(',')[0]  # Extraer el DOI del string completo
                # Construir la URL de la API para obtener la información del documento
                url = f"{API_BASE}{doi}"
                # Enviar una solicitud GET a la API
                response = requests.get(url)

                if response.status_code == 200:
                    # Si la respuesta es exitosa, guardar el documento JSON en un archivo
                    document = response.json()
                    filename = hashlib.md5(doi.encode()).hexdigest() + ".json"
                    with open(os.path.join(PATH, filename), 'w') as f:
                        json.dump(document, f)
                else:
                    # Si el DOI no es válido, agregarlo a la lista de omitidos
                    print("El doi: ", doi, " no es valido")
                    omitted.append(doi)

            # Actualizar el estado del trabajo a "done" y guardar la fecha de finalización y los omitidos
            cursor.execute(f"UPDATE {MARIADB_TABLE} SET status='done', fecha_fin=%s, omitted=%s WHERE id=%s",
                            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), json.dumps(omitted), job_id))
            connection.commit()

    except Exception as e:
        # Manejar cualquier excepción que ocurra durante el procesamiento del trabajo
        print(f"Error procesando el job {job_id}: {e}")
    finally:
        # Cerrar el cursor y la conexión a la base de datos
        cursor.close()
        connection.close()
        # Confirmar que el mensaje ha sido procesado correctamente para RabbitMQ
        ch.basic_ack(delivery_tag=method.delivery_tag)

class TestProcessMessage(unittest.TestCase):
    # Se utiliza patch para sustituir temporalmente los servicios
    @patch('pymysql.connect')
    @patch('pika.BlockingConnection')
    @patch('requests.get')
    @patch('os.path.join', return_value='path/to/file.json')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_process_message(self, mock_open, mock_os_path_join, mock_requests_get, mock_pika_blocking_connection, mock_pymysql_connect):
        # Mock de la conexión a la base de datos 
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_pymysql_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Configuración del mock para requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "value"}
        mock_requests_get.return_value = mock_response

        # Datos de prueba
        job_id = 'job1'
        dois = json.dumps(['10.1000/abcd1234'])
        mock_cursor.fetchone.return_value = (dois,)

        # Mock del canal RabbitMQ
        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 'mock_tag'

        # Nos aseguramos de que body sea de tipo bytes
        body = job_id.encode()  # Se codifica el string 'job1' a bytes

        # Llamar a la función process_message
        with patch('__main__.get_db_connection', return_value=mock_connection):
            process_message(mock_channel, mock_method, None, body)

        # Verificaciones
        # Se usa assert_any_call para asegurarnos de que los metodos fueron llamados en algun momento
        mock_cursor.execute.assert_any_call(f"UPDATE objects SET status='in-progress' WHERE id=%s", (job_id,))
        mock_cursor.execute.assert_any_call(f"SELECT dois FROM objects WHERE id=%s", (job_id,))
        mock_cursor.execute.assert_any_call(
            f"UPDATE objects SET status='done', fecha_fin=%s, omitted=%s WHERE id=%s",
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), json.dumps([]), job_id)
        )
        # assert_called_once_with también sirve para asegurarnos de que los métodos fueron llamados
        # con ciertos argumentos
        mock_open.assert_called_once_with('path/to/file.json', 'w')
        mock_requests_get.assert_called_once_with('https://api.crossref.org/works/10.1000/abcd1234')
        mock_channel.basic_ack.assert_called_once_with(delivery_tag='mock_tag')

#if __name__ == "__main__":
    # Se ejecutan las pruebas unitarias
    #unittest.main()

# Configurar el consumidor
channel.basic_qos(prefetch_count=1) # Limitar la cantidad de mensajes no confirmados a 1
channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=process_message)
# Iniciar el ciclo de consumo de mensajes
print('Esperando mensajes. Presiona CTRL+C para salir')
channel.start_consuming()
