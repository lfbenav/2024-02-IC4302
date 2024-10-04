import unittest
from flask import json
from app import app, model 

class HuggingFaceAPI_Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app.test_client()
        cls.app.testing = True

    def test_index(self):
        """Prueba del endpoint de la raíz"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('utf-8'), "Funciona correctamente!")

    def test_status(self):
        """Prueba del endpoint /status"""
        response = self.app.get('/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('embedding', data)
        self.assertIn('text', data)
        self.assertEqual(data['text'], "This is my best example. I'll play well today \n John is my name")
        self.assertTrue(isinstance(data['embedding'], list))

    def test_generate_vector(self):
        """Prueba del endpoint /encode"""
        response = self.app.post('/encode', json={"text": "Texto de Prueba"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('embeddings', data)
        self.assertIn('text', data)
        self.assertEqual(data['text'], "Texto de Prueba")
        self.assertTrue(isinstance(data['embeddings'], list))

    def test_generate_vector_no_text(self):
        """Prueba del endpoint /encode sin el campo 'text'"""
        response = self.app.post('/encode', json={})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], "El campo 'text' es requerido")

if __name__ == '__main__':
    unittest.main()
