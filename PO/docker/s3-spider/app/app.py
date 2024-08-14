import boto3
import pymysql
import pika
import os
import hashlib
import json
import random
import string
from datetime import datetime

# Variables de entorno
BUCKET="2024-02-ic4302-gr1"
ACCESS_KEY="AKIAQ2VOGXQDTWAX4PUY"
SECRET_KEY="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"

RABBITMQ_USER = "guest"
RABBITMQ_PASS = "guest"
RABBITMQ_QUEUE = "queue"
RABBITMQ = "localhost"
MARIADB_USER = "root"
MARIADB_PASS = "1234"
MARIADB = "localhost"
MARIADB_DB = "control"
MARIADB_TABLE = "objects"

JOB_SIZE = 10

def list_s3_objects(bucket, access_key, secret_key):
    s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    response = s3.list_objects_v2(Bucket=bucket)
    return response.get('Contents', [])

def download_s3_object(bucket, key, access_key, secret_key):
    s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj['Body'].read().decode('utf-8')

def create_jobs(data, job_size):
    lines = data.splitlines()
    num_jobs = len(lines) // job_size
    jobs = []
    for i in range(num_jobs):
        job_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        job = {
            'id': job_id,
            'status': 'pending',
            'dois': lines[i*job_size:(i+1)*job_size],
            'omitted': [],
            'fecha_inicio': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_fin': None
        }
        jobs.append(job)
    return jobs

"""
Version OG
def save_jobs_to_db(jobs, mariadb_user, mariadb_pass, mariadb_host, mariadb_db, mariadb_table):
    connection = pymysql.connect(user=mariadb_user, password=mariadb_pass, host=mariadb_host, database=mariadb_db)
    cursor = connection.cursor()
    for job in jobs:
        try:
            dois_str = json.dumps(job['dois'])  # Convertir la lista de DOIs a una cadena JSON
            print(dois_str)
            break
            cursor.execute(f"INSERT INTO {mariadb_table} (id, status, dois, omitted, fecha_inicio, fecha_fin) VALUES (%s, %s, %s, %s, %s, %s)", 
                            (job['id'], job['status'], dois_str, json.dumps(job['omitted']), job['fecha_inicio'], job['fecha_fin']))
        except pymysql.MySQLError as e:
            print(f"Error al insertar el job {job['id']}: {e}")
    connection.commit()
    cursor.close()
    connection.close()
"""
def save_jobs_to_db(jobs, mariadb_user, mariadb_pass, mariadb_host, mariadb_db, mariadb_table):
    connection = pymysql.connect(user=mariadb_user, password=mariadb_pass, host=mariadb_host, database=mariadb_db)
    cursor = connection.cursor()
    for job in jobs:
        try:
            dois_str = json.dumps(job['dois'])  # Convert the list of DOIs to a JSON string
            omitted_str = json.dumps(job['omitted'])  # Convert omitted list to JSON string
            cursor.execute(f"INSERT INTO {mariadb_table} (id, status, dois, omitted, fecha_inicio, fecha_fin) VALUES (%s, %s, %s, %s, %s, %s)", 
                            (job['id'], job['status'], dois_str, omitted_str, job['fecha_inicio'], job['fecha_fin']))
        except pymysql.MySQLError as e:
            print(f"Error al insertar el job {job['id']}: {e}")
    connection.commit()
    cursor.close()
    connection.close()

def publish_jobs_to_rabbitmq(jobs, rabbitmq_user, rabbitmq_pass, rabbitmq_host, rabbitmq_queue):
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    print(f"Connecting to RabbitMQ at {rabbitmq_host} with user {rabbitmq_user}")
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials))
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_queue, durable=True)  # Asegurarse de que la cola se declara como durable
        for job in jobs:
            channel.basic_publish(
                exchange='',
                routing_key=rabbitmq_queue,
                body=job['id'],
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer el mensaje persistente
                ))
        connection.close()
    except Exception as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        
if __name__ == "__main__":
    objects = list_s3_objects(BUCKET, ACCESS_KEY, SECRET_KEY)
    for obj in objects:
        data = download_s3_object(BUCKET, obj['Key'], ACCESS_KEY, SECRET_KEY)
        jobs = create_jobs(data, JOB_SIZE)
        save_jobs_to_db(jobs, MARIADB_USER, MARIADB_PASS, MARIADB, MARIADB_DB, MARIADB_TABLE)
        publish_jobs_to_rabbitmq(jobs, RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ, RABBITMQ_QUEUE)
print("OKAY....")