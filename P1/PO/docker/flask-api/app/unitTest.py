import unittest
from unittest.mock import patch, MagicMock
import os
import json
import base64
from datetime import datetime
from flask import jsonify

class TestRegisterFunction(unittest.TestCase):

    @patch.dict(os.environ, {
        'ELASTIC_USER': 'elastic_user',
        'ELASTIC_PASS': 'elastic_password',
        'ELASTIC': 'localhost',
        'ELASTIC_PORT': '9200',
        'MARIADB_USER': 'test_user',
        'MARIADB_PASS': 'test_pass',
        'MARIADB': 'localhost',
        'MARIADB_DB': 'test_db'
    })
    @patch('elasticsearch.Elasticsearch')
    @patch('appPruebas.get_connection')
    def test_register_success(self, mock_get_connection, mock_elasticsearch):
        # Mock de la conexión
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Definir la respuesta esperada
        mock_cursor.execute.return_value = None

        # Se importa el modulo después de que las variables de entorno y mocks están aplicados
        import appPruebas

        # Configurar el cliente de prueba de Flask
        with appPruebas.app.test_client() as client:  
            # Datos que se envían a la solicitud POST
            data = {
                "username": "test_user",
                "password": "password123"
            }

            # Simular la solicitud POST
            response = client.post('/register', data=json.dumps(data), content_type='application/json')

            # Se verifica que la respuesta fue exitosa
            self.assertEqual(response.status_code, 200)

            # Se verifica que el estado de la respuesta es "Usuario registrado con éxito"
            response_json = response.get_json()  # Se obtiene la respuesta como JSON
            self.assertEqual(response_json['status'], 'Usuario registrado con éxito')

            # Se verifica que se hizo la llamada correcta al método cursor.execute()
            mock_cursor.execute.assert_called_once_with(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                ('test_user', 'cGFzc3dvcmQxMjM=')  # Base64 encoded password123
            )

            # Se verifica que se realizó el commit
            mock_connection.commit.assert_called_once()

class TestLoginFunction(unittest.TestCase):

    @patch.dict(os.environ, {
        'ELASTIC_USER': 'elastic_user',
        'ELASTIC_PASS': 'elastic_password',
        'ELASTIC': 'localhost',
        'ELASTIC_PORT': '9200',
        'MARIADB_USER': 'test_user',
        'MARIADB_PASS': 'test_pass',
        'MARIADB': 'localhost',
        'MARIADB_DB': 'test_db'
    })
    @patch('elasticsearch.Elasticsearch')
    @patch('appPruebas.get_connection')
    def test_login_success(self, mock_get_connection, mock_elasticsearch):
        # Crear un mock de la conexión
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Datos de prueba
        username = "test_user"
        password = "password123"
        encrypted_password = base64.b64encode(password.encode('utf-8')).decode('utf-8')

        # Simular el resultado de la consulta
        mock_cursor.fetchone.return_value = (username,)

        # Importar 'appPruebas' después de que las variables de entorno y mocks están aplicados
        import appPruebas

        # Configurar el cliente de prueba de Flask
        with appPruebas.app.test_client() as client:
            # Datos que se envían a la solicitud POST
            data = {
                "username": username,
                "password": password
            }

            # Simular la solicitud POST
            response = client.post('/login', data=json.dumps(data), content_type='application/json')

            # Verificar que la respuesta fue exitosa
            self.assertEqual(response.status_code, 200)

            # Verificar que el estado de la respuesta es "Inicio de sesión exitoso"
            response_json = response.get_json()
            self.assertEqual(response_json['status'], 'Inicio de sesión exitoso')

            # Verificar que se hizo la llamada correcta al método cursor.execute()
            mock_cursor.execute.assert_called_once_with(
                "SELECT username FROM users WHERE username = %s and password = %s",
                (username, encrypted_password)
            )

            # Verificar que se realizó el commit
            mock_connection.close.assert_called_once()

    @patch.dict(os.environ, {
        'ELASTIC_USER': 'elastic_user',
        'ELASTIC_PASS': 'elastic_password',
        'ELASTIC': 'localhost',
        'ELASTIC_PORT': '9200',
        'MARIADB_USER': 'test_user',
        'MARIADB_PASS': 'test_pass',
        'MARIADB': 'localhost',
        'MARIADB_DB': 'test_db'
    })
    @patch('elasticsearch.Elasticsearch')
    @patch('appPruebas.get_connection')
    def test_login_failure(self, mock_get_connection, mock_elasticsearch):
        # Crear un mock de la conexión
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Datos de prueba
        username = "test_user"
        password = "wrong_password"
        encrypted_password = base64.b64encode(password.encode('utf-8')).decode('utf-8')

        # Simular que no se encontró el usuario
        mock_cursor.fetchone.return_value = None

        # Importar 'appPruebas' después de que las variables de entorno y mocks están aplicados
        import appPruebas

        # Configurar el cliente de prueba de Flask
        with appPruebas.app.test_client() as client:
            # Datos que se envían a la solicitud POST
            data = {
                "username": username,
                "password": password
            }

            # Simular la solicitud POST
            response = client.post('/login', data=json.dumps(data), content_type='application/json')

            # Verificar que la respuesta fue fallida
            self.assertEqual(response.status_code, 404)

            # Verificar que el estado de la respuesta es "Inicio fallido"
            response_json = response.get_json()
            self.assertEqual(response_json['status'], 'Inicio fallido')

            # Verificar que se hizo la llamada correcta al método cursor.execute()
            mock_cursor.execute.assert_called_once_with(
                "SELECT username FROM users WHERE username = %s and password = %s",
                (username, encrypted_password)
            )

            # Verificar que se cerró la conexión
            mock_connection.close.assert_called_once()

