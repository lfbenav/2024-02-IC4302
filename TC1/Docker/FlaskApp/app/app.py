
from flask import Flask, jsonify, request
import pymysql  # MariaDB
import psycopg2  # PostgreSQL
from elasticsearch import Elasticsearch  # Elasticsearch
import redis  # Redis
import os
# import pylibmc  # Memcached
from prometheus_client import start_http_server, Summary, Counter, Histogram, generate_latest

app = Flask(__name__)

# Configuración de bases de datos
mariadb_config = {
    'host': os.getenv('MARIADB'),
    'user': 'root',
    'password': os.getenv('MARIADB_PASS'),
    'database': os.getenv('MARIADB_DB')
}

'''
postgresql_config = {
    'host': 'postgresql_host',
    'user': 'postgresql_user',
    'password': 'postgresql_password',
    'database': 'postgresql_db'
}
'''
# es = Elasticsearch(['elasticsearch_host'])

# Configuración de caché
redis_client = redis.Redis(host='redis_host', port=6379, db=0)
# memcached_client = pylibmc.Client(['memcached_host'], binary=True)

# Métricas de Prometheus
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests (count)', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])
CACHE_HITS = Counter('cache_hits_total', 'Total Cache Hits', ['cache_type'])
CACHE_MISSES = Counter('cache_misses_total', 'Total Cache Misses', ['cache_type'])


# Función para determinar si se usa Redis o Memcached
def get_cache_client(cache_type):
    if cache_type == 'redis':
        return redis_client
    # elif cache_type == 'memcached':
    #     return memcached_client
    else:
        return None

@app.route("/metrics")
def metrics():
    return generate_latest(), 200

@app.route("/mariadb", methods=["GET"])
def get_from_mariadb():
    endpoint = "/mariadb"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'mariadb_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = pymysql.connect(**mariadb_config)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM movies LIMIT 10;")
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})



# ENDPOINT #1 
# Peliculas con un rating promedio mayor a 3.5;

#mariadb
@app.route("/mariadb/movies/rating", methods=["GET"])
def get_from_mariadb_movies_rating():
    endpoint = "/mariadb/movies/rating"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'mariadb_movies_rating_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = pymysql.connect(**mariadb_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT m.movieId, m.title, AVG(r.rating) AS avg_rating
                        FROM movies m
                        INNER JOIN ratings r ON r.movieId = m.movieId
                        GROUP BY m.movieId, m.title
                        HAVING AVG(r.rating) > 3.5
                        ORDER BY m.movieId DESC;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})
''' 
#postgresql
@app.route("/postgresql/movies/rating", methods=["GET"])
def get_from_postgresql_movies_rating():
    endpoint = "/postgresql/movies/rating"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'postgresql_movies_rating_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = psycopg2.connect(**postgresql_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT m.movieId, m.title, AVG(r.rating) AS avg_rating
                        FROM movies m
                        INNER JOIN ratings r ON r.movieId = m.movieId
                        GROUP BY m.movieId, m.title
                        HAVING AVG(r.rating) > 3.5
                        ORDER BY m.movieId DESC;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})
    
#elasticsearch
@app.route("/elasticsearch/movies/rating", methods=["GET"])
def get_from_elasticsearch_movies_rating():
    endpoint = "/elasticsearch/movies/rating"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'elasticsearch_movies_rating_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        # result = es.search(index='movies', body={"query": {"range": {"rating": {"gt": 3.5}}}})
        result = {"data": "result", "source": "elasticsearch"}

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify(result)
'''
#ENDPOINT 2
#Películas mejor valoradas con más de 250 calificaciones

#mariadb
@app.route("/mariadb/movies/best", methods=["GET"])
def get_from_mariadb_movies_best():
    endpoint = "/mariadb/movies/best"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'mariadb_movies_best_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = pymysql.connect(**mariadb_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT m.movieId, m.title, AVG(r.rating) AS avg_rating, COUNT(r.rating) AS rating_count
                        FROM movies m
                        INNER JOIN ratings r ON m.movieId = r.movieId
                        GROUP BY m.movieId, m.title
                        HAVING COUNT(r.rating) >= 250
                        ORDER BY avg_rating DESC;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})
'''  
#postgresql
@app.route("/postgresql/movies/best", methods=["GET"])
def get_from_postgresql_movies_best():
    endpoint = "/postgresql/movies/best"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'postgresql_movies_best_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = psycopg2.connect(**postgresql_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT m.movieId, m.title, AVG(r.rating) AS avg_rating, COUNT(r.rating) AS rating_count
                        FROM movies m
                        INNER JOIN ratings r ON m.movieId = r.movieId
                        GROUP BY m.movieId, m.title
                        HAVING COUNT(r.rating) >= 250
                        ORDER BY avg_rating DESC;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})
    
#elasticsearch
@app.route("/elasticsearch/movies/best", methods=["GET"])
def get_from_elasticsearch_movies_best():
    endpoint = "/elasticsearch/movies/best"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'elasticsearch_movies_best_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        # result = es.search(index='movies', body={"query": {"range": {"rating": {"gt": 3.5}}}})
        result = {"data": "result", "source": "elasticsearch"}

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify(result)
'''
#ENDPOINT 3
#Tendencia de calificaciones a lo largo del tiempo para una película

