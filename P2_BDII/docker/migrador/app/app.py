import os
from pymongo import MongoClient
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from bson.decimal128 import Decimal128

MONGO_CLIENT = os.getenv('mongo_client')

ELASTIC_PASSWORD = os.getenv("ELASTIC_PASS")
ELASTIC_USER = os.getenv("ELASTIC_USER")
ELASTIC_SERVICE = os.getenv("ELASTIC")
ELASTIC_PORT = os.getenv("ELASTIC_PORT")
es_url = f"http://{ELASTIC_SERVICE}:{ELASTIC_PORT}"

# Función para convertir Decimal128 a float en los documentos
def convert_decimal128_to_float(document):
    for key, value in document.items():
        if isinstance(value, Decimal128):
            document[key] = float(value.to_decimal())  # Convertir Decimal128 a float
        elif isinstance(value, dict):
            # Si el valor es un diccionario, aplicar recursivamente
            convert_decimal128_to_float(value)
        elif isinstance(value, list):
            # Si es una lista, procesar cada elemento
            for item in value:
                if isinstance(item, dict):
                    convert_decimal128_to_float(item)
    return document

# 1. Conectar a MongoDB y leer los documentos de sample_airbnb.listingsAndReviews
def read_documents_from_mongodb():
    print(f"Conectando a MongoDB con la cadena de conexión: {MONGO_CLIENT}")
    client = MongoClient(MONGO_CLIENT)
    db = client['sample_airbnb']
    collection = db['listingsAndReviews']
    
    # Leer todos los documentos de la colección
    documents = list(collection.find({}))
    print(f"Se han leído {len(documents)} documentos desde MongoDB")
    return documents

# 2. Calcular el embedding de un solo documento usando SentenceTransformer
def calculate_embedding_for_document(doc, embedding_model):
    text_to_embed = f"{doc.get('name', '')} {doc.get('summary', '')} {doc.get('description', '')}"

    # Concatenar comentarios de reviews si existen
    reviews = doc.get('reviews', [])
    comments = " ".join([review.get('comments', '') for review in reviews])
    text_to_embed += f" {comments}"

    # Calcular embedding usando el modelo de SentenceTransformer
    embedding = embedding_model.encode(text_to_embed)
    
    # Guardar el embedding en el documento
    doc['embedding'] = embedding.tolist()  # Convertir a lista para JSON
    print(f"Embedding calculado para el documento {doc.get('_id')}")

    return doc

# 3. Almacenar un solo documento en Elasticsearch
def store_document_in_elasticsearch(doc, es):
    # Extraer el campo _id y eliminarlo del documento
    document_id = str(doc.pop('_id'))

    # Convertir Decimal128 a float en el documento antes de almacenarlo
    doc = convert_decimal128_to_float(doc)

    # Filtrar el documento para conservar solo los campos necesarios
    filtered_doc = {
        "name": doc.get("name"),
        "summary": doc.get("summary"),
        "description": doc.get("description"),
        "reviews": [{"comments": review.get("comments")} for review in doc.get("reviews", [])],
        "embedding": doc.get("embedding")
    }

    # Verificar si el documento ya existe en Elasticsearch
    if es.exists(index="listings_and_reviews", id=document_id):
        print(f"Documento {document_id} ya existe en Elasticsearch, omitiendo inserción.")
    else:
        # Insertar el documento si no existe
        es.index(index="listings_and_reviews", id=document_id, body=filtered_doc)
        print(f"Documento {document_id} almacenado en Elasticsearch")