class TestAskFunction(unittest.TestCase):

    @patch.dict(os.environ, {
        'HUGGING_FACE_API': 'localhost',
        'HUGGING_FACE_API_PORT': '5000',
        'ELASTIC_USER': 'elastic_user',
        'ELASTIC_PASS': 'elastic_password',
        'ELASTIC': 'localhost',
        'ELASTIC_PORT': '9200',
    })
    @patch('appPruebas.requests.post')
    @patch('appPruebas.es.search')
    def test_ask_success(self, mock_es_search, mock_requests_post):
        # Datos de prueba
        question = "¿Cuál es la mejor canción?"

        # Simular la respuesta de Hugging Face
        mock_requests_post.return_value = MagicMock(status_code=200, json=lambda: {"embeddings": [0.1, 0.2, 0.3]})

        # Simular la respuesta de Elasticsearch
        mock_es_search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "name": "Song A",
                            "lyrics": "Lyrics of Song A",
                            "artists": "Artist A"
                        }
                    },
                    {
                        "_source": {
                            "name": "Song B",
                            "lyrics": "Lyrics of Song B",
                            "artists": "Artist B"
                        }
                    }
                ]
            }
        }

        # Importar el modulo después de que las variables de entorno y mocks están aplicados
        import appPruebas

        # Configurar el cliente de prueba de Flask
        with appPruebas.app.test_client() as client:
            # Datos que se envían a la solicitud POST
            data = {
                "question": question
            }

            # Simular la solicitud POST
            response = client.post('/ask', data=json.dumps(data), content_type='application/json')

            # Verificar que la respuesta fue exitosa
            self.assertEqual(response.status_code, 200)

            # Verificar que se obtuvieron resultados
            response_json = response.get_json()
            self.assertEqual(len(response_json), 2)
            self.assertEqual(response_json[0]['name'], 'Song A')
            self.assertEqual(response_json[1]['name'], 'Song B')

            # Verificar que se hizo la llamada correcta a Hugging Face
            mock_requests_post.assert_called_once_with(
                "http://localhost:None/encode", json={"text": question}
            )

            # Verificar que se hizo la llamada correcta a Elasticsearch
            mock_es_search.assert_called_once()

    @patch.dict(os.environ, {
        'HUGGING_FACE_API': 'localhost',
        'HUGGING_FACE_API_PORT': '5000',
        'ELASTIC_USER': 'elastic_user',
        'ELASTIC_PASS': 'elastic_password',
        'ELASTIC': 'localhost',
        'ELASTIC_PORT': '9200',
    })
    @patch('appPruebas.requests.post')
    def test_ask_missing_question(self, mock_requests_post):
        # Importar el modulo después de que las variables de entorno y mocks están aplicados
        import appPruebas

        # Configurar el cliente de prueba de Flask
        with appPruebas.app.test_client() as client:
            # Simular la solicitud POST sin el campo 'question'
            response = client.post('/ask', data=json.dumps({}), content_type='application/json')

            # Verificar que se devolvió un error 400
            self.assertEqual(response.status_code, 400)

            # Verificar que el mensaje de error es correcto
            response_json = response.get_json()
            self.assertEqual(response_json['error'], "El campo 'question' es requerido")

    @patch.dict(os.environ, {
        'HUGGING_FACE_API': 'localhost',
        'HUGGING_FACE_API_PORT': '5000',
        'ELASTIC_USER': 'elastic_user',
        'ELASTIC_PASS': 'elastic_password',
        'ELASTIC': 'localhost',
        'ELASTIC_PORT': '9200',
    })
    @patch('appPruebas.requests.post')
    def test_ask_hugging_face_error(self, mock_requests_post):
        # Simular la respuesta de Hugging Face con un error
        mock_requests_post.return_value = MagicMock(status_code=500)

        # Importar 'appPruebas' después de que las variables de entorno y mocks están aplicados
        import appPruebas

        # Configurar el cliente de prueba de Flask
        with appPruebas.app.test_client() as client:
            # Datos que se envían a la solicitud POST
            data = {
                "question": "¿Cuál es la mejor canción?"
            }

            # Simular la solicitud POST
            response = client.post('/ask', data=json.dumps(data), content_type='application/json')

            # Verificar que se devolvió un error 500
            self.assertEqual(response.status_code, 500)

            # Verificar que el mensaje de error es correcto
            response_json = response.get_json()
            self.assertEqual(response_json['error'], "Error al obtener el embedding")

    @patch.dict(os.environ, {
        'HUGGING_FACE_API': 'localhost',
        'HUGGING_FACE_API_PORT': '5000',
        'ELASTIC_USER': 'elastic_user',
        'ELASTIC_PASS': 'elastic_password',
        'ELASTIC': 'localhost',
        'ELASTIC_PORT': '9200',
    })
    @patch('appPruebas.requests.post')
    @patch('appPruebas.es.search')
    def test_ask_no_embedding(self, mock_es_search, mock_requests_post):
        # Datos de prueba
        question = "¿Cuál es la mejor canción?"

        # Simular la respuesta de Hugging Face sin embeddings
        mock_requests_post.return_value = MagicMock(status_code=200, json=lambda: {"embeddings": []})

        # Importar 'appPruebas' después de que las variables de entorno y mocks están aplicados
        import appPruebas

        # Configurar el cliente de prueba de Flask
        with appPruebas.app.test_client() as client:
            # Datos que se envían a la solicitud POST
            data = {
                "question": question
            }

            # Simular la solicitud POST
            response = client.post('/ask', data=json.dumps(data), content_type='application/json')

            # Verificar que se devolvió un error 500
            self.assertEqual(response.status_code, 500)

            # Verificar que el mensaje de error es correcto
            response_json = response.get_json()
            self.assertEqual(response_json['error'], "No se pudo generar el embedding")