#mariadb
@app.route("/mariadb/movies/trend/<int:movie_id>", methods=["GET"])
def get_from_mariadb_movies_trend(movie_id):
    endpoint = "/mariadb/movies/trend"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'mariadb_movies_trend_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = pymysql.connect(**mariadb_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT DATE(FROM_UNIXTIME(r.timestamp)) AS rating_date, AVG(r.rating) AS avg_rating
                        FROM ratings r
                        WHERE r.movieId = %s
                        GROUP BY rating_date
                        ORDER BY rating_date;
                        """, (movie_id,))
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})
'''
#postgresql
@app.route("/postgresql/movies/trend/<int:movie_id>", methods=["GET"])
def get_from_postgresql_movies_trend(movie_id):
    endpoint = "/postgresql/movies/trend"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'postgresql_movies_trend_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = psycopg2.connect(**postgresql_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT DATE(TO_TIMESTAMP(r.timestamp)) AS rating_date, AVG(r.rating) AS avg_rating
                        FROM ratings r
                        WHERE r.movieId = %s
                        GROUP BY rating_date
                        ORDER BY rating_date;
                        """, (movie_id,))
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})
    
#elasticsearch
@app.route("/elasticsearch/movies/trend/<int:movie_id>", methods=["GET"])
def get_from_elasticsearch_movies_trend(movie_id):
    endpoint = "/elasticsearch/movies/trend"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'elasticsearch_movies_trend_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        # result = es.search(index='ratings', body={"query": {"term": {"movieId": movie_id}}})
        result = {"data": "result", "source": "elasticsearch"}

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify(result)
'''
#ENDPOINT 4
#Películas con calificaciones inconsistentes (calificaciones que varían demasiado entre usuarios)

#mariadb
@app.route("/mariadb/movies/inconsistent", methods=["GET"])
def get_from_mariadb_movies_inconsistent():
    endpoint = "/mariadb/movies/inconsistent"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'mariadb_movies_inconsistent_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = pymysql.connect(**mariadb_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT m.movieId, m.title, MAX(r.rating) - MIN(r.rating) AS rating_variance
                        FROM movies m
                        INNER JOIN ratings r ON m.movieId = r.movieId
                        GROUP BY m.movieId, m.title
                        HAVING rating_variance > 3;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})
'''
#postgresql
@app.route("/postgresql/movies/inconsistent", methods=["GET"])
def get_from_postgresql_movies_inconsistent():
    endpoint = "/postgresql/movies/inconsistent"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'postgresql_movies_inconsistent_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = psycopg2.connect(**postgresql_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT m.movieId, m.title, MAX(r.rating) - MIN(r.rating) AS rating_variance
                        FROM movies m
                        INNER JOIN ratings r ON m.movieId = r.movieId
                        GROUP BY m.movieId, m.title
                        HAVING rating_variance > 3;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})

#elasticsearch
@app.route("/elasticsearch/movies/inconsistent", methods=["GET"])
def get_from_elasticsearch_movies_inconsistent():
    endpoint = "/elasticsearch/movies/inconsistent"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'elasticsearch_movies_inconsistent_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        # result = es.search(index='movies', body={"query": {"range": {"rating_variance": {"gt": 3}}})
        result = {"data": "result", "source": "elasticsearch"}

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify(result)
'''
#ENDPOINT 5
#Películas que tienen más calificaciones que la mediana de todas las películas

#mariadb
@app.route("/mariadb/movies/median_ratings", methods=["GET"])
def get_movies_median_ratings():
    endpoint = "/mariadb/movies/median_ratings"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'movies_median_ratings_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = pymysql.connect(**mariadb_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT m.movieId, m.title, COUNT(r.rating) AS rating_count
                        FROM movies m
                        INNER JOIN ratings r ON m.movieId = r.movieId
                        GROUP BY m.movieId, m.title
                        HAVING rating_count > (
                            SELECT rating_count
                            FROM (
                                SELECT r.movieId, COUNT(r.rating) AS rating_count,
                                    ROW_NUMBER() OVER (ORDER BY COUNT(r.rating)) AS row_num,
                                    COUNT(*) OVER () AS total_rows
                                FROM ratings r
                                GROUP BY r.movieId
                            ) AS movie_ratings
                            WHERE row_num = FLOOR((total_rows + 1) / 2)
                        )
                        ORDER BY rating_count DESC;
                        ;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})
'''
#postgresql
@app.route("/postgresql/movies/median_ratings", methods=["GET"])
def get_movies_median_ratings_postgresql():
    endpoint = "/postgresql/movies/median_ratings"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'movies_median_ratings_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = psycopg2.connect(**postgresql_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT m.movieId, m.title, COUNT(r.rating) AS rating_count
                        FROM movies m
                        INNER JOIN ratings r ON m.movieId = r.movieId
                        GROUP BY m.movieId, m.title
                        HAVING rating_count > (
                            SELECT rating_count
                            FROM (
                                SELECT r.movieId, COUNT(r.rating) AS rating_count,
                                    ROW_NUMBER() OVER (ORDER BY COUNT(r.rating)) AS row_num,
                                    COUNT(*) OVER () AS total_rows
                                FROM ratings r
                                GROUP BY r.movieId
                            ) AS movie_ratings
                            WHERE row_num = FLOOR((total_rows + 1) / 2)
                        )
                        ORDER BY rating_count DESC;
                        ;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})
    
