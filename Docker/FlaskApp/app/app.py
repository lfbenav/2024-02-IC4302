
from flask import Flask, jsonify, request
import pymysql  # MariaDB
import psycopg2  # PostgreSQL
from elasticsearch import Elasticsearch # Elasticsearch
import redis  # Redis
import os
import pylibmc  # Memcached
from prometheus_client import start_http_server, Summary, Counter, Histogram, generate_latest

app = Flask(__name__)

print("Corriendo Flaskapp...")
pipi = os.getenv('variable_test')

#Configuración de mariadb
mariadb_config = {
    'host': os.getenv('maria_host'),
    'user': os.getenv('maria_user'),
    'password': os.getenv('maria_password'),
    'database': os.getenv('maria_database')
}

#Configuración de postgresql
postgresql_config = {
    'host': os.getenv('postgre_host'),
    'user': os.getenv('postgre_user'),
    'password': os.getenv('postgre_password'),
    'dbname': os.getenv('postgre_dbname')
}

#Configuración de elasticsearch
contraseña_elastic = os.getenv('es_pass')
es_host = os.getenv('es_host')
es_port = os.getenv('es_port')
es_usuario = os.getenv('es_usuario')
es_url = f"http://{es_host}:{es_port}"

#Configuración de caches
redis_host = os.getenv('redis_host')
redis_port = os.getenv('redis_port')
memcached_host = os.getenv('memcached_host')
memcached_port = os.getenv('memcached_port')

redis_client = redis.Redis(host=redis_host, port=redis_port)
memcached_client = pylibmc.Client([f"{memcached_host}:{memcached_port}"])

# Métricas de Prometheus
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests (count)', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])
CACHE_HITS = Counter('cache_hits_total', 'Total Cache Hits', ['cache_type'])
CACHE_MISSES = Counter('cache_misses_total', 'Total Cache Misses', ['cache_type'])


# Función para determinar si se usa Redis o Memcached
def get_cache_client(cache_type):
    if cache_type == 'redis':
        return redis_client
    elif cache_type == 'memcached':
         return memcached_client
    else:
        return None

@app.route("/")
def index():
    return "Funciona correctamente!"

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
        cursor.execute("SELECT * FROM movies LIMIT 100;")
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})
    
@app.route("/postgresql", methods=["GET"])
def get_from_postgresql():
    endpoint = "/postgresql"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'mariadb_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        connection = psycopg2.connect(**postgresql_config)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM movies LIMIT 100;")
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "database"})

@app.route("/elasticsearch", methods=["GET"]) 
def get_from_elasticsearch():
    try:
        es = Elasticsearch(es_url, basic_auth=(es_usuario, contraseña_elastic))
        # Prueba de conexión a Elasticsearch
        if es.ping():
            return jsonify({"message": "Conexión exitosa a Elasticsearch"}), 200
        else:
            return jsonify({"error": "No se pudo conectar a Elasticsearch"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT #1 
# Peliculas con un rating promedio mayor a 3.5;

#mariadb
@app.route("/mariadb/movies/rating", methods=["GET"])
def get_from_mariadb_movies_rating():
    endpoint = "/mariadb/movies/rating"
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
        cursor.execute('''
                       SELECT m.movieId, m.title, AVG(r.rating) AS avg_rating
                       FROM movies m
                       INNER JOIN ratings r ON r.movieId = m.movieId
                       GROUP BY m.movieId, m.title
                       HAVING AVG(r.rating) > 3.5
                       ORDER BY m.movieId DESC;
                       ''')
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "mariadb"})

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

        return jsonify({"data": result, "source": "postgresql"})
    

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
        es = Elasticsearch(es_url, basic_auth=(es_usuario, contraseña_elastic))
        query = {
  "size": 0,
  "aggs": {
    "movies": {
      "terms": {
        "field": "movieId",
        "size": 10000,
        "order": {
          "_key": "desc"
        }
      },
      "aggs": {
        "avg_rating": {
          "avg": {
            "field": "rating"
          }
        },
        "filtered_movies": {
          "bucket_selector": {
            "buckets_path": {
              "averageRating": "avg_rating"
            },
            "script": "params.averageRating > 3.5"
          }
        }
      }
    }
  }
}
        result = es.search(index='ratings', body=query)
        result_data = result.body  # Extraer el contenido como diccionario
        result = {"data": result_data, "source": "elasticsearch"}

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify(result)

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

        return jsonify({"data": result, "source": "mariadb"})

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

        return jsonify({"data": result, "source": "postgresql"})


