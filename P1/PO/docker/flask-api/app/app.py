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

# Solicitudes para la sección ME
# Ruta para obtener mi usuario
@app.route("/me/getProfile", methods=["GET"])
def getProfile():
    data = request.get_json()
    username = data.get("username")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT username FROM users WHERE username = %s"
            cursor.execute(sql, (username))
            result = cursor.fetchone()

            return jsonify({"results": result}), 200
    finally:
        connection.close()

# Ruta para cambiar mi username
@app.route("/me/updateUsername", methods=["POST"])
def updateUsername():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password").encode('utf-8')
    newUsername = data.get("newUsername")
    encryptedPassword = base64.b64encode(password).decode('utf-8')  # Encripta la contraseña

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Desactivar restricciones de clave foránea
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            
            # Verificar si el usuario y la contraseña son correctos
            sql_check = "SELECT * FROM users WHERE username = %s AND password = %s"
            cursor.execute(sql_check, (username, encryptedPassword))
            user = cursor.fetchone()

            if not user:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")  # Rehabilitar restricciones de clave foránea
                return jsonify({"error": "Invalid username or password"}), 403

            # Verificar si el nuevo nombre de usuario ya está en uso
            sql_check_new_username = "SELECT * FROM users WHERE username = %s"
            cursor.execute(sql_check_new_username, (newUsername,))
            if cursor.fetchone():
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")  # Rehabilitar restricciones de clave foránea
                return jsonify({"error": "Username already exists"}), 400

            # Actualizar el username en todas las tablas relevantes
            sql_users = "UPDATE users SET username = %s WHERE username = %s"
            sql_prompts = "UPDATE prompts SET username = %s WHERE username = %s"
            sql_likes = "UPDATE likes SET username = %s WHERE username = %s"
            sql_follows_follower = "UPDATE follows SET follower_username = %s WHERE follower_username = %s"
            sql_follows_followee = "UPDATE follows SET followee_username = %s WHERE followee_username = %s"

            cursor.execute(sql_users, (newUsername, username))
            cursor.execute(sql_prompts, (newUsername, username))
            cursor.execute(sql_likes, (newUsername, username))
            cursor.execute(sql_follows_follower, (newUsername, username))
            cursor.execute(sql_follows_followee, (newUsername, username))

            connection.commit()

            # Rehabilitar restricciones de clave foránea
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        return jsonify({"status": "Usuario registrado con éxito"}), 200
    finally:
        connection.close()



# Ruta para cambiar mi contraseña
@app.route("/me/updatePassword", methods=["POST"])
def updatePassword():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password").encode('utf-8')  # Convertimos a bytes
    newPassword = data.get("newPassword").encode('utf-8')  # Convertimos a bytes
    encryptedPassword = base64.b64encode(password).decode('utf-8')  # Encriptamos la contraseña actual
    encryptedNewPassword = base64.b64encode(newPassword).decode('utf-8')  # Encriptamos la nueva contraseña

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE users SET password = %s WHERE username = %s and password = %s"
            cursor.execute(sql, (encryptedNewPassword, username, encryptedPassword))
            connection.commit()

        return jsonify({"status": "Usuario registrado con éxito"}), 200
    finally:
        connection.close()


# Ruta para obtener mis prompts que he hecho
@app.route("/me/getMyPrompts", methods=["GET"])
def getMyPrompts():
    # Obtener el parámetro 'username' de la URL
    username = request.args.get("username")  # request.args para obtener parámetros de la URL

    if not username:
        return jsonify({"error": "Username is required"}), 400

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Incluir el 'id' del prompt en la consulta
            sql = "SELECT id, username, prompt, date, likes FROM prompts WHERE username = %s"
            cursor.execute(sql, (username,))
            results = cursor.fetchall()

            # Convertir los resultados en un formato legible (lista de diccionarios)
            prompts_list = [{
                "id": row[0],         # ID del prompt
                "username": row[1],
                "prompt": row[2],
                "date": row[3],
                "likes": row[4]
            } for row in results]

            return jsonify({"results": prompts_list}), 200
    finally:
        connection.close()

@app.route("/updatePrompt/<int:prompt_id>", methods=["PUT"])
def update_prompt(prompt_id):
    data = request.get_json()
    new_prompt = data.get("prompt")

    if not new_prompt:
        return jsonify({"error": "New prompt text is required"}), 400

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Verificar si el prompt existe
            sql_check = "SELECT * FROM prompts WHERE id = %s"
            cursor.execute(sql_check, (prompt_id,))
            prompt = cursor.fetchone()

            if not prompt:
                return jsonify({"error": "Prompt not found"}), 404

            # Actualizar el prompt con el nuevo texto
            sql_update = "UPDATE prompts SET prompt = %s WHERE id = %s"
            cursor.execute(sql_update, (new_prompt, prompt_id))
            connection.commit()

        return jsonify({"status": "Prompt updated successfully"}), 200
    finally:
        connection.close()
