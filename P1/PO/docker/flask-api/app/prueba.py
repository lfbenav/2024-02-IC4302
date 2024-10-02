from elasticsearch import Elasticsearch
import numpy as np
from sentence_transformers import SentenceTransformer
import time
print("iniciando")
# Conectar a Elasticsearch
es_pass = "nOIp3b91I4i13P781lBUDSo1"
es_user = "elastic"
es_host = "localhost"
#esurl
es_url = "http://localhost:51892"
es = Elasticsearch(es_url, basic_auth=(es_user, es_pass))
print("elastic listo")
# Cargar el modelo
model = SentenceTransformer('all-mpnet-base-v2')


# Generar un embedding de ejemplo (esto debería ser tu vector de búsqueda)
# Por ejemplo, esto podría venir de un modelo de lenguaje preentrenado como BERT o similar
query_embedding = model.encode("Canciones cristianas")
print(len(query_embedding))
query_embedding = query_embedding / np.linalg.norm(query_embedding)
# print(query_embedding)
# Vector de ejemplo de 768 dimensiones

# Definir el índice en el que se hará la búsqueda
index_name = 'songs'

# Definir la consulta de búsqueda
query = {
    "query": {
        "script_score": {
            "query": {
                "match_all": {}
            },
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                "params": {
                    "query_vector": query_embedding.tolist()
                }
            }
        }
    }
}

# mostrar solo 5 resultados
query["size"] = 5


"""
KNN
# Definir la consulta KNN
query = {
    "knn": {
        "field": "embedding",               # Campo donde están los embeddings
        "query_vector": query_embedding.tolist(),  # El vector de la consulta
        "k": 10,                            # Número de vecinos más cercanos que se quieren recuperar
        "num_candidates": 50                # Número de candidatos que se procesarán antes de elegir los más cercanos
    }
}

# Mostrar solo 5 resultados
query["size"] = 5

# Ejecutar la búsqueda
response = es.search(index=index_name, body=query)

# Imprimir los resultados
for hit in response['hits']['hits']:
    song_name = hit['_source'].get('name', 'Unknown Song')
    lyrics = hit['_source'].get('lyrics', 'No lyrics available')
    
    # Mostrar en un formato más bonito
    print(f"ID: {hit['_id']}, Puntaje: {hit['_score']}")
    print(f"\n{'='*50}")
    print(f"Canción: {song_name}")
    print(f"Letras:\n{lyrics}")
    print(f"{'='*50}\n")

"""


"""
HNSW

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
                "similarity": "cosine",
                "method": {
                    "name": "hnsw", 
                    "space_type": "cosinesimil", 
                    "engine": "nmslib", 
                    "ef_construction": 100,  # Mejora la precisión de la búsqueda
                    "m": 16  # Ajusta el número de vecinos que se conectan
                }
            }
        }
    }
}

# Crear el índice
if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, body=index_body)
    print(f"Índice {index_name} creado exitosamente con HNSW.")
else:
    print(f"El índice {index_name} ya existe.")

    
    # Generar un embedding de ejemplo para la búsqueda
query_embedding = model.encode("Songs to play to my 6 years old daughter").tolist()

# Definir la consulta KNN
query = {
    "knn": {
        "field": "embedding",         # El campo del vector
        "query_vector": query_embedding,  # El embedding de la consulta
        "k": 5,                      # Número de resultados (vecinos) a devolver
        "num_candidates": 100         # Número de candidatos considerados en la búsqueda
    }
}

# Ejecutar la búsqueda
response = es.search(index=index_name, body=query)

# Imprimir los resultados
for hit in response['hits']['hits']:
    song_name = hit['_source'].get('name', 'Unknown Song')
    lyrics = hit['_source'].get('lyrics', 'No lyrics available')
    
    # Mostrar en un formato más bonito
    print(f"ID: {hit['_id']}, Puntaje: {hit['_score']}")
    print(f"\n{'='*50}")
    print(f"Canción: {song_name}")
    print(f"Letras:\n{lyrics}")
    print(f"{'='*50}\n")



"""


# # Ejecutar la búsqueda
# response = es.search(index=index_name, body=query)

# # Imprimir los resultados
# for hit in response['hits']['hits']:
#     song_name = hit['_source'].get('name', 'Unknown Song')
#     lyrics = hit['_source'].get('lyrics', 'No lyrics available')
    
#     # Mostrar en un formato más bonito
#     print(f"ID: {hit['_id']}, Puntaje: {hit['_score']}")
#     print(f"\n{'='*50}")
#     print(f"Canción: {song_name}")
#     print(f"Letras:\n{lyrics}")
#     print(f"{'='*50}\n")

    # Definir la consulta de búsqueda con similitud de coseno
query_cosine = {
    "query": {
        "script_score": {
            "query": {
                "match_all": {}
            },
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                "params": {
                    "query_vector": query_embedding.tolist()
                }
            }
        }
    }
}

# Mostrar solo 5 resultados
# query_cosine["size"] = 5

# Medir el tiempo de ejecución para la consulta con similitud de coseno
start_time = time.time()
response_cosine = es.search(index=index_name, body=query_cosine)
end_time = time.time()


# Tiempo de ejecución
elapsed_time_cosine = end_time - start_time
print(f"Tiempo de ejecución (Cosine Similarity): {elapsed_time_cosine:.4f} segundos")


# Definir la consulta KNN
query_knn = {
    "knn": {
        "field": "embedding",               # Campo donde están los embeddings
        "query_vector": query_embedding.tolist(),  # El vector de la consulta
        "k": 5,                            # Número de vecinos más cercanos
        "num_candidates": 50                # Número de candidatos que se procesarán antes de elegir los más cercanos
    }
}

# Mostrar solo 5 resultados
# query_knn["size"] = 5

# Medir el tiempo de ejecución para la consulta KNN
start_time = time.time()
response_knn = es.search(index=index_name, body=query_knn)
end_time = time.time()

# Tiempo de ejecución
elapsed_time_knn = end_time - start_time
print(f"Tiempo de ejecución (KNN): {elapsed_time_knn:.4f} segundos")

print("RESPUESTAS DE LOS ALGORITMOS")

# Imprimir los resultados de la búsqueda con similitud de coseno
print("\nResultados de la búsqueda con similitud de coseno:")
for hit in response_knn['hits']['hits']:
    song_name = hit['_source'].get('name', 'Unknown Song')
    artists = hit['_source'].get('artists', 'Unknown Artist')
    lyrics = hit['_source'].get('lyrics', 'No lyrics available')
    
    # Mostrar en un formato más bonito
    print(f"ID: {hit['_id']}, Puntaje: {hit['_score']}")
    print(f"\n{'='*50}")
    print(f"Canción: {song_name}")
    print(f"Autor:\n{artists}")
    print(f"Letras:\n{lyrics}")
    print(f"{'='*50}\n")

# Imprimir los resultados de la búsqueda KNN
print("\nResultados de la búsqueda KNN:")
for hit in response_knn['hits']['hits']:
    song_name = hit['_source'].get('name', 'Unknown Song')
    artists = hit['_source'].get('artists', 'Unknown Artist')
    lyrics = hit['_source'].get('lyrics', 'No lyrics available')
    
    # Mostrar en un formato más bonito
    print(f"ID: {hit['_id']}, Puntaje: {hit['_score']}")
    print(f"\n{'='*50}")
    print(f"Canción: {song_name}")
    print(f"Autor:\n{artists}")
    print(f"Letras:\n{lyrics}")
    print(f"{'='*50}\n")