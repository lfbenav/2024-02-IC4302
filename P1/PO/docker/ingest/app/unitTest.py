import os
import unittest
from unittest.mock import patch, MagicMock, ANY, Mock, call
import pandas as pd
from io import StringIO

class TestAppFunctions(unittest.TestCase):

    @patch.dict(os.environ, {
        "BUCKET": "test-bucket",
        "ACCESS_KEY": "test-access-key",
        "SECRET_KEY": "test-secret-key",
        "HUGGING_FACE_API": "localhost",
        "HUGGING_FACE_API_PORT": "8000",
        "RABBITMQ_USER": "test-user",
        "RABBITMQ_PASS": "test-pass",
        "RABBITMQ_QUEUE": "test-queue",
        "RABBITMQ": "localhost",
        "MARIADB_USER": "test-mariadb-user",
        "MARIADB_PASS": "test-mariadb-pass",
        "MARIADB": "localhost",
        "MARIADB_DB": "test-db",
        "ELASTIC_PASS": "test-elastic-pass",
        "ELASTIC_USER": "test-elastic-user",
        "ELASTIC": "localhost",
        "ELASTIC_PORT": "9200",
    })
    @patch('app.pika.BlockingConnection')
    @patch('app.pika.ConnectionParameters')
    @patch('elasticsearch.Elasticsearch')
    def test_start_rabbitmq_consumer(self, MockElasticsearch, mock_connection_parameters, mock_blocking_connection):

        import app
        
        # Configurar el comportamiento simulado del cliente de Elasticsearch
        mock_es_instance = MockElasticsearch.return_value
        mock_es_instance.indices.exists.return_value = False  # Simula que el índice no existe

        # Llama a la función que se está probando
        app.start_rabbitmq_consumer()

        # Verifica que la conexión a RabbitMQ se haya realizado correctamente
        mock_blocking_connection.assert_called_once()
        mock_blocking_connection().channel.assert_called_once()
        
        # Verifica que se haya llamado a la verificación del índice en Elasticsearch
        mock_es_instance.indices.exists.assert_called_with(index="songs")


class TestAppFunctions2(unittest.TestCase):
    
    @patch('pymysql.connect')
    def test_is_song_processed(self, mock_pymysql_connect):
        # Simular conexión a la base de datos y cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        # Configurar el cursor para que devuelva un resultado específico
        mock_cursor.fetchone.return_value = (1,)  # Se simula que la canción ha sido procesada
        mock_connection.cursor.return_value = mock_cursor
        
        # Configurar el mock de pymysql.connect para que devuelva la conexión simulada
        mock_pymysql_connect.return_value = mock_connection

        import app

        # Llamar a la función is_song_processed
        song_id = 123
        result = app.is_song_processed(song_id, mock_connection)

        # Verificar que el cursor ejecutó la consulta con el id correcto
        mock_cursor.execute.assert_called_with("SELECT 1 FROM processed_songs WHERE id = %s", (song_id,))
        
        # Verificar el resultado
        self.assertTrue(result)  # Debe ser True ya que la canción ha sido procesada

    @patch('pymysql.connect')
    def test_is_song_not_processed(self, mock_pymysql_connect):
        # Simular conexión a la base de datos y cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        # Configurar el cursor para que no devuelva ningún resultado
        mock_cursor.fetchone.return_value = None  # Se simula que la canción no ha sido procesada
        mock_connection.cursor.return_value = mock_cursor
        
        # Configurar el mock de pymysql.connect para que devuelva la conexión simulada
        mock_pymysql_connect.return_value = mock_connection

        import app

        # Llamar a la función is_song_processed
        song_id = 456
        result = app.is_song_processed(song_id, mock_connection)

        # Verificar que el cursor ejecutó la consulta con el id correcto
        mock_cursor.execute.assert_called_with("SELECT 1 FROM processed_songs WHERE id = %s", (song_id,))
        
        # Verificar el resultado
        self.assertFalse(result)  # Debe ser False ya que la canción no ha sido procesada

    @patch('pymysql.connect')
    def test_mark_song_as_processed(self, mock_pymysql_connect):
        # Simular conexión a la base de datos
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        # Configurar el cursor para ser devuelto por la conexión simulada
        mock_connection.cursor.return_value = mock_cursor
        
        # Configurar el mock de pymysql.connect para que devuelva la conexión simulada
        mock_pymysql_connect.return_value = mock_connection

        import app

        # Llamar a la función mark_song_as_processed
        song_id = 123
        app.mark_song_as_processed(song_id, mock_connection)

        # Verificar que se ejecutó la consulta de inserción con el ID de la canción correcto
        mock_cursor.execute.assert_called_with("INSERT INTO processed_songs (id) VALUES (%s)", (song_id,))
        
        # Verificar que se realizó un commit en la conexión
        mock_connection.commit.assert_called_once()

