import os
from pymongo import MongoClient
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

MONGO_CLIENT = os.getenv('mongo_client')

ELASTIC_PASSWORD = os.getenv("ELASTIC_PASS")
ELASTIC_USER = os.getenv("ELASTIC_USER")
ELASTIC_SERVICE = os.getenv("ELASTIC")
ELASTIC_PORT = os.getenv("ELASTIC_PORT")
es_url = f"http://{ELASTIC_SERVICE}:{ELASTIC_PORT}"

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

# 2. Calcular embeddings usando SentenceTransformer
def calculate_embeddings(documents, embedding_model):
    for doc in documents:
        text_to_embed = f"{doc.get('name', '')} {doc.get('summary', '')} {doc.get('description', '')}"

        # Concatenar comentarios de reviews si existen
        reviews = doc.get('reviews', [])
        comments = " ".join([review.get('comments', '') for review in reviews])
        text_to_embed += f" {comments}"

        # Calcular embeddings usando el modelo de SentenceTransformer
        embedding = embedding_model.encode(text_to_embed)
        
        # Guardar los embeddings en el documento
        doc['embedding'] = embedding.tolist()  # Convertir a lista para JSON
        print(f"Embedding calculado para el documento {doc.get('_id')}")

    return documents

# 3. Almacenar los documentos junto con los embeddings en Elasticsearch
def store_documents_in_elasticsearch(documents):
    # Conectar a Elasticsearch
    print(f"Conectando a Elasticsearch en la URL: {es_url}")
    es = Elasticsearch(es_url, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))

    # Iterar sobre los documentos y almacenarlos en el índice "listingsAndReviews"
    for doc in documents:
        es.index(index="listingsAndReviews", body=doc)
        print(f"Documento {doc.get('_id')} almacenado en Elasticsearch")

# Función principal
def run_migrador():
    # Leer documentos de MongoDB
    documents = read_documents_from_mongodb()

    # Utilizar el modelo SentenceTransformer para calcular embeddings
    embedding_model = SentenceTransformer('all-mpnet-base-v2')
    documents_with_embeddings = calculate_embeddings(documents, embedding_model)

    # Almacenar los documentos en Elasticsearch
    store_documents_in_elasticsearch(documents_with_embeddings)

# Ejecutar el migrador
if __name__ == "__main__":
    print("Ejecutando...")
    run_migrador()
