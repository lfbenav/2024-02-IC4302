# pip install sentence-transformers
# pip install --upgrade torch sentence-transformers
# pip install "numpy<2"
from flask import Flask, jsonify, request
from sentence_transformers import SentenceTransformer
from prometheus_client import Counter, Histogram, generate_latest
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()] 
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Cargar el modelo
model = SentenceTransformer('all-mpnet-base-v2')

# Contador de requests al endpoint /encode
REQUEST_COUNT = Counter('api_requests_total', 'Total number of requests to the encode endpoint', ['endpoint'])
# Histograma para medir el tiempo que tarda en generar el embedding
REQUEST_LATENCY = Histogram('embedding_generation_seconds', 'Time spent generating embeddings', ['endpoint'])

@app.route("/")
def index():
    return "Funciona correctamente!"

# Ruta para conseguir las metricas
@app.route("/metrics")
def metrics():
    return generate_latest(), 200

@app.route("/status")
def status():
    logger.info("Se accedió al endpoint /status .")
    text = "This is my best example. I'll play well today \n John is my name"
    embedding = model.encode(text)
    return jsonify({"embedding": embedding.tolist(), "text":text})

@app.route("/encode", methods=["POST"])
def generateVector():
    REQUEST_COUNT.labels(endpoint='/encode').inc()  # Incrementar el contador de requests

    # Medir el tiempo que tarda en generar el embedding
    with REQUEST_LATENCY.labels(endpoint='/encode').time():
        # Obtener el JSON del body
        data = request.get_json()
        text = data.get("text")
        
        # Verifica si el campo 'text' fue enviado
        if text is None:
            logger.error("Error: El campo 'text' es requerido.")
            return jsonify({"error": "El campo 'text' es requerido"}), 400
        
        # Codificar el texto
        embedding = model.encode(text)
        
        # Crear la estructura del JSON que será retornado
        response = {
            "embeddings": embedding.tolist(),  # Convertir a lista si es un vector de numpy
            "text": text
        }

    logger.info("Embeddings generados exitosamente.")
    # Retornar el JSON
    return jsonify(response)

logger.info("Ejecutando API")
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    print("Termina")