import boto3
import pymysql
import pika
import os
import json
import random
import string
from datetime import datetime

# Para los Unit Tests
import unittest
from unittest.mock import ANY, patch, MagicMock
from moto import mock_aws 

BUCKET="2024-02-ic4302-gr1"
ACCESS_KEY="AKIAQ2VOGXQDTWAX4PUY"
SECRET_KEY="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"

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



def list_s3_objects(bucket, access_key, secret_key):
    #Listar objetos en S3
    # Crear un cliente S3 utilizando las credenciales proporcionadas
    s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    # Listar los objetos en el bucket especificado
    response = s3.list_objects_v2(Bucket=bucket)
    # Retornar la lista de objetos si existen, o una lista vacía si no hay objetos
    return response.get('Contents', [])

def download_s3_object(bucket, key, access_key, secret_key):
    # Descargar un objeto específico de S3
    # Crear un cliente S3 utilizando las credenciales proporcionadas
    s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    # Obtener el objeto del bucket y la clave especificados
    obj = s3.get_object(Bucket=bucket, Key=key)
    # Leer y decodificar el contenido del objeto, luego retornarlo como una cadena de texto
    return obj['Body'].read().decode('utf-8')

def create_jobs(data, job_size):
    # Crear trabajos a partir de los datos
    # Dividir los datos en líneas individuales
    lines = data.splitlines()
    # Calcular el número de trabajos a crear según el tamaño de cada trabajo
    num_jobs = len(lines) // job_size
    # Inicializar una lista para almacenar los trabajos
    jobs = []
    for i in range(num_jobs):
        # Crear un ID único para el trabajo utilizando una combinación de letras y números
        job_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        # Crear un diccionario que represente el trabajo con la información relevante
        job = {
            'id': job_id,
            'status': 'pending',
            'dois': lines[i*job_size:(i+1)*job_size],
            'omitted': [],
            'fecha_inicio': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_fin': None
        }
        # Agregar el trabajo a la lista de trabajos
        jobs.append(job)
    # Retornar la lista de trabajos creados
    return jobs

def save_jobs_to_db(jobs, mariadb_user, mariadb_pass, mariadb_host, mariadb_db, mariadb_table):
    # Guardar trabajos en la base de datos
    # Establecer una conexión a la base de datos MariaDB
    connection = pymysql.connect(user=mariadb_user, password=mariadb_pass, host=mariadb_host, database=mariadb_db)
    try:
        # Crear un cursor para ejecutar comandos SQL
        cursor = connection.cursor()
        for job in jobs:
            # Guardar cada trabajo en la base de datos
            try:
                # Convertir la lista de DOIs y omitidos en cadenas JSON para almacenarlas en la base de datos
                dois_str = json.dumps(job['dois'])  # Convertir la lista de DOIS en un Json String
                omitted_str = json.dumps(job['omitted'])  # Convertir la lista de omitidos a un JSON string 
                # Ejecutar la consulta SQL para insertar el trabajo en la tabla correspondiente
                cursor.execute(f"INSERT INTO {mariadb_table} (id, status, dois, omitted, fecha_inicio, fecha_fin) VALUES (%s, %s, %s, %s, %s, %s)", 
                                (job['id'], job['status'], dois_str, omitted_str, job['fecha_inicio'], job['fecha_fin']))
                
            except pymysql.MySQLError as e:
                # Manejar errores de SQL durante la inserción de un trabajo específico
                print(f"Error al insertar el job {job['id']}: {e}")
        # Confirmar los cambios en la base de datos
        connection.commit()
    finally:
        # Cerrar el cursor y la conexión a la base de datos
        cursor.close()
        connection.close()

def publish_jobs_to_rabbitmq(jobs, rabbitmq_user, rabbitmq_pass, rabbitmq_host, rabbitmq_queue):   
    #Publicar trabajos en RabbitMQ
    # Crear credenciales para la conexión a RabbitMQ
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    try:
        # Establecer una conexión con el servidor RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials))
        # Crear un canal de comunicación con RabbitMQ
        channel = connection.channel()
        # Declarar la cola de RabbitMQ y asegurarse de que es durable (persistente)
        channel.queue_declare(queue=rabbitmq_queue, durable=True)  # Asegurarse de que la cola se declara como durable
        for job in jobs:
            # Publicar cada trabajo en la cola de Rabbit
            channel.basic_publish(
                exchange='', # Usar el intercambio predeterminado
                routing_key=rabbitmq_queue, # Enviar a la cola especificada
                body=job['id'],  # El cuerpo del mensaje será el ID del trabajo
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer el mensaje persistente (asegurarse de que el mensaje no se pierda si el servidor de RabbitMQ se reinicia o falla antes de que el mensaje sea procesado)
                ))
        # Cerrar la conexión a RabbitMQ después de publicar todos los trabajos
        connection.close()
    except Exception as e:
        # Manejar errores si la conexión a RabbitMQ falla
        print(f"Failed to connect to RabbitMQ: {e}")

