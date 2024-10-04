import unittest
from unittest.mock import patch, MagicMock
import os

class TestApp(unittest.TestCase):

    @patch('os.getenv')
    @patch('boto3.Session')
    @patch('pika.BlockingConnection')
    def test_get_csv(self, mock_pika_connection, mock_boto3_session, mock_getenv):
        # Mock a las variables de entorno
        mock_getenv.side_effect = lambda key: {
            "BUCKET": "valid-bucket-name",
            "ACCESS_KEY": "test-access-key",
            "SECRET_KEY": "test-secret-key",
            "PREFIX": "test-prefix",
            "RABBITMQ_USER": "test_user",
            "RABBITMQ_PASS": "test_pass",
            "RABBITMQ": "test_host",
            "RABBITMQ_QUEUE": "test_queue"
        }.get(key, None)

        # Mock al cliente de S3
        mock_s3_client = MagicMock()
        mock_boto3_session.return_value.client.return_value = mock_s3_client
        
        # Simulacion de la respuesta de list_objects_v2
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'test-file.csv'},
                {'Key': 'sample-file.csv'}
            ]
        }

        # Mock a la conexión de RabbitMQ
        mock_pika_connection.return_value = MagicMock()

        # Se importa el modulo despues de configurar el Mock
        import app

        # Se llama a la funcion
        csv_files = app.get_csv()
        # Se prueba que los resultados llamando a la funcion son los mismos que los que se espera que se reciban
        self.assertEqual(csv_files, ['test-file.csv', 'sample-file.csv'])
    
    @patch('os.getenv')
    @patch('boto3.Session')
    @patch('pika.BlockingConnection')
    def test_publish_csv_to_rabbitmq(self, mock_pika_connection, mock_boto3_session, mock_getenv):
        # Mockear las variables de entorno
        mock_getenv.side_effect = lambda key: {
            "BUCKET": "valid-bucket-name",
            "ACCESS_KEY": "test-access-key",
            "SECRET_KEY": "test-secret-key",
            "PREFIX": "test-prefix",
            "RABBITMQ_USER": "test_user",
            "RABBITMQ_PASS": "test_pass",
            "RABBITMQ": "test_host",
            "RABBITMQ_QUEUE": "test_queue"
        }.get(key, None)

        # Mockear el cliente de S3
        mock_s3_client = MagicMock()
        mock_boto3_session.return_value.client.return_value = mock_s3_client
        
        # Simular la respuesta de list_objects_v2
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'test-file.csv'},
                {'Key': 'another-file.txt'},
                {'Key': 'sample-file.csv'}
            ]
        }

        # Mockear la conexión a RabbitMQ
        mock_connection = MagicMock()
        mock_pika_connection.return_value = mock_connection

        # Importar el módulo después de haber configurado el mock
        import app

        # Se llama a la función que se va a probar
        app.publish_csv_to_rabbitmq('test_user', 'test_pass', 'test_host', 'test_queue')

        # Se verifica que la cola se haya declarado
        mock_connection.channel.return_value.queue_declare.assert_called_once_with(queue='test_queue')

        # Se verifica que los mensajes se hayan publicado correctamente
        mock_connection.channel.return_value.basic_publish.assert_any_call(exchange='', routing_key='test_queue', body='test-file.csv')
        mock_connection.channel.return_value.basic_publish.assert_any_call(exchange='', routing_key='test_queue', body='sample-file.csv')

        # Se verifica que la conexión se cierra al final
        mock_connection.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
