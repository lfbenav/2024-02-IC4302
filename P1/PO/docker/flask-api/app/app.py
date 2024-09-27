from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from elasticsearch import Elasticsearch
import os
#import pylibmc
import boto3
import pymysql
from datetime import datetime
from prometheus_client import start_http_server, Summary, Counter, Histogram, generate_latest
import base64

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuración de hugging-face-api
HUGGING_FACE_API = os.getenv('HUGGING_FACE_API')
HUGGING_FACE_API_PORT = os.getenv("HUGGING_FACE_PORT")
print(HUGGING_FACE_API)
print(HUGGING_FACE_API_PORT)
# Configuración de Elasticsearch
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASS")
ELASTIC_USER = os.getenv("ELASTIC_USER")
ELASTIC_SERVICE = os.getenv("ELASTIC")
ELASTIC_PORT = os.getenv("ELASTIC_PORT")
es_url = f"http://{ELASTIC_SERVICE}:{ELASTIC_PORT}"

# Conexión a Elasticsearch
es = Elasticsearch(es_url, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))

# Configuración de MariaDB
MARIADB_USER = os.getenv('MARIADB_USER')
MARIADB_PASS = os.getenv('MARIADB_PASS')
MARIADB = os.getenv('MARIADB')
MARIADB_DB = os.getenv('MARIADB_DB')
MARIADB_TABLE = os.getenv('MARIADB_TABLE')

mariadb_config = {
    'host': MARIADB,
    'user': MARIADB_USER,
    'password': MARIADB_PASS,
    'database': MARIADB_DB
}

def get_connection():
    return pymysql.connect(
        host=os.getenv('MARIADB'),
        user=os.getenv('MARIADB_USER'),
        password=os.getenv('MARIADB_PASS'),
        db=os.getenv('MARIADB_DB')
    )

# Métricas de Prometheus
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests (count)', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])
CACHE_HITS = Counter('cache_hits_total', 'Total Cache Hits', ['cache_type'])
CACHE_MISSES = Counter('cache_misses_total', 'Total Cache Misses', ['cache_type'])

# Configuración de Memcached
MEMCACHED_HOST = os.getenv('MEMCACHED_HOST')
MEMCACHED_PORT = os.getenv('MEMCACHED_PORT')
# memcached_client = pylibmc.Client([f"{MEMCACHED_HOST}:{MEMCACHED_PORT}"])
# TODO Arreglar memcached

# Función para determinar si usa cache
def get_cache_client(cache_type):
    if cache_type == 'memcached':
        return None #memcached_client # TODO Arreglar memcached
    else:
        return None

# Ruta para validar funcionamiento
@app.route("/")
def index():
    return "Funciona correctamente!"

# Ruta para conseguir las metricas
@app.route("/metrics")
def metrics():
    return generate_latest(), 200

# Ruta para registrar usuarios
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password").encode('utf-8')  # Convert password to bytes

    # Base64 encode the password
    encryptedPassword = base64.b64encode(password).decode('utf-8')  # Encode to base64 and then decode to a string

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
            cursor.execute(sql, (username, encryptedPassword))
            connection.commit()

        return jsonify({"status": "Usuario registrado con éxito"}), 200
    finally:
        connection.close()

# Ruta para loguear usuarios
@app.route("/login", methods=["POST"])  # Cambiado a POST
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password").encode('utf-8')

    # Encriptamos la contraseña como antes
    encryptedPassword = base64.b64encode(password).decode('utf-8')

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT username FROM users WHERE username = %s and password = %s"
            cursor.execute(sql, (username, encryptedPassword))
            result = cursor.fetchone()

            if result is None:
                return jsonify({"status": "Inicio fallido"}), 404
            else:
                return jsonify({"status": "Inicio de sesión exitoso"}), 200
    finally:
        connection.close()