class TestAppFunctions3(unittest.TestCase):
    @patch('pymysql.connect')
    def test_is_file_processed(self, mock_pymysql_connect):
        # Simular conexión a la base de datos y cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        # Configurar el cursor para que devuelva un resultado específico
        mock_cursor.fetchone.return_value = (1,)  # Simulamos que el archivo ha sido procesado
        mock_connection.cursor.return_value = mock_cursor
        
        # Configurar el mock de pymysql.connect para que devuelva la conexión simulada
        mock_pymysql_connect.return_value = mock_connection

        import app
        
        # Se llama a la función is_file_processed
        filename = 'test-file.csv'
        result = app.is_file_processed(filename, mock_connection)

        # Verificar que el cursor ejecutó la consulta con el filename correcto
        mock_cursor.execute.assert_called_with("SELECT 1 FROM processed_files WHERE filename = %s", (filename,))
        
        # Verificar el resultado
        self.assertTrue(result)  # Debe ser True ya que el archivo ha sido procesado

    @patch('pymysql.connect')
    def test_is_file_not_processed(self, mock_pymysql_connect):
        # Simular conexión a la base de datos y cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        # Configurar el cursor para que no devuelva ningún resultado
        mock_cursor.fetchone.return_value = None  # Se simula que el archivo no ha sido procesado
        mock_connection.cursor.return_value = mock_cursor
        
        # Configurar el mock de pymysql.connect para que devuelva la conexión simulada
        mock_pymysql_connect.return_value = mock_connection

        import app

        # Se llama a la función is_file_processed
        filename = 'test-file.csv'
        result = app.is_file_processed(filename, mock_connection)

        # Verificar que el cursor ejecutó la consulta con el filename correcto
        mock_cursor.execute.assert_called_with("SELECT 1 FROM processed_files WHERE filename = %s", (filename,))
        
        # Verificar el resultado
        self.assertFalse(result)  # Debe ser False ya que el archivo no ha sido procesado
    
    @patch('pymysql.connect')
    def test_mark_file_as_processed(self, mock_pymysql_connect):
        # Simular conexión a la base de datos
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        # Configurar el cursor para ser devuelto por la conexión simulada
        mock_connection.cursor.return_value = mock_cursor
        
        # Configurar el mock de pymysql.connect para que devuelva la conexión simulada
        mock_pymysql_connect.return_value = mock_connection

        import app

        # Llamada a la función mark_file_as_processed
        filename = 'test_file.csv'
        app.mark_file_as_processed(filename, mock_connection)

        # Verificar que se ejecutó la consulta de inserción con el nombre de archivo correcto
        mock_cursor.execute.assert_called_with(
            "INSERT INTO processed_files (filename, processed) VALUES (%s, %s)", 
            (filename, 1)
        )
        
        # Verificar que se realizó un commit en la conexión
        mock_connection.commit.assert_called_once()

class TestAppFunctions4(unittest.TestCase):
    
    @patch('requests.post')
    @patch.dict(os.environ, {
        "HUGGING_FACE_API": "localhost",
        "HUGGING_FACE_API_PORT": "8080"
    })
    def test_generate_embedding_success(self, mock_post):
        # Simulamos una respuesta exitosa de la API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embeddings": [0.1, 0.2, 0.3]}  # Embedding simulado
        mock_post.return_value = mock_response
        
        import app

        text = "Test text"
        embedding = app.generate_embedding(text)
        
        # Verificamos que se haya llamado a requests.post con los parámetros correctos
        mock_post.assert_called_once_with("http://localhost:None/encode", json={"text": text})
        
        # Verificamos que el embedding retornado es el esperado
        self.assertEqual(embedding, [0.1, 0.2, 0.3])

    @patch('requests.post')
    @patch.dict(os.environ, {
        "HUGGING_FACE_API": "localhost",
        "HUGGING_FACE_API_PORT": "8080"
    })
    def test_generate_embedding_no_embedding(self, mock_post):
        # Simulamos una respuesta exitosa de la API sin embedding
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "No embeddings found"}  # Sin embedding
        mock_post.return_value = mock_response
        
        text = "Test text"
        
        import app

        # Verificamos que exista una excepción al no encontrar el embedding
        with self.assertRaises(Exception) as context:
            app.generate_embedding(text)
        
        self.assertEqual(str(context.exception), "No se encontró el embedding en la respuesta: {'message': 'No embeddings found'}")

    @patch('requests.post')
    @patch.dict(os.environ, {
        "HUGGING_FACE_API": "localhost",
        "HUGGING_FACE_API_PORT": "8080"
    })
    def test_generate_embedding_error_status_code(self, mock_post):
        # Simulamos una respuesta de error de la API
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        text = "Test text"
        
        import app

        # Se verifica que exista una excepción al recibir un código de estado de error
        with self.assertRaises(Exception) as context:
            app.generate_embedding(text)
        
        self.assertEqual(str(context.exception), "Error al generar embedding desde Hugging Face API, Status Code: 500")