class TestS3Functions(unittest.TestCase):

    @mock_aws # Decorator para que todas las llamadas se simulan automáticamente.
    def test_list_s3_objects(self):
        # Se crea un bucket en el entorno simulado
        s3 = boto3.client('s3')
        s3.create_bucket(Bucket = 'mybucket')
        
        # Añadir objetos al bucket simulado
        s3.put_object(Bucket = 'mybucket', Key='file1.txt', Body='data1')
        s3.put_object(Bucket = 'mybucket', Key='file2.txt', Body='data2')
        
        objects = list_s3_objects('mybucket', 'test-access-key', 'test-secret-key')
        
        # Revisión de resultados
        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[0]['Key'], 'file1.txt')
        self.assertEqual(objects[1]['Key'], 'file2.txt')
    
    @mock_aws
    def test_download_s3_object(self):
        # Configuracion
        key_name = 'test.txt'
        content = 'Archivo de Prueba.'
        s3 = boto3.client('s3')
        s3.create_bucket(Bucket = 'mybucket')
        s3.put_object(Bucket = 'mybucket', Key = key_name, Body = content)

        downloaded_content = download_s3_object('mybucket', key_name, 'test-access-key', 'test-secret-key')

        # Se revisa si el contenido descargado es el mismo del content
        self.assertEqual(downloaded_content, content)

    def test_create_jobs(self):
        # Prueba con 20 DOIs
        data = "\n".join([f"doi{i}" for i in range(1, 21)]) + "\n"
        job_size = 10
        
        jobs = create_jobs(data, job_size)
        
        # Se revisa si el num de jobs es el correcto
        self.assertEqual(len(jobs), 2)

        self.assertEqual(jobs[0]['dois'], [f"doi{i}" for i in range(1, 11)])
        self.assertEqual(jobs[1]['dois'], [f"doi{i}" for i in range(11, 21)])

        for job in jobs:
            self.assertIsNotNone(job['fecha_inicio']) # El campo fecha_inicio tiene que estar definido
            datetime.strptime(job['fecha_inicio'], '%Y-%m-%d %H:%M:%S') # Revisar formato de la fecha
            self.assertEqual(job['status'], 'pending') # El estado inicial debe ser pending
            self.assertIsNone(job['fecha_fin'])
            self.assertIsNotNone(job['id'])
            self.assertEqual(len(job['id']), 8) # los IDs son de 8 caracteres
    
    @patch('pymysql.connect')  
    def test_save_jobs_to_db(self, mock_connect):
        # Se simulan las conexiones
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        
        # Configuración de los mocks
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        
        # Datos de prueba
        jobs = [ # Datos para la prueba. 10 DOIs por job
            {
                'id': 'job1',
                'status': 'pending',
                'dois': [f"doi{i}" for i in range(1, 11)],  
                'omitted': [],
                'fecha_inicio': '2024-08-14 10:00:00',
                'fecha_fin': None
            },
            {
                'id': 'job2',
                'status': 'pending',
                'dois': [f"doi{i}" for i in range(11, 21)],  
                'omitted': [],
                'fecha_inicio': '2024-08-14 11:30:00',
                'fecha_fin': None
            }
        ]

        # Llamada a la función que se esta probando
        mariadb_table = 'jobs'
        save_jobs_to_db(jobs, 'test_user', 'test_pass', 'localhost', 'test_db', mariadb_table)
        
        # Verificar las llamadas de INSERT
        mock_cursor.execute.assert_any_call(
            f"INSERT INTO {mariadb_table} (id, status, dois, omitted, fecha_inicio, fecha_fin) VALUES (%s, %s, %s, %s, %s, %s)",
            ('job1', 'pending', json.dumps([f"doi{i}" for i in range(1, 11)]), '[]', '2024-08-14 10:00:00', None)
        )
        
        mock_cursor.execute.assert_any_call(
            f"INSERT INTO {mariadb_table} (id, status, dois, omitted, fecha_inicio, fecha_fin) VALUES (%s, %s, %s, %s, %s, %s)",
            ('job2', 'pending', json.dumps([f"doi{i}" for i in range(11, 21)]), '[]', '2024-08-14 11:30:00', None)
        )
        
        self.assertEqual(mock_connection.commit.call_count, 1)

        # Revisar el estado de las conexiones
        mock_cursor.close.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch('pika.BlockingConnection')
    def test_publish_jobs_to_rabbitmq(self, mock_blocking_connection):
        # Se crea un mock para la conexión de RabbitMQ
        mock_connection = MagicMock()
        # Configuración de mocks
        mock_channel = mock_connection.channel.return_value
        mock_blocking_connection.return_value = mock_connection

        # ejemplo de prueba 
        jobs = [{'id': 'job1'}]
        publish_jobs_to_rabbitmq(jobs, 'user', 'pass', 'host', 'queue')

        mock_channel.basic_publish.assert_called_once_with(
        exchange='',
        routing_key='queue',
        body='job1',
        properties=pika.BasicProperties(
            delivery_mode=2,  
        )
    )   
        # Se verifica que la conexión se cerró después de publicar los jobs
        mock_connection.close.assert_called_once()

if __name__ == "__main__":
    # Ejecutar los unit tests
    unittest.main()
    
    # Listar objetos en el bucket S3 especificado
    objects = list_s3_objects(BUCKET, ACCESS_KEY, SECRET_KEY)
    for obj in objects:
        # Descargar el contenido de cada objeto S3
        data = download_s3_object(BUCKET, obj['Key'], ACCESS_KEY, SECRET_KEY)
        # Crear trabajos a partir de los datos descargados
        jobs = create_jobs(data, JOB_SIZE)
        # Guardar los trabajos en la base de datos
        save_jobs_to_db(jobs, MARIADB_USER, MARIADB_PASS, MARIADB, MARIADB_DB, MARIADB_TABLE)
        # Publicar los trabajos en la cola de RabbitMQ
        publish_jobs_to_rabbitmq(jobs, RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ, RABBITMQ_QUEUE)
print("El proceso ha terminado")