#elasticsearch
@app.route("/elasticsearch/movies/best", methods=["GET"])
def get_from_elasticsearch_movies_best():
    endpoint = "/elasticsearch/movies/best"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'elasticsearch_movies_rating_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        es = Elasticsearch(es_url, basic_auth=(es_usuario, contraseña_elastic))
        query = {
  "size": 0,
  "query": {
    "bool": {
      "must": [
        {
          "exists": {
            "field": "movieId"
          }
        }
      ]
    }
  },
  "aggs": {
    "group_by_movie": {
      "terms": {
        "field": "movieId",
        "size": 10
      },
      "aggs": {
        "avg_rating": {
          "avg": {
            "field": "rating"
          }
        },
        "rating_count": {
          "value_count": {
            "field": "rating"
          }
        },
        "rating_count_filter": {
          "bucket_selector": {
            "buckets_path": {
              "ratingCount": "rating_count"
            },
            "script": "params.ratingCount >= 250"
          }
        },
        "sorted_by_avg_rating": {
          "bucket_sort": {
            "sort": [
              {
                "avg_rating": {
                  "order": "desc"
                }
              }
            ],
            "from": 0,
            "size": 10
          }
        }
      }
    }
  }
}
        result = es.search(index='ratings', body=query)
        result_data = result.body  # Extraer el contenido como diccionario
        result = {"data": result_data, "source": "elasticsearch"}

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify(result)

#ENDPOINT 3
#Tendencia de calificaciones a lo largo del tiempo para la película "Star Wars: Episode IV - A New Hope (1977)"

#mariadb
@app.route("/mariadb/movies/trend", methods=["GET"])
def get_from_mariadb_movies_trend():
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
                        WHERE r.movieId = 260
                        GROUP BY rating_date
                        ORDER BY rating_date;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "mariadb"})

#postgresql
@app.route("/postgresql/movies/trend", methods=["GET"])
def get_from_postgresql_movies_trend():
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
                        WHERE r.movieId = 260
                        GROUP BY rating_date
                        ORDER BY rating_date;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "postgresql"})


#elasticsearch
@app.route("/elasticsearch/movies/trend", methods=["GET"])
def get_from_elasticsearch_movies_trend():
    endpoint = "/elasticsearch/movies/trend"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'elasticsearch_movies_rating_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        es = Elasticsearch(es_url, basic_auth=(es_usuario, contraseña_elastic))
        query = {
  "size": 0,
  "query": {
    "term": {
      "movieId": "260"
    }
  },
  "aggs": {
    "ratings_over_time": {
      "date_histogram": {
        "field": "timestamp",
        "calendar_interval": "day",
        "format": "yyyy-MM-dd"
      },
      "aggs": {
        "avg_rating": {
          "avg": {
            "field": "rating"
          }
        }
      }
    }
  },
  "sort": [
    {
      "timestamp": {
        "order": "asc"
      }
    }
  ]
}
        result = es.search(index='ratings', body=query)
        result_data = result.body  # Extraer el contenido como diccionario
        result = {"data": result_data, "source": "elasticsearch"}

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify(result)


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

        return jsonify({"data": result, "source": "mariadb"})

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
                        HAVING MAX(r.rating) - MIN(r.rating) > 3;
                        """)
        result = cursor.fetchall()
        connection.close()

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify({"data": result, "source": "postgresql"})


#elasticsearch
@app.route("/elasticsearch/movies/inconsistent", methods=["GET"])
def get_from_elasticsearch_movies_inconsistent():
    endpoint = "/elasticsearch/movies/inconsistent"
    REQUEST_COUNT.labels(method='GET', endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(method='GET', endpoint=endpoint).time():
        cache_type = request.args.get('cache')
        cache_key = 'elasticsearch_movies_rating_key'
        cache_client = get_cache_client(cache_type)

        if cache_client and cache_client.get(cache_key):
            CACHE_HITS.labels(cache_type=cache_type).inc()
            return jsonify({"data": cache_client.get(cache_key).decode('utf-8'), "source": "cache"})

        CACHE_MISSES.labels(cache_type=cache_type).inc()
        es = Elasticsearch(es_url, basic_auth=(es_usuario, contraseña_elastic))
        query = {
  "size": 0,
  "query": {
    "bool": {
      "must": [
        {
          "exists": {
            "field": "movieId"
          }
        }
      ]
    }
  },
  "aggs": {
    "group_by_movie": {
      "terms": {
        "field": "movieId",
        "size": 9000
      },
      "aggs": {
        "max_rating": {
          "max": {
            "field": "rating"
          }
        },
        "min_rating": {
          "min": {
            "field": "rating"
          }
        },
        "rating_variance": {
          "bucket_script": {
            "buckets_path": {
              "maxRating": "max_rating",
              "minRating": "min_rating"
            },
            "script": "params.maxRating - params.minRating"
          }
        },
        "rating_variance_filter": {
          "bucket_selector": {
            "buckets_path": {
              "ratingVariance": "rating_variance"
            },
            "script": "params.ratingVariance > 3"
          }
        }
      }
    }
  }
}
        result = es.search(index='ratings', body=query)
        result_data = result.body  # Extraer el contenido como diccionario
        result = {"data": result_data, "source": "elasticsearch"}

        if cache_client:
            cache_client.set(cache_key, str(result))

        return jsonify(result)

print("Ejecutando API")  
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    print("Termina")

# LISTA CON TODAS LAS URL DE MARIADB
# /mariadb/movies/rating
# /mariadb/movies/best
# /mariadb/movies/trend
# /mariadb/movies/inconsistent

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