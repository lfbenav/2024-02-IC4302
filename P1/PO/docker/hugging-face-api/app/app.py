# pip install sentence-transformers
# pip install --upgrade torch sentence-transformers
# pip install "numpy<2"
from flask import Flask, jsonify, request
from sentence_transformers import SentenceTransformer
app = Flask(__name__)

# Cargar el modelo
model = SentenceTransformer('all-mpnet-base-v2')


@app.route("/")
def index():
    return "Funciona correctamente!"

@app.route("/status")
def status():
    text = "This is my best example. I'll play well today \n John is my name"
    embedding = model.encode(text)
    return jsonify({"embedding": embedding.tolist(), "text":text})

@app.route("/encode", methods=["POST"])
def generateVector():
    # Obtener el JSON del body
    data = request.get_json()
    text = data.get("text")
    # Verifica si el campo 'text' fue enviado
    if text is None:
        return jsonify({"error": "El campo 'text' es requerido"}), 400
    # Codificar el texto
    embedding = model.encode(text)
    # Crear la estructura del JSON que será retornado
    response = {
        "embeddings": embedding.tolist(),  # Convertir a lista si es un vector de numpy
        "text": text
    }    
    # Retornar el JSON
    return jsonify(response)

print("Ejecutando API")  
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    print("Termina")