# 4. Crear el índice en Elasticsearch con el mapeo adecuado
def create_elasticsearch_index(es):
    mapping = {
        "mappings": {
            "properties": {
                "name": {
                    "type": "text"
                },
                "summary": {
                    "type": "text"
                },
                "description": {
                    "type": "text"
                },
                "reviews": {
                    "type": "nested",
                    "properties": {
                        "comments": {
                            "type": "text"
                        }
                    }
                },
                "embedding": {
                    "type": "dense_vector", 
                    "dims": 768, 
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }

    # Verificar si el índice ya existe, y crearlo si no
    if not es.indices.exists(index="listings_and_reviews"):
        es.indices.create(index="listings_and_reviews", body=mapping)
        print("Índice 'listings_and_reviews' creado en Elasticsearch")
    else:
        print("Índice 'listings_and_reviews' ya existe en Elasticsearch, no se crea uno nuevo.")



# Función principal
def run_migrador():
    # Leer documentos de MongoDB
    documents = read_documents_from_mongodb()

    # Inicializar el modelo de embeddings
    embedding_model = SentenceTransformer('all-mpnet-base-v2')

    # Conectar a Elasticsearch
    es = Elasticsearch(es_url, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
    print(f"Conectado a Elasticsearch en la URL: {es_url}")

    # Crear el índice con el mapeo adecuado
    create_elasticsearch_index(es)

    # Procesar cada documento individualmente
    for doc in documents:
        # Calcular embedding para el documento
        doc_with_embedding = calculate_embedding_for_document(doc, embedding_model)

        # Almacenar el documento en Elasticsearch
        store_document_in_elasticsearch(doc_with_embedding, es)

        print("\n")

# Ejecutar el migrador
if __name__ == "__main__":
    print("Ejecutando...")
    run_migrador()
    print("\nProceso Finalizado")















# import os
# from pymongo import MongoClient
# from elasticsearch import Elasticsearch
# from sentence_transformers import SentenceTransformer
# from bson.decimal128 import Decimal128

# MONGO_CLIENT = os.getenv('mongo_client')

# ELASTIC_PASSWORD = os.getenv("ELASTIC_PASS")
# ELASTIC_USER = os.getenv("ELASTIC_USER")
# ELASTIC_SERVICE = os.getenv("ELASTIC")
# ELASTIC_PORT = os.getenv("ELASTIC_PORT")
# es_url = f"http://{ELASTIC_SERVICE}:{ELASTIC_PORT}"


# # Función para convertir Decimal128 a float en los documentos
# def convert_decimal128_to_float(document):
#     for key, value in document.items():
#         if isinstance(value, Decimal128):
#             document[key] = float(value.to_decimal())  # Convertir Decimal128 a float
#         elif isinstance(value, dict):
#             # Si el valor es un diccionario, aplicar recursivamente
#             convert_decimal128_to_float(value)
#         elif isinstance(value, list):
#             # Si es una lista, procesar cada elemento
#             for item in value:
#                 if isinstance(item, dict):
#                     convert_decimal128_to_float(item)
#     return document

# # 1. Conectar a MongoDB y leer los documentos de sample_airbnb.listingsAndReviews
# def read_documents_from_mongodb():
#     print(f"Conectando a MongoDB con la cadena de conexión: {MONGO_CLIENT}")
#     client = MongoClient(MONGO_CLIENT)
#     db = client['sample_airbnb']
#     collection = db['listingsAndReviews']
    
#     # Leer todos los documentos de la colección
#     documents = list(collection.find({}))
#     print(f"Se han leído {len(documents)} documentos desde MongoDB")
#     return documents

# # 2. Calcular embeddings usando SentenceTransformer
# def calculate_embeddings(documents, embedding_model):
#     for doc in documents:
#         text_to_embed = f"{doc.get('name', '')} {doc.get('summary', '')} {doc.get('description', '')}"

#         # Concatenar comentarios de reviews si existen
#         reviews = doc.get('reviews', [])
#         comments = " ".join([review.get('comments', '') for review in reviews])
#         text_to_embed += f" {comments}"

#         # Calcular embeddings usando el modelo de SentenceTransformer
#         embedding = embedding_model.encode(text_to_embed)
        
#         # Guardar los embeddings en el documento
#         doc['embedding'] = embedding.tolist()  # Convertir a lista para JSON
#         print(f"Embedding calculado para el documento {doc.get('_id')}")

#     return documents

# # 3. Almacenar los documentos junto con los embeddings en Elasticsearch
# def store_documents_in_elasticsearch(documents):
#     # Conectar a Elasticsearch
#     es = Elasticsearch(es_url, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
#     print(f"Conectado a Elasticsearch en la URL: {es_url}")

#     # Iterar sobre los documentos y almacenarlos en el índice "listingsAndReviews"
#     for doc in documents:
#         # Convertir Decimal128 a float en el documento antes de almacenarlo
#         doc = convert_decimal128_to_float(doc)

#         # Insertar el documento en Elasticsearch
#         es.index(index="listings_and_reviews", body=doc)
#         print(f"Documento {doc.get('_id')} almacenado en Elasticsearch")

# # Función principal
# def run_migrador():
#     # Leer documentos de MongoDB
#     documents = read_documents_from_mongodb()

#     # Utilizar el modelo SentenceTransformer para calcular embeddings
#     embedding_model = SentenceTransformer('all-mpnet-base-v2')
#     documents_with_embeddings = calculate_embeddings(documents, embedding_model)

#     # Almacenar los documentos en Elasticsearch
#     store_documents_in_elasticsearch(documents_with_embeddings)

# # Ejecutar el migrador
# if __name__ == "__main__":
#     print("Ejecutando...")
#     run_migrador()