#elasticsearch
@app.route("/elasticsearch/movies/median_ratings", methods=["GET"])
def get_movies_median_ratings_elasticsearch():
    endpoint = "/elasticsearch/movies/median_ratings"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'movies_median_ratings_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        # result = es.search(index='movies', body={"query": {"range": {"rating_count": {"gt": 500}}})
        result = {"data": "result", "source": "elasticsearch"}

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify(result)
'''
    
#ENDPOINT 6
#Películas que tienen más de 100 calificaciones y muestran mayor variabilidad en las opiniones de los usuarios.


#mariadb
@app.route("/mariadb/movies/variability", methods=["GET"])
def get_from_mariadb_movies_variability():
    endpoint = "/mariadb/movies/variability"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'mariadb_movies_variability_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = pymysql.connect(**mariadb_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT m.movieId, m.title, 
                            SQRT(SUM(pow(r.rating - sub.avg_rating, 2)) / COUNT(r.rating)) AS stddev_rating
                        FROM movies m
                        INNER JOIN ratings r ON m.movieId = r.movieId
                        INNER JOIN (
                            SELECT movieId, AVG(rating) AS avg_rating
                            FROM ratings
                            GROUP BY movieId
                        ) sub ON m.movieId = sub.movieId
                        GROUP BY m.movieId, m.title
                        HAVING COUNT(r.rating) > 100
                        ORDER BY stddev_rating DESC;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})

'''
#postgresql
@app.route("/postgresql/movies/variability", methods=["GET"])
def get_from_postgresql_movies_variability():
    endpoint = "/postgresql/movies/variability"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'postgresql_movies_variability_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = psycopg2.connect(**postgresql_config)
        cursor = connection.cursor()
        cursor.execute("""
                        SELECT m.movieId, m.title, 
                            SQRT(SUM(pow(r.rating - sub.avg_rating, 2)) / COUNT(r.rating)) AS stddev_rating
                        FROM movies m
                        INNER JOIN ratings r ON m.movieId = r.movieId
                        INNER JOIN (
                            SELECT movieId, AVG(rating) AS avg_rating
                            FROM ratings
                            GROUP BY movieId
                        ) sub ON m.movieId = sub.movieId
                        GROUP BY m.movieId, m.title
                        HAVING COUNT(r.rating) > 100
                        ORDER BY stddev_rating DESC;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})
    
#elasticsearch
@app.route("/elasticsearch/movies/variability", methods=["GET"])
def get_from_elasticsearch_movies_variability():
    endpoint = "/elasticsearch/movies/variability"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'elasticsearch_movies_variability_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        # result = es.search(index='movies', body={"query": {"range": {"stddev_rating": {"gt": 3}}})
        result = {"data": "result", "source": "elasticsearch"}

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify(result)
'''
        
if __name__ == "__main__":
    print("Clitoris")
    #start_http_server(8000)  # Inicia el servidor de Prometheus en el puerto 8000
    app.run(host="0.0.0.0", port=5000)
    print("Iniciado")

#lISTA CON TODAS LAS URL DE MARIADB
#http://localhost:5000/mariadb/movies/rating
#http://localhost:5000/mariadb/movies/best
#http://localhost:5000/mariadb/movies/trend/1
#http://localhost:5000/mariadb/movies/inconsistent
#http://localhost:5000/mariadb/movies/median_ratings
#http://localhost:5000/mariadb/movies/variability

"""
Explicación del Código:

Configuración de Bases de Datos:
mariadb_config y postgresql_config contienen la configuración para conectarse a MariaDB y PostgreSQL, respectivamente.
es se utiliza para conectarse a Elasticsearch.

Caché:
Puedes seleccionar entre Redis y Memcached pasando el parámetro cache=redis o cache=memcached en la URL.
Los resultados de las consultas se almacenan en caché si se especifica el uso de caché.

Endpoints:
/mariadb: Consulta en MariaDB.
/postgresql: Consulta en PostgreSQL.
/elasticsearch: Consulta en Elasticsearch.

Funcionamiento:
El código primero verifica si la consulta ya está en caché. Si no está, realiza la consulta en la base de datos correspondiente y luego guarda el resultado en la caché si está configurado para hacerlo.

Ejemplo de uso:
Sin caché: GET http://localhost:5000/mariadb
Con caché Redis: GET http://localhost:5000/mariadb?cache=redis
Con caché Memcached: GET http://localhost:5000/mariadb?cache=memcached
Este código te proporciona una base sólida para interactuar con varias bases de datos y utilizar mecanismos de caché. Asegúrate de ajustar las configuraciones y detalles específicos según tu entorno y necesidades.
"""