class TestPublishFunction(unittest.TestCase):

    @patch.dict(os.environ, {
        'MARIADB_USER': 'test_user',
        'MARIADB_PASS': 'test_pass',
        'MARIADB': 'localhost',
        'MARIADB_DB': 'test_db'
    })
    @patch('appPruebas.get_connection')
    def test_publish_success(self, mock_get_connection):
        # Crear un mock de la conexión
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Datos de entrada para la prueba
        test_data = {
            "username": "test_user",
            "prompt": "Este es un prompt de prueba"
        }

        import appPruebas

        # Configurar el cliente de prueba de Flask
        with appPruebas.app.test_client() as client:
            # Simular la solicitud POST
            response = client.post('/publish', json=test_data)

            # Verificar que la respuesta fue exitosa
            self.assertEqual(response.status_code, 200)

            # Convertir la respuesta en un diccionario JSON
            response_json = json.loads(response.data.decode('utf-8'))
            self.assertIn('status', response_json)
            self.assertEqual(response_json['status'], 'Prompt publicado con éxito')

            # Verificar que se hizo la llamada correcta al método cursor.execute()
            mock_cursor.execute.assert_called_once()
            args, _ = mock_cursor.execute.call_args  # Obtener los argumentos pasados
            self.assertEqual(args[0], 'INSERT INTO prompts (username, prompt, date, likes) VALUES (%s, %s, %s, %s)')  # Verifica la consulta SQL
            self.assertEqual(args[1][0], 'test_user')  # Verificar username
            self.assertEqual(args[1][1], 'Este es un prompt de prueba')  # Verificar prompt
            self.assertIsInstance(args[1][2], datetime)  # Verificar que el tercer argumento sea un datetime
            self.assertEqual(args[1][3], 0)  # Verificar likes