# Ruta ask para generar los resultados de una consulta
@app.route("/ask", methods=["POST"])
def ask():
    # Obtener el JSON del body
    data = request.get_json()
    question = data.get("question")
    
    # Verificar si el campo 'question' fue enviado
    if question is None:
        return jsonify({"error": "El campo 'question' es requerido"}), 400
    
    try:
        # Codificar el texto usando el servicio de Hugging Face
        response_hf = requests.post(f"http://{HUGGING_FACE_API}:{HUGGING_FACE_API_PORT}/encode", json={"text": question})
        
        # Verificar si la respuesta fue exitosa
        if response_hf.status_code != 200:
            return jsonify({"error": "Error al obtener el embedding"}), 500
        
        # Obtener el embedding del JSON
        embedding_question = response_hf.json().get("embeddings", [])
        
        # Si no se encuentra el embedding
        if not embedding_question:
            return jsonify({"error": "No se pudo generar el embedding"}), 500
        
        # Definir la consulta KNN en Elasticsearch
        query_knn = {
            "knn": {
                "field": "embedding",               # Campo donde están los embeddings
                "query_vector": embedding_question,  # El vector de la consulta
                "k": 10,                            # Número de vecinos más cercanos
                "num_candidates": 50                # Número de candidatos que se procesarán antes de elegir los más cercanos
            }
        }
        # Ejecutar la búsqueda en Elasticsearch
        response = es.search(index="songs", body=query_knn)
        
        # Crear la lista de resultados
        results = []
        for hit in response['hits']['hits']:
            song_name = hit['_source'].get('name', 'Unknown Song')
            lyrics = hit['_source'].get('lyrics', 'No lyrics available')
            artists = hit['_source'].get('artists', 'No artists available')
            # Agregar el resultado a la lista
            results.append({
                "name": song_name,
                "lyrics": lyrics,
                "artists": artists
            })
        
        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para publicar los prompts
@app.route("/publish", methods=["POST"])
def publish():
    data = request.get_json()
    prompt = data.get("prompt")
    username = data.get("username")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO prompts (username, prompt, date, likes) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (username, prompt, datetime.now(), 0))
            connection.commit()

        return jsonify({"status": "Prompt publicado con éxito"}), 200
    finally:
        connection.close()

# Ruta para buscar por prompts similares
@app.route("/search", methods=["GET"])
def search():
    # Obtener el parámetro 'keyword' de la URL
    keyword = request.args.get("keyword")
    
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Buscar en la base de datos usando LIKE
            sql = "SELECT id, username, prompt, date, likes FROM prompts WHERE prompt LIKE %s"
            cursor.execute(sql, ('%' + keyword + '%',))
            results = cursor.fetchall()

        # Convertir los resultados en un formato legible (lista de diccionarios)
        prompts = []
        for result in results:
            prompt = {
                "id": result[0],
                "username": result[1],
                "prompt": result[2],
                "date": result[3],
                "likes": result[4]
            }
            prompts.append(prompt)

        return jsonify({"results": prompts}), 200
    finally:
        connection.close()


# Ruta para dar like a un prompt
@app.route("/like", methods=["POST"])
def like():
    data = request.get_json()
    username = data.get("username") 
    prompt_id = data.get("prompt_id")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Verificar si el usuario ya ha dado "like" al prompt
            sql_check = "SELECT * FROM likes WHERE username = %s AND prompt_id = %s"
            cursor.execute(sql_check, (username, prompt_id))
            like_exists = cursor.fetchone()

            if like_exists:
                return jsonify({"error": "You have already liked this prompt"}), 400

            # Insertar el "like" en la tabla de 'likes'
            sql_like = "INSERT INTO likes (username, prompt_id) VALUES (%s, %s)"
            cursor.execute(sql_like, (username, prompt_id))

            # Actualizar el número de "likes" en el prompt original
            sql_update_likes = "UPDATE prompts SET likes = likes + 1 WHERE id = %s"
            cursor.execute(sql_update_likes, (prompt_id,))

            # Verificar si se actualizó correctamente el número de likes
            cursor.execute("SELECT likes FROM prompts WHERE id = %s", (prompt_id,))
            updated_likes = cursor.fetchone()

            # Obtener el contenido del prompt para republicarlo
            sql_fetch = "SELECT prompt FROM prompts WHERE id = %s"
            cursor.execute(sql_fetch, (prompt_id,))
            prompt_data = cursor.fetchone()

            if not prompt_data:
                return jsonify({"error": "Prompt not found"}), 404

            prompt_text = prompt_data[0]

            # Republicar el prompt bajo el nombre del usuario que dio "like"
            sql_republish = "INSERT INTO prompts (username, prompt, date, likes) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql_republish, (username, prompt_text, datetime.now(), 0))

            connection.commit()

        return jsonify({"status": "Prompt liked and republished successfully", "updated_likes": updated_likes[0]}), 200
    finally:
        connection.close()