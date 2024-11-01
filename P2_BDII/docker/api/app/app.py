import os
from pymongo import MongoClient
from elasticsearch import Elasticsearch
import pg8000
from flask import Flask, jsonify, request
from flask_cors import CORS
from sentence_transformers import SentenceTransformer


POSTGRE_HOST = os.getenv('postgre_host')
POSTGRE_USER = os.getenv('postgre_user')
POSTGRE_PASSWORD = os.getenv('postgre_password')
POSTGRE_DBNAME = os.getenv('postgre_dbname')
POSTGRE_PORT = os.getenv('postgre_port')

MONGO_CLIENT = os.getenv('mongo_client')

ELASTIC_PASSWORD = os.getenv("ELASTIC_PASS")
ELASTIC_USER = os.getenv("ELASTIC_USER")
ELASTIC_SERVICE = os.getenv("ELASTIC")
ELASTIC_PORT = os.getenv("ELASTIC_PORT")
es_url = f"http://{ELASTIC_SERVICE}:{ELASTIC_PORT}"


# Cargar el modelo de embeddings
embedding_model = SentenceTransformer('all-mpnet-base-v2')


# Conexión a PostgreSQL
def get_postgres_connection():
    return pg8000.connect(
            user=POSTGRE_USER,
            password=POSTGRE_PASSWORD,
            host=POSTGRE_HOST,
            port=POSTGRE_PORT,
            database=POSTGRE_DBNAME
        )

# Conexión a MongoDB
mongo_client = MongoClient(
            MONGO_CLIENT,
            tls=True,
            tlsAllowInvalidCertificates=True
        )
mongo_db = mongo_client['LyricsDB']
lyrics_collection = mongo_db['LyricsCollection']

# Conexión a Elasticsearch
es = Elasticsearch(es_url, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))


# Flask
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# Función para generar un embedding
def encode(text):
    if text == "":
        return None

    embedding = embedding_model.encode(text)
    response = {
        "embeddings": embedding.tolist(),
        "text": text
    }
    return response



'''                   '''
'''     Endpoints     '''
'''                   '''



# Ruta para validar funcionamiento
@app.route("/")
def index():
    return "Funciona correctamente!"



# Endpoint para búsqueda general en MongoDB o PostgreSQL
@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query")
    database = data.get("database")

    if database == "mongo":
        # Realizar búsqueda en MongoDB usando el pipeline de búsqueda
        search_pipeline = [
            {
                "$search": {
                    "index": "default",  # Nombre del índice de búsqueda
                    "text": {
                        "query": query,
                        "path": ["artist", "genres", "songs.song_name", "songs.lyric", "songs.language", "popularity"]  # Solo buscar en estos campos
                    }
                }
            },
            {
                "$project": {
                    "artist": 1,
                    "genres": 1,
                    "popularity": 1,
                    "link": 1,  # Incluir el enlace del artista
                    "score": {"$meta": "searchScore"},  # Relevancia de la búsqueda
                    "matching_songs": {
                        "$filter": {
                            "input": "$songs",
                            "as": "song",
                            "cond": {
                                "$or": [
                                    {"$regexMatch": {"input": "$$song.song_name", "regex": query, "options": "i"}},
                                    {"$regexMatch": {"input": "$$song.lyric", "regex": query, "options": "i"}}
                                ]
                            }
                        }
                    }
                }
            },
            {
                "$match": {
                    "matching_songs": {"$ne": []}  # Filtrar documentos sin canciones coincidentes
                }
            }
        ]

        results = list(lyrics_collection.aggregate(search_pipeline))

        # Procesar los resultados
        processed_results = []
        for doc in results:
            artist = doc['artist']
            genres = doc['genres']
            popularity = doc['popularity']
            artist_link = doc['link']  # Link del artista
            score = doc['score']
            for song in doc['matching_songs']:
                processed_results.append({
                    "artist": artist,
                    "genres": genres,
                    "song_name": song['song_name'],
                    "lyric": song['lyric'],
                    "language": song.get('language', "Unknown Language"),
                    "popularity": popularity,
                    "artist_link": artist_link,  # Añadir link del artista
                    "song_link": song['song_link'],  # Añadir link de la canción
                    "score": score  # Relevancia de la búsqueda
                })

        results = processed_results

    elif database == "postgres":
        # Realizar búsqueda en PostgreSQL
        connection = get_postgres_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT a.artist_name, a.genres, a.popularity, a.link AS artist_link, s.song_name, s.song_link, s.lyric, s.language, 
                ts_rank(to_tsvector(s.lyric), plainto_tsquery(%s)) AS rank 
            FROM Songs s 
            JOIN Artists a ON s.artist_id = a.artist_id 
            WHERE a.artist_name ILIKE %s OR s.lyric ILIKE %s 
            ORDER BY rank DESC 
        """, (query, f'%{query}%', f'%{query}%'))
        
        # Procesar los resultados para que coincidan con el formato de MongoDB
        results = []
        for row in cursor.fetchall():
            results.append({
                "artist": row[0],
                "genres": row[1],
                "song_name": row[4],
                "lyric": row[6],
                "language": row[7],
                "popularity": row[2],
                "artist_link": row[3],
                "song_link": row[5],
                "score": row[8]
            })

        cursor.close()
        connection.close()

    else:
        return jsonify({"error": "Especifique una base de datos válida"}), 400

    return jsonify(results)



# Endpoint para convertir texto en embeddings y buscar apartamentos similares en Elasticsearch
@app.route("/apartment/search", methods=["POST"])
def apartment_search():
    data = request.get_json()
    selected_text = data.get("selected_text")
    if not selected_text:
        return jsonify({"error": "El campo 'selected_text' es requerido"}), 400

    embeddings = embedding_model.encode(selected_text).tolist()

    query = {
        "knn": {
            "field": "embedding",
            "query_vector": embeddings,
            "k": 10,
            "num_candidates": 50
        }
    }

    response = es.search(index="listings_and_reviews", body=query)

    results = []
    for hit in response['hits']['hits']:
        name = hit['_source'].get('name', 'Unknown Apartment')
        summary = hit['_source'].get('summary', 'No summary available')
        description = hit['_source'].get('description', 'No description available')
        reviews = hit['_source'].get('reviews', [])

        # Procesar los comentarios en 'reviews'
        reviews_list = [review.get("comments", "") for review in reviews]

        # Agregar el resultado a la lista
        results.append({
            "name": name,
            "summary": summary,
            "description": description,
            "reviews": reviews_list
        })

    return jsonify(results)



# Endpoint para obtener todos los géneros y lenguajes distintos
@app.route("/distinct", methods=["GET"])
def distinct_fields():
    # Obtener todos los géneros únicos
    genres_result_temp = lyrics_collection.distinct("genres")

    generos_unicos = set()

    # Separar los géneros y agregarlos al conjunto
    for genero in genres_result_temp:
        generos_separados = genero.split('; ')
        for g in generos_separados:
            generos_unicos.add(g.strip())  # Usar strip() para eliminar espacios en blanco

    # Convertir el conjunto de vuelta a una lista (opcional)
    genres_result = list(generos_unicos)

    # Obtener todos los lenguajes únicos
    languages_result_temp = lyrics_collection.distinct("songs.language")

    languages_result = []
    for lang in languages_result_temp:
        if(len(lang)==2):
            languages_result.append(lang)

    # Estructurar el resultado
    result = {
        "distinct_genres": genres_result,
        "distinct_languages": languages_result
    }

    return jsonify(result)



print("Ejecutando API...")
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)
    print("Terminando API...")