class TestSearchFunction(unittest.TestCase):

    @patch('appPruebas.get_connection')
    def test_search(self, mock_get_connection):
        # Crear la aplicación en cada prueba
        import appPruebas
        appPruebas.app.test_client().testing = True
        
        # Simulación de conexión a la base de datos
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Simulación de datos devueltos por la consulta
        mock_cursor.fetchall.return_value = [
            (1, 'user1', 'Este es un prompt de prueba', '2024-09-26 09:03:07', 0),
            (2, 'user2', 'Otro prompt de prueba', '2024-09-26 09:04:07', 5)
        ]
        
        # Realizar la solicitud GET
        response = appPruebas.app.test_client().get('/search?keyword=prompt')

        # Verificar el estado de la respuesta y los datos
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 2)
        self.assertEqual(data['results'][0]['username'], 'user1')
        self.assertEqual(data['results'][1]['likes'], 5)

class TestLikeFunction(unittest.TestCase):

    @patch('appPruebas.get_connection')
    @patch('appPruebas.datetime')
    def test_like_success(self, mock_datetime, mock_get_connection):
        # Valor fijo para datetime.now()
        fixed_time = datetime(2024, 9, 26, 9, 44, 59)
        mock_datetime.now.return_value = fixed_time

        # Inicializar el cliente de pruebas
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configurar el mock de la conexión y el cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simular que el prompt existe y no hay like previo
        mock_cursor.fetchone.side_effect = [None, (5,), ("Test prompt",)]

        # Hacer la solicitud POST a /like
        response = client.post("/like", json={
            "username": "test_user",
            "prompt_id": 1
        })

        # Afirmaciones
        self.assertEqual(response.status_code, 200)
        self.assertIn("Prompt liked and republished successfully", response.get_data(as_text=True))
        
        # Verificar que se ejecutaron las consultas en el orden correcto y con los parámetros adecuados
        mock_cursor.execute.assert_any_call(
            "INSERT INTO likes (username, prompt_id) VALUES (%s, %s)", 
            ("test_user", 1)
        )
        mock_cursor.execute.assert_any_call(
            "UPDATE prompts SET likes = likes + 1 WHERE id = %s", 
            (1,)
        )
        
        # Verifica la llamada a la inserción del prompt republicado
        mock_cursor.execute.assert_any_call(
            "INSERT INTO prompts (username, prompt, date, likes) VALUES (%s, %s, %s, %s)",
            ("test_user", "Test prompt", fixed_time, 0)
        )
        
        # Asegurar que se hizo commit
        mock_connection.commit.assert_called_once()

    @patch('appPruebas.get_connection')
    def test_like_already_exists(self, mock_get_connection):
        # Inicializar el cliente de pruebas
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configurar el mock de la conexión y el cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simular que ya existe un like para el prompt
        mock_cursor.fetchone.return_value = ("test_user", 1)

        # Hacer la solicitud POST a /like
        response = client.post("/like", json={
            "username": "test_user",
            "prompt_id": 1
        })

        # Afirmaciones
        self.assertEqual(response.status_code, 400)
        self.assertIn("You have already liked this prompt", response.get_data(as_text=True))

    @patch('appPruebas.get_connection')
    def test_like_prompt_not_found(self, mock_get_connection):
        # Inicializar el cliente de pruebas
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configurar el mock de la conexión y el cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simular que el prompt no existe
        mock_cursor.fetchone.side_effect = [None, None, None]

        # Hacer la solicitud POST a /like
        response = client.post("/like", json={
            "username": "test_user",
            "prompt_id": 1
        })

        # Afirmaciones
        self.assertEqual(response.status_code, 404)
        self.assertIn("Prompt not found", response.get_data(as_text=True))

