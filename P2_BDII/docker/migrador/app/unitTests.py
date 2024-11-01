import os
import unittest
from unittest.mock import patch, MagicMock
from bson.decimal128 import Decimal128
from app import (
    read_documents_from_mongodb,
    calculate_embedding_for_document,
    store_document_in_elasticsearch,
    create_elasticsearch_index
)

class TestMigrador(unittest.TestCase):
    # Patch a las variables de entorno
    @patch.dict(os.environ, {
        'mongo_client': 'mongodb://localhost:27017',
        'ELASTIC_PASS': 'test_password',
        'ELASTIC_USER': 'test_user',
        'ELASTIC': 'localhost',
        'ELASTIC_PORT': '9200'
    })
    @patch('app.MongoClient') # Patch de MongoClient
    def test_read_documents_from_mongodb(self, mock_mongo_client):
        # Configuración de los Mocks
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        mock_collection.find.return_value = [{'name': 'Artist1'}]

        documents = read_documents_from_mongodb() # llamada a la función
        # Revisar que exista solo un documento y que coincida con el simulado
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]['name'], 'Artist1')

    # Patch a las variables de entorno
    @patch.dict(os.environ, {
        'mongo_client': 'mongodb://localhost:27017',
        'ELASTIC_PASS': 'test_password',
        'ELASTIC_USER': 'test_user',
        'ELASTIC': 'localhost',
        'ELASTIC_PORT': '9200'
    })
    @patch('app.SentenceTransformer')
    def test_calculate_embedding_for_document(self, mock_sentence_transformer):
        # Crear un objeto de embedding simulado 
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = [0.1] * 768  # Simulando un embedding 
        
        # Configurar el modelo de embeddings simulado para devolver el mock_embedding
        mock_embedding_model = MagicMock()
        mock_sentence_transformer.return_value = mock_embedding_model
        mock_embedding_model.encode.return_value = mock_embedding  
        
        # Documento de prueba
        doc = {
            '_id': 1,
            'name': 'Test',
            'summary': 'Summary',
            'description': 'Description',
            'reviews': [{'comments': 'Great!'}]
        }

        # Ejecutar la función con el documento y modelo simulados
        result_doc = calculate_embedding_for_document(doc, mock_embedding_model)

        # Verificar si el embedding fue agregado al documento
        self.assertIn('embedding', result_doc)
        self.assertEqual(result_doc['embedding'], [0.1] * 768)  # Comparación con el embedding simulado

    # Patch a las variables de entorno
    @patch.dict(os.environ, {
        'mongo_client': 'mongodb://localhost:27017',
        'ELASTIC_PASS': 'test_password',
        'ELASTIC_USER': 'test_user',
        'ELASTIC': 'localhost',
        'ELASTIC_PORT': '9200'
    })
    @patch('app.Elasticsearch')
    def test_store_document_in_elasticsearch(self, mock_elasticsearch):
        # Mocks
        mock_es_instance = MagicMock()
        mock_elasticsearch.return_value = mock_es_instance

        # Dato simulado
        doc = {
            '_id': 1,
            'name': 'Test',
            'summary': 'Summary',
            'description': 'Description',
            'reviews': [{'comments': 'Great!'}],
            'embedding': [0.1] * 768
        }

        # Simulando que el documento no existe en Elasticsearch
        mock_es_instance.exists.return_value = False
        store_document_in_elasticsearch(doc, mock_es_instance) # llamada a la función que se esta probando

        mock_es_instance.index.assert_called_once()
        self.assertEqual(mock_es_instance.index.call_args[1]['id'], '1')

    # Patch a las variables de entorno
    @patch.dict(os.environ, {
        'mongo_client': 'mongodb://localhost:27017',
        'ELASTIC_PASS': 'test_password',
        'ELASTIC_USER': 'test_user',
        'ELASTIC': 'localhost',
        'ELASTIC_PORT': '9200'
    })
    @patch('app.Elasticsearch')
    def test_create_elasticsearch_index(self, mock_elasticsearch):
        # Configuración de los Mocks
        mock_es_instance = MagicMock()
        mock_elasticsearch.return_value = mock_es_instance

        # Simulando que el índice no existe:
        mock_es_instance.indices.exists.return_value = False
        create_elasticsearch_index(mock_es_instance)

        # Revisar que se llamó una vez
        mock_es_instance.indices.create.assert_called_once()

if __name__ == '__main__':
    unittest.main()