class TestAppFunctions5(unittest.TestCase):

    @patch('app.pymysql.connect')  # Simular la conexión a la base de datos
    @patch('app.is_file_processed')  # Simular la verificación del archivo procesado
    @patch('app.is_song_processed')  # Simular la verificación de la canción procesada
    @patch('app.generate_embedding')  # Simular la generación de embeddings
    @patch('app.bulk')  # Simular la operación bulk en Elasticsearch
    @patch('app.mark_song_as_processed')  # Simular mark_song_as_processed
    @patch('app.mark_file_as_processed')  # Simular mark_file_as_processed
    def test_process_csv(self, mock_mark_file, mock_mark_song, mock_bulk, mock_generate_embedding, 
                         mock_is_song_processed, mock_is_file_processed, mock_connect):
        # Datos de entrada para el CSV
        csv_data = """id,name,artists,album_name,lyrics
        1,Song A,Artist A,Album A,These are the lyrics for song A.
        2,Song B,Artist B,Album B,These are the lyrics for song B.
        """
        filename = "test_file.csv"
        
        # Simulaciones
        mock_is_file_processed.return_value = False  # El archivo no ha sido procesado
        mock_is_song_processed.side_effect = [False, False]  # Ninguna canción ha sido procesada
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]  # Embedding simulado
        mock_bulk.return_value = (2, 0)  # 2 documentos subidos exitosamente, 0 fallidos

        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        import app

        app.process_csv(csv_data, filename, batch_size=2)

        # Se verifican que las funciones fueron llamadas adecuadamente
        mock_connect.assert_called_once()
        mock_is_file_processed.assert_called_once_with(filename, mock_connection)
        mock_generate_embedding.assert_any_call("These are the lyrics for song A.")
        mock_generate_embedding.assert_any_call("These are the lyrics for song B.")
        mock_bulk.assert_called_once()  # Asegurarse de que se llamó a la operación bulk
        mock_mark_file.assert_called_once_with(filename, mock_connection)  # Verificar que el archivo fue marcado como procesado
        mock_mark_song.assert_called() # Como ya se reviso en una prueba anterior si se marcan las canciones, se verifica que se realiza la llamada
        mock_connection.close.assert_called_once()  # Verificar que la conexión fue cerrada

    @patch('app.pymysql.connect')
    @patch('app.is_file_processed')
    @patch('app.is_song_processed')
    @patch('app.generate_embedding')
    @patch('app.bulk')
    @patch('app.mark_song_as_processed')
    @patch('app.mark_file_as_processed')
    def test_process_csv_song_already_processed(self, mock_mark_file, mock_mark_song, 
                                                 mock_bulk, mock_generate_embedding, 
                                                 mock_is_song_processed, mock_is_file_processed, 
                                                 mock_connect):
        # Datos de entrada para el CSV
        csv_data = """id,name,artists,album_name,lyrics
        1,Song A,Artist A,Album A,These are the lyrics for song A.
        """
        filename = "test_file.csv"
        
        # Simulaciones
        mock_is_file_processed.return_value = False  # El archivo no ha sido procesado
        mock_is_song_processed.return_value = True  # La canción ya ha sido procesada
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]  # Embedding simulado

        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        import app

        app.process_csv(csv_data, filename, batch_size=1)

        # Verificar que la canción no fue procesada
        mock_is_song_processed.assert_called_once_with(1, mock_connection)
        mock_generate_embedding.assert_not_called()  # No debería llamar a generate_embedding
        mock_bulk.assert_not_called()  # No debería llamar a bulk
        mock_mark_song.assert_not_called()  # No debería marcar la canción como procesada
        mock_mark_file.assert_called_once_with(filename, mock_connection)  # Archivo marcado como procesado
        mock_connection.close.assert_called_once()  # Verificar que la conexión fue cerrada

class TestAppFunctions6(unittest.TestCase):

    @patch('pymysql.connect')
    @patch('app.download_from_s3')  
    @patch('app.process_csv')
    @patch('app.is_file_processed')
    def test_callback_file_processed(self, mock_is_file_processed, mock_process_csv, mock_download_from_s3, mock_connect):
        # Configuración del mock
        mock_is_file_processed.return_value = True  # Simulamos que el archivo ya fue procesado
        
        import app

        # Llamamos a la función callback
        app.callback(None, None, None, b'test_file.csv')

        # Verificamos que no se descargó ni procesó el archivo
        mock_download_from_s3.assert_not_called()
        mock_process_csv.assert_not_called()
        mock_connect.assert_called_once()  # Se asegura que se llamó a connect solamente una vez

    @patch('pymysql.connect')
    @patch('app.download_from_s3')
    @patch('app.process_csv')
    @patch('app.is_file_processed')
    def test_callback_process_file(self, mock_is_file_processed, mock_process_csv, mock_download_from_s3, mock_connect):
        # Configuración del mock
        mock_is_file_processed.return_value = False  # Simulamos que el archivo no fue procesado
        mock_download_from_s3.return_value = "mock_csv_data"  # Simulamos datos CSV descargados

        import app

        # Llamada a la función callback
        app.callback(None, None, None, b'test_file.csv')

        # Verificamos que se descargó y procesó el archivo
        mock_download_from_s3.assert_called_once_with('test_file.csv')
        mock_process_csv.assert_called_once_with("mock_csv_data", 'test_file.csv')
        mock_connect.assert_called_once()  # Aseguramos que se llamó a connect una vez

if __name__ == '__main__':
    unittest.main()