# Solicitudes para la sección Friends
# Ruta para obtener A
@app.route("/friends/random", methods=["GET"])
def get_random_users():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Fetch 20 random users from the database
            sql = "SELECT username FROM users ORDER BY RAND() LIMIT 20"
            cursor.execute(sql)
            users = cursor.fetchall()

            # Convertir la lista de tuplas en una lista simple de cadenas
            user_list = [user[0] for user in users]

        return jsonify({"users": user_list}), 200
    finally:
        connection.close()


@app.route("/friends/search", methods=["GET"])
def search_user():
    # Obtener el 'username' del usuario desde los parámetros de consulta
    username = request.args.get('username') 

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Buscar el usuario por 'username'
            sql = "SELECT username FROM users WHERE username = %s"
            cursor.execute(sql, (username,))
            user = cursor.fetchone()

        if user:
            # Devolver el resultado como un diccionario con el 'username'
            user_data = {
                "username": user[0]
            }
            return jsonify({"user": user_data}), 200
        else:
            return jsonify({"user": None}), 404
    finally:
        connection.close()



@app.route("/follow", methods=["POST"])
def follow_user():
    # Obtener los nombres de usuario (username) del seguidor y seguido
    follower_username = request.form.get('follower_username')  
    followee_username = request.form.get('followee_username')  

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Verificar si ya existe una relación de seguimiento
            sql_check = "SELECT * FROM follows WHERE follower_username = %s AND followee_username = %s"
            cursor.execute(sql_check, (follower_username, followee_username))
            follow_exists = cursor.fetchone()

            if follow_exists:
                return jsonify({"status": "Already following"}), 400

            # Si no existe la relación, insertarla
            sql_insert = "INSERT INTO follows (follower_username, followee_username) VALUES (%s, %s)"
            cursor.execute(sql_insert, (follower_username, followee_username))
            connection.commit()

        return jsonify({"status": "Follow successful"}), 200
    finally:
        connection.close()



@app.route("/friends", methods=["GET"])
def get_friends():
    follower_username = request.args.get('follower_id')   

    if not follower_username:
        return jsonify({"status": "Error", "message": "follower_username is required"}), 400

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Obtener los usuarios que el usuario sigue, basado en el username
            sql = """
            SELECT u.username 
            FROM users u
            JOIN follows f ON u.username = f.followee_username
            WHERE f.follower_username = %s
            """
            cursor.execute(sql, (follower_username,))
            friends = cursor.fetchall()

        # Convertir los resultados a un formato de lista de diccionarios
        friends_list = [{"username": friend[0]} for friend in friends]

        return jsonify({"friends": friends_list}), 200
    finally:
        connection.close()

@app.route("/feed", methods=["GET"])
def get_feed():
    username = request.args.get('username')  # Obtener el nombre de usuario del que solicita el feed

    if not username:
        return jsonify({"error": "Username is required"}), 400

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Obtener los nombres de usuario de los amigos del usuario logueado
            sql_friends = """
                SELECT followee_username 
                FROM follows 
                WHERE follower_username = %s
            """
            cursor.execute(sql_friends, (username,))
            friends = cursor.fetchall()
            friend_usernames = [f[0] for f in friends]
            friend_usernames.append(username)  # Incluir también los prompts del propio usuario

            # Obtener los prompts de los amigos y del usuario logueado, ordenados por fecha
            sql_prompts = """
                SELECT p.id, p.username, p.prompt, p.date, p.likes 
                FROM prompts p
                WHERE p.username IN %s
                ORDER BY p.date DESC
            """
            cursor.execute(sql_prompts, (tuple(friend_usernames),))
            prompts = cursor.fetchall()

        # Crear la lista de resultados con id, username, prompt, likes y date
        prompts_list = [{
            "id": p[0],
            "username": p[1],
            "prompt": p[2],
            "date": p[3],
            "likes": p[4]
        } for p in prompts]

        return jsonify({"feed": prompts_list}), 200
    finally:
        connection.close()

@app.route("/deletePrompts/<int:prompt_id>", methods=["DELETE"])
def delete_prompt(prompt_id):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Verificar si el prompt existe antes de intentar eliminarlo
            sql_check = "SELECT * FROM prompts WHERE id = %s"
            cursor.execute(sql_check, (prompt_id,))
            prompt = cursor.fetchone()

            if not prompt:
                return jsonify({"error": "Prompt not found"}), 404

            # Eliminar los likes asociados al prompt
            sql_delete_likes = "DELETE FROM likes WHERE prompt_id = %s"
            cursor.execute(sql_delete_likes, (prompt_id,))

            # Eliminar el prompt de la base de datos
            sql_delete_prompt = "DELETE FROM prompts WHERE id = %s"
            cursor.execute(sql_delete_prompt, (prompt_id,))

            connection.commit()

        return jsonify({"status": "Prompt and associated likes deleted successfully"}), 200
    finally:
        connection.close()

print("Ejecutando API")  
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)
    print("Termina")
