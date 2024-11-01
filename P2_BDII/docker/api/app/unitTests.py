import unittest
from unittest.mock import patch, MagicMock
from flask import json
import os
import numpy as np
from pymongo import MongoClient

class TestAppFunctions(unittest.TestCase):

    # Simular las variables de entorno para evitar errores
    @patch.dict(os.environ, {
        "postgre_host": "localhost",
        "postgre_user": "test_user",
        "postgre_password": "test_password",
        "postgre_dbname": "test_db",
        "postgre_port": "5432",
        "mongo_client": "test_db",
        "ELASTIC_USER": "elastic_user",
        "ELASTIC_PASS": "elastic_password",
        "ELASTIC": "localhost",
        "ELASTIC_PORT": "9200"
    })
    @patch('app.MongoClient')
    def setUp(self, mock_mongo_client):
        # Mock para la conexión de MongoDB
        mock_db = MagicMock()
        mock_collection = MagicMock()

        # Mock para devolver el mock de la colección
        mock_mongo_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        # Asignación del mock_collection a la variable 
        self.mock_collection = mock_collection
        
        # Hacer el import luego de configurar los mocks y los patches
        from app import app, encode, search, apartment_search, distinct_fields
        
        # Modo de Tests
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.embedding_model')
    def test_encode(self, mock_embedding_model):
        # Cambio en el retorno para que sea un array de NumPy
        mock_embedding_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        
        from app import encode
        # Prueba con un texto no vacío
        response = encode("Hello world")
        self.assertEqual(response["text"], "Hello world")
        self.assertEqual(response["embeddings"], [0.1, 0.2, 0.3])
        
        # Prueba con texto vacío
        response = encode("")
        self.assertIsNone(response)

    @patch('app.lyrics_collection.aggregate')
    def test_search_mongo(self, mock_aggregate):
        # Configurar el mock de MongoDB
        mock_aggregate.return_value = [{
            "artist": "Test Artist",
            "genres": ["Rock"],
            "popularity": 5,
            "link": "artist_link",
            "score": 0.9,
            "matching_songs": [{
                "song_name": "Test Song",
                "lyric": "Some lyrics",
                "language": "English",
                "song_link": "song_link"
            }]
        }]

        # Simulación de una solicitud POST a /search
        response = self.app.post('/search', data=json.dumps({
            "query": "Test",
            "database": "mongo"
        }), content_type='application/json')

        # Verificar el contenido de la respuesta
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data[0]["artist"], "Test Artist")
        self.assertEqual(data[0]["song_name"], "Test Song")
        self.assertEqual(data[0]["score"], 0.9)

    @patch('app.get_postgres_connection')
    def test_search_postgres(self, mock_get_postgres_connection):
        # Configuración del mock de PostgreSQL
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("Test Artist", ["Rock"], 5, "artist_link", "Test Song", "song_link", "Some lyrics", "English", 0.9)
        ]
        mock_get_postgres_connection.return_value = mock_connection

        # Simulación de una solicitud POST a /search
        response = self.app.post('/search', data=json.dumps({
            "query": "Test",
            "database": "postgres"
        }), content_type='application/json')

        # Verificar el contenido de la respuesta
        self.assertEqual(response.status_code, 200) # Verificar el status
        data = json.loads(response.data) # Cargar los datos de la respuesta a una variable 
        self.assertEqual(data[0]["artist"], "Test Artist")
        self.assertEqual(data[0]["song_name"], "Test Song")
        self.assertEqual(data[0]["score"], 0.9)

    @patch('app.lyrics_collection.distinct')
    def test_distinct_fields(self, mock_distinct):
        # Configuración de los mocks para géneros y lenguajes
        mock_distinct.side_effect = [
            ["Rock; Pop; Jazz", "Hip-Hop; Classical"],  # Géneros
            ["en", "es", "fr"]  # lenguajes
        ]

        # Simulación de una solicitud GET a /distinct
        response = self.app.get('/distinct')
        
        # Verificar el contenido de la respuesta
        self.assertEqual(response.status_code, 200) # Verificar el status
        data = json.loads(response.data)
        self.assertIn("Rock", data["distinct_genres"])
        self.assertIn("Pop", data["distinct_genres"])
        self.assertIn("en", data["distinct_languages"])
        self.assertIn("fr", data["distinct_languages"])  

class TestApartmentSearchAPI(unittest.TestCase):
    
    # Configuración de las variables de entorno
    @patch.dict(os.environ, {
        "postgre_host": "localhost",
        "postgre_user": "test_user",
        "postgre_password": "test_password",
        "postgre_dbname": "test_db",
        "postgre_port": "5432",
        "mongo_client": "test_db",
        "ELASTIC_USER": "elastic_user",
        "ELASTIC_PASS": "elastic_password",
        "ELASTIC": "localhost",
        "ELASTIC_PORT": "9200"
    })
    @patch('app.es')  # Mock de Elasticsearch
    @patch('app.embedding_model')  # Mock del modelo de embeddings
    def test_apartment_search(self, mock_embedding_model, mock_es):
        # Configurar el mock de embedding_model.encode
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1] * 768  # Simular un embedding de 768 dimensiones
        mock_embedding_model.encode.return_value = mock_embedding

        # Configurar el mock de es.search para devolver resultados simulados
        mock_es.search.return_value = {
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'name': 'Test Apartment',
                            'summary': 'A lovely place to stay.',
                            'description': 'This is a spacious apartment.',
                            'reviews': [{'comments': 'Great experience!'}]
                        }
                    }
                ]
            }
        }

        # Preparar datos de entrada para la solicitud
        from app import app
        with app.test_client() as client:
            response = client.post('/apartment/search', json={'selected_text': 'spacious and lovely'})
            
            # Verificar que la respuesta tenga el código de status 200
            self.assertEqual(response.status_code, 200)

            # Convertir la respuesta a JSON
            results = response.get_json()
            
            # Verificar que el resultado tenga los campos esperados
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['name'], 'Test Apartment')
            self.assertEqual(results[0]['summary'], 'A lovely place to stay.')
            self.assertEqual(results[0]['description'], 'This is a spacious apartment.')
            self.assertEqual(results[0]['reviews'], ['Great experience!'])

            # Verificar que el método encode fue llamado con el texto correcto
            mock_embedding_model.encode.assert_called_once_with('spacious and lovely')
            
            # Verificar que es.search fue llamado con el query esperado
            expected_query = {
                "knn": {
                    "field": "embedding",
                    "query_vector": [0.1] * 768,
                    "k": 10,
                    "num_candidates": 50
                }
            }
            mock_es.search.assert_called_once_with(index="listings_and_reviews", body=expected_query)

if __name__ == "__main__":
    unittest.main()