class TestGetProfileFunction(unittest.TestCase):

    @patch('appPruebas.get_connection')
    def test_get_profile_success(self, mock_get_connection):
        # Inicializar el cliente de pruebas
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configurar el mock de la conexión y el cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simular que el usuario existe
        mock_cursor.fetchone.return_value = ("test_user",)

        # Hacer la solicitud GET a /me/getProfile
        with appPruebas.app.test_client() as client:  # Asegúrate de usar el contexto correcto
            response = client.get('/me/getProfile', json={"username": "test_user"})

        # Afirmaciones
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"results": ['test_user',]})

        # Verifica que la consulta se haya ejecutado correctamente
        mock_cursor.execute.assert_called_once_with(
            "SELECT username FROM users WHERE username = %s", 
            'test_user'
        )

class TestUpdatePasswordFunction(unittest.TestCase):
    @patch('appPruebas.get_connection')
    def test_update_password_success(self, mock_get_connection):
        # Configura el mock de la conexión y el cursor
        mock_cursor = MagicMock()
        mock_get_connection.return_value.__enter__.return_value = mock_cursor
        
        username = "test_user"
        password = "test_password"
        new_password = "new_test_password"
        encrypted_password = base64.b64encode(password.encode('utf-8')).decode('utf-8')
        encrypted_new_password = base64.b64encode(new_password.encode('utf-8')).decode('utf-8')

        # Simula la respuesta del cursor para el caso exitoso
        mock_cursor.rowcount = 1  # Simula que se actualizó 1 fila

        import appPruebas
        # Realiza la solicitud de prueba
        with appPruebas.app.test_client() as client:
            response = client.post('/me/updatePassword', json={
                "username": username,
                "password": password,
                "newPassword": new_password
            })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "Usuario registrado con éxito"})

class TestUpdatePromptFunction(unittest.TestCase):
    @patch('appPruebas.get_connection')
    def test_update_prompt_success(self, mock_get_connection):
        # Configura el mock de la conexión y el cursor
        mock_cursor = MagicMock()
        mock_get_connection.return_value.__enter__.return_value = mock_cursor
        
        prompt_id = 1
        new_prompt_text = "Updated prompt text"
        
        # Simula que el prompt existe
        mock_cursor.fetchone.return_value = (prompt_id, "Old prompt text")

        import appPruebas

        # Realiza la solicitud de prueba
        with appPruebas.app.test_client() as client:
            response = client.put(f'/updatePrompt/{prompt_id}', json={"prompt": new_prompt_text})

        # Verifica que se haya realizado la actualización correctamente
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "Prompt updated successfully"})

