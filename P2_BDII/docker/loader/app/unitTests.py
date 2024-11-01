import unittest
from unittest.mock import patch, MagicMock
import os
import app

class TestLoader(unittest.TestCase):

    @patch('app.storage.Client')
    def test_download_files_from_gcs(self, mock_storage_client):
        # Simulación del comportamiento 
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.name = 'test.csv'
        mock_bucket.list_blobs.return_value = [mock_blob]
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        # Folder de destino (simulado)
        destination_folder = 'test_folder'
        app.download_files_from_gcs('test_bucket', destination_folder)

        # Verificar que se llama a download_to_filename
        mock_blob.download_to_filename.assert_called_once_with(os.path.join(destination_folder, 'test.csv'))

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='Artist,Genres,Popularity,Link\nArtist1,Genre1,100,http://link1\n')
    def test_parse_csv_file(self, mock_file):
        # Llamada a la función
        result = app.parse_csv_file('dummy_path.csv')
        # Resultado esperado:
        expected_result = [{'Artist': 'Artist1', 'Genres': 'Genre1', 'Popularity': '100', 'Link': 'http://link1'}]
        
        # Revisar que ambos resultados sean iguales y que se realizo la llamada utilizando el path: dummy_path.csv
        self.assertEqual(result, expected_result)
        mock_file.assert_called_once_with('dummy_path.csv', mode='r', encoding='utf-8')

    @patch('app.os.walk')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='SName,SLink,Lyric,language\nSong1,http://link1,lyric1,en\n')
    def test_parse_csv_files_in_folder(self, mock_open, mock_os_walk):
        # Se simula el valor de retorno
        mock_os_walk.return_value = [('folder', ('subfolder',), ('file.csv',))]
        
        result = app.parse_csv_files_in_folder('dummy_folder')
        expected_result = [{'SName': 'Song1', 'SLink': 'http://link1', 'Lyric': 'lyric1', 'language': 'en'}]
        
        # Revisar que ambos resultados sean iguales y que se realizo la llamada utilizando el path definido
        self.assertEqual(result, expected_result)
        mock_open.assert_called_once_with('folder\\file.csv', mode='r', encoding='utf-8')

class TestInsertData(unittest.TestCase):

    @patch('app.pg8000.connect')
    @patch('app.MongoClient')
    @patch('app.insert_artist_into_postgres')
    @patch('app.insert_song_into_postgres')
    @patch('app.insert_artist_into_mongodb')
    def test_insert_data(self, mock_insert_artist_mongo, mock_insert_song_postgres, mock_insert_artist_postgres, mock_mongo_client, mock_pg_connect):
        mock_cursor = MagicMock()
        mock_pg_connect.return_value.cursor.return_value = mock_cursor

        # Datos de prueba
        artists_data = [{'Artist': 'Artist1', 'Genres': 'Genre1', 'Popularity': '100', 'Link': 'http://link1'}]
        lyrics_data = [{'SName': 'Song1', 'SLink': 'http://link1', 'Lyric': 'lyric1', 'language': 'en', 'ALink': 'http://link1'}]

        # Simular que el artista no existe en MongoDB
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None  # Se simula el valor de retorno para que no se encuentra el artista
        mock_mongo_client.return_value['LyricsDB']['LyricsCollection'] = mock_collection

        # Llamada a la función que se está probando
        app.insert_data(artists_data, lyrics_data)

        # Verificar inserciones en PostgreSQL
        mock_insert_artist_postgres.assert_called_once_with(artists_data[0], mock_cursor)
        mock_insert_song_postgres.assert_called_once_with(lyrics_data[0], mock_cursor)

    @patch('app.MongoClient')
    @patch('app.pg8000.connect')
    @patch('app.insert_artist_into_postgres')
    @patch('app.insert_song_into_postgres')
    @patch('app.insert_artist_into_mongodb')
    def test_insert_existing_artist(self, mock_insert_artist_mongo, mock_insert_song_postgres, mock_insert_artist_postgres, mock_pg_connect, mock_mongo_client):
        mock_cursor = MagicMock()
        mock_pg_connect.return_value.cursor.return_value = mock_cursor

        artists_data = [{'Artist': 'Artist1', 'Genres': 'Genre1', 'Popularity': '100', 'Link': 'http://link1'}]
        lyrics_data = [{'SName': 'Song1', 'SLink': 'http://link1', 'Lyric': 'lyric1', 'language': 'en', 'ALink': 'http://link1'}]

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = {'artist': 'Artist1'}  # Artista ya existe
        mock_mongo_client.return_value['LyricsDB']['LyricsCollection'] = mock_collection

        app.insert_data(artists_data, lyrics_data)

        # Verifica que no se insertó en MongoDB
        mock_insert_artist_mongo.assert_not_called()
    
    @patch('app.MongoClient')  # Patch de MongoClient
    def test_insert_new_artist(self, mock_mongo_client):
        # Configurar el mock de la colección
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_mongo_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        # Datos de prueba para un nuevo artista
        artist_data = {
            'Artist': 'Nuevo Artista',
            'Genres': 'Pop',
            'Popularity': '75', 
            'Link': 'http://example.com/nuevo-artista'
        }

        # Datos de prueba para canciones
        songs = ['Canción 1', 'Canción 2']  

        # Llamada a la función que se está probando
        app.insert_artist_into_mongodb(artist_data, songs, mock_collection)

        # Verificar que se haya ejecutado la inserción en la colección
        mock_collection.insert_one.assert_called_once_with({
            'artist': artist_data['Artist'],  
            'genres': artist_data['Genres'],
            'popularity': artist_data['Popularity'],  
            'link': artist_data['Link'],
            'songs': songs  
        })

if __name__ == '__main__':
    unittest.main()