class TestSearchUser(unittest.TestCase):

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_search_user_found(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula la ejecución de la consulta y el resultado
        mock_cursor.fetchone.return_value = ('testuser',)  # Simula que se encontró el usuario

        # Realiza una petición GET a la ruta /friends/search con el username
        response = client.get('/friends/search?username=testuser')

        # Verifica que el estado de la respuesta sea 200
        self.assertEqual(response.status_code, 200)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        self.assertEqual(data, {"user": {"username": "testuser"}})

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_search_user_not_found(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula que no se encontró el usuario
        mock_cursor.fetchone.return_value = None

        # Realiza una petición GET a la ruta /friends/search con el username
        response = client.get('/friends/search?username=nonexistentuser')

        # Verifica que el estado de la respuesta sea 404
        self.assertEqual(response.status_code, 404)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        self.assertEqual(data, {"user": None})

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

class TestFollowUser(unittest.TestCase):

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_follow_user_success(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula que no existe la relación de seguimiento
        mock_cursor.fetchone.return_value = None

        # Realiza una petición POST a la ruta /follow con los datos del formulario
        response = client.post('/follow', data={
            'follower_username': 'user1',
            'followee_username': 'user2'
        })

        # Verifica que el estado de la respuesta sea 200
        self.assertEqual(response.status_code, 200)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        self.assertEqual(data, {"status": "Follow successful"})

        # Verifica que se haya insertado la relación en la base de datos
        mock_cursor.execute.assert_called_with(
            "INSERT INTO follows (follower_username, followee_username) VALUES (%s, %s)",
            ('user1', 'user2')
        )

        # Verifica que se haya hecho un commit a la conexión
        mock_connection.commit.assert_called_once()

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_follow_user_already_following(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula que ya existe la relación de seguimiento
        mock_cursor.fetchone.return_value = ('user1', 'user2')

        # Realiza una petición POST a la ruta /follow con los datos del formulario
        response = client.post('/follow', data={
            'follower_username': 'user1',
            'followee_username': 'user2'
        })

        # Verifica que el estado de la respuesta sea 400
        self.assertEqual(response.status_code, 400)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        self.assertEqual(data, {"status": "Already following"})

        # Verifica que no se haya insertado la relación en la base de datos
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM follows WHERE follower_username = %s AND followee_username = %s",
            ('user1', 'user2')
        )

        # Verifica que la conexión no haya hecho un commit
        mock_connection.commit.assert_not_called()

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

class TestGetFriends(unittest.TestCase):

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_get_friends_success(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula la respuesta de la base de datos
        mock_cursor.fetchall.return_value = [
            ('user2',), 
            ('user3',)
        ]

        # Realiza una petición GET a la ruta /friends con el follower_username
        response = client.get('/friends', query_string={'follower_id': 'user1'})

        # Verifica que el estado de la respuesta sea 200
        self.assertEqual(response.status_code, 200)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        self.assertEqual(data, {"friends": [{"username": "user2"}, {"username": "user3"}]})

        # Verifica que se ejecutara la consulta correcta en la base de datos
        mock_cursor.execute.assert_called_once_with(
            """
            SELECT u.username 
            FROM users u
            JOIN follows f ON u.username = f.followee_username
            WHERE f.follower_username = %s
            """, 
            ('user1',)
        )

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_get_friends_missing_follower_username(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Realiza una petición GET a la ruta /friends sin el follower_username
        response = client.get('/friends')

        # Verifica que el estado de la respuesta sea 400
        self.assertEqual(response.status_code, 400)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        self.assertEqual(data, {"status": "Error", "message": "follower_username is required"})

        # Verifica que no se haya llamado a get_connection
        mock_get_connection.assert_not_called()

class TestGetFeed(unittest.TestCase):

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_get_feed_success(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula la respuesta de la base de datos para los amigos
        mock_cursor.fetchall.side_effect = [
            [('user2',), ('user3',)],  # Amigos del usuario
            [(1, 'user2', 'Prompt 1', '2024-09-26', 10), 
             (2, 'user3', 'Prompt 2', '2024-09-25', 5), 
             (3, 'user1', 'My Prompt', '2024-09-24', 20)]  # Prompts de amigos y del usuario
        ]

        # Realiza una petición GET a la ruta /feed con el username
        response = client.get('/feed', query_string={'username': 'user1'})

        # Verifica que el estado de la respuesta sea 200
        self.assertEqual(response.status_code, 200)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        expected_feed = [
            {"id": 1, "username": "user2", "prompt": "Prompt 1", "date": "2024-09-26", "likes": 10},
            {"id": 2, "username": "user3", "prompt": "Prompt 2", "date": "2024-09-25", "likes": 5},
            {"id": 3, "username": "user1", "prompt": "My Prompt", "date": "2024-09-24", "likes": 20},
        ]
        self.assertEqual(data, {"feed": expected_feed})

        # Verifica que se ejecutara la consulta correcta para amigos
        mock_cursor.execute.assert_any_call(
            """
                SELECT followee_username 
                FROM follows 
                WHERE follower_username = %s
            """, 
            ('user1',)
        )

        # Verifica que se ejecutara la consulta correcta para prompts
        mock_cursor.execute.assert_any_call(
            """
                SELECT p.id, p.username, p.prompt, p.date, p.likes 
                FROM prompts p
                WHERE p.username IN %s
                ORDER BY p.date DESC
            """, 
            (('user2', 'user3', 'user1'),)
        )

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

class TestDeletePrompt(unittest.TestCase):

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_delete_prompt_success(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula que el prompt existe
        mock_cursor.fetchone.return_value = (1, 'user1', 'Sample prompt', '2024-09-26', 0)

        # Realiza una petición DELETE a la ruta /deletePrompts/<prompt_id>
        response = client.delete('/deletePrompts/1')

        # Verifica que el estado de la respuesta sea 200
        self.assertEqual(response.status_code, 200)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        self.assertEqual(data, {"status": "Prompt and associated likes deleted successfully"})

        # Verifica que se ejecutaron las consultas correctas
        mock_cursor.execute.assert_any_call(
            "SELECT * FROM prompts WHERE id = %s", 
            (1,)
        )
        mock_cursor.execute.assert_any_call(
            "DELETE FROM likes WHERE prompt_id = %s", 
            (1,)
        )
        mock_cursor.execute.assert_any_call(
            "DELETE FROM prompts WHERE id = %s", 
            (1,)
        )

        # Verifica que se cometió la transacción
        mock_connection.commit.assert_called_once()

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

class TestUpdateUsername(unittest.TestCase):

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_update_username_success(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Datos de entrada para la solicitud
        request_data = {
            "username": "old_username",
            "password": "password123",
            "newUsername": "new_username"
        }

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula que el usuario existe y la contraseña es correcta
        encrypted_password = base64.b64encode(request_data["password"].encode('utf-8')).decode('utf-8')
        mock_cursor.fetchone.side_effect = [("old_username", encrypted_password), None]  # Primero existe el usuario

        # Realiza una petición POST a la ruta /me/updateUsername
        response = client.post('/me/updateUsername', json=request_data)

        # Verifica que el estado de la respuesta sea 200
        self.assertEqual(response.status_code, 200)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        self.assertEqual(data, {"status": "Usuario registrado con éxito"})

        # Verifica que se ejecutaron las consultas correctas
        mock_cursor.execute.assert_any_call(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            ("old_username", encrypted_password)
        )
        mock_cursor.execute.assert_any_call(
            "UPDATE users SET username = %s WHERE username = %s",
            ("new_username", "old_username")
        )

        # Verifica que se cometió la transacción
        mock_connection.commit.assert_called_once()

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_update_username_username_already_exists(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Datos de entrada para la solicitud
        request_data = {
            "username": "old_username",
            "password": "password123",
            "newUsername": "existing_username"
        }

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula que el usuario existe y la contraseña es correcta
        encrypted_password = base64.b64encode(request_data["password"].encode('utf-8')).decode('utf-8')
        mock_cursor.fetchone.side_effect = [("old_username", encrypted_password), ("existing_username", None)]  # Usuario existente

        # Realiza una petición POST a la ruta /me/updateUsername
        response = client.post('/me/updateUsername', json=request_data)

        # Verifica que el estado de la respuesta sea 400
        self.assertEqual(response.status_code, 400)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        self.assertEqual(data, {"error": "Username already exists"})

        # Verifica que se ejecutaron las consultas correctas
        mock_cursor.execute.assert_any_call(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            ("old_username", encrypted_password)
        )
        mock_cursor.execute.assert_any_call(
            "SELECT * FROM users WHERE username = %s",
            ("existing_username",)
        )

        # Verifica que no se ejecutara la consulta de actualización
        mock_cursor.execute.assert_any_call(
            "SET FOREIGN_KEY_CHECKS = 0;"
        )

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

class TestGetMyPrompts(unittest.TestCase):

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_get_my_prompts_success(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Parámetros de la solicitud
        username = "test_user"

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula resultados de la base de datos
        mock_cursor.fetchall.return_value = [
            (1, "test_user", "Prompt 1", "2024-01-01", 5),
            (2, "test_user", "Prompt 2", "2024-01-02", 3)
        ]

        # Realiza una petición GET a la ruta /me/getMyPrompts
        response = client.get('/me/getMyPrompts', query_string={"username": username})

        # Verifica que el estado de la respuesta sea 200
        self.assertEqual(response.status_code, 200)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        expected_data = {
            "results": [
                {"id": 1, "username": "test_user", "prompt": "Prompt 1", "date": "2024-01-01", "likes": 5},
                {"id": 2, "username": "test_user", "prompt": "Prompt 2", "date": "2024-01-02", "likes": 3}
            ]
        }
        self.assertEqual(data, expected_data)

        # Verifica que se ejecutara la consulta correcta
        mock_cursor.execute.assert_called_once_with(
            "SELECT id, username, prompt, date, likes FROM prompts WHERE username = %s",
            (username,)
        )

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_get_my_prompts_no_results(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Parámetros de la solicitud
        username = "test_user"

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula resultados vacíos de la base de datos
        mock_cursor.fetchall.return_value = []

        # Realiza una petición GET a la ruta /me/getMyPrompts
        response = client.get('/me/getMyPrompts', query_string={"username": username})

        # Verifica que el estado de la respuesta sea 200
        self.assertEqual(response.status_code, 200)

        # Verifica que la respuesta tenga resultados vacíos
        data = json.loads(response.data)
        expected_data = {"results": []}
        self.assertEqual(data, expected_data)

        # Verifica que se ejecutara la consulta correcta
        mock_cursor.execute.assert_called_once_with(
            "SELECT id, username, prompt, date, likes FROM prompts WHERE username = %s",
            (username,)
        )

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

class TestGetRandomUsers(unittest.TestCase):

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_get_random_users_success(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula resultados de la base de datos
        mock_cursor.fetchall.return_value = [
            ("user1",), ("user2",),  ("user3",), ("user4",),
            ("user5",), ("user6",), ("user7",), ("user8",),
            ("user9",), ("user10",), ("user11",), ("user12",),
            ("user13",), ("user14",), ("user15",), ("user16",),
            ("user17",), ("user18",), ("user19",), ("user20",)
        ]

        # Realiza una petición GET a la ruta /friends/random
        response = client.get('/friends/random')

        # Verifica que el estado de la respuesta sea 200
        self.assertEqual(response.status_code, 200)

        # Verifica el contenido de la respuesta
        data = json.loads(response.data)
        expected_data = {
            "users": [
                "user1", "user2", "user3", "user4", "user5", 
                "user6", "user7", "user8", "user9", "user10", 
                "user11", "user12", "user13", "user14", "user15", 
                "user16", "user17", "user18", "user19", "user20"
            ]
        }
        self.assertEqual(data, expected_data)

        # Verifica que se ejecutara la consulta correcta
        mock_cursor.execute.assert_called_once_with(
            "SELECT username FROM users ORDER BY RAND() LIMIT 20"
        )

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

    @patch('appPruebas.get_connection')  # Mockea la función get_connection
    def test_get_random_users_no_results(self, mock_get_connection):
        # Crea un cliente de prueba para la aplicación
        import appPruebas
        appPruebas.app.testing = True
        client = appPruebas.app.test_client()

        # Configura el mock para que devuelva un objeto de conexión simulado
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection

        # Configura el cursor simulado
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simula resultados vacíos de la base de datos
        mock_cursor.fetchall.return_value = []

        # Realiza una petición GET a la ruta /friends/random
        response = client.get('/friends/random')

        # Verifica que el estado de la respuesta sea 200
        self.assertEqual(response.status_code, 200)

        # Verifica que la respuesta tenga una lista vacía
        data = json.loads(response.data)
        expected_data = {"users": []}
        self.assertEqual(data, expected_data)

        # Verifica que se ejecutara la consulta correcta
        mock_cursor.execute.assert_called_once_with(
            "SELECT username FROM users ORDER BY RAND() LIMIT 20"
        )

        # Verifica que se cerrara la conexión
        mock_connection.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
