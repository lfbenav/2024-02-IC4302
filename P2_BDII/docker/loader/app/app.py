import os
import csv
from time import sleep
from google.cloud import storage
from pymongo import MongoClient
import pg8000

XPATH = os.getenv('XPATH')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

POSTGRE_HOST = os.getenv('postgre_host')
POSTGRE_USER = os.getenv('postgre_user')
POSTGRE_PASSWORD = os.getenv('postgre_password')
POSTGRE_DBNAME = os.getenv('postgre_dbname')
POSTGRE_PORT = os.getenv('postgre_port')

MONGO_CLIENT = os.getenv('mongo_client')

# Descargar archivos desde Google Cloud Storage
def download_files_from_gcs(bucket_name, destination_folder):
    # Crear cliente de Google Cloud Storage
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # Listar y descargar los archivos del bucket
    blobs = bucket.list_blobs()
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    for blob in blobs:
        file_name = blob.name
        # Filtrar solo archivos .csv
        if not file_name.endswith('.csv'):
            print(f"Omitiendo archivo no relevante: {file_name}")
            continue

        destination_path = os.path.join(destination_folder, file_name)
        # Crear subdirectorios si no existen
        subdirectory = os.path.dirname(destination_path)
        if not os.path.exists(subdirectory):
            os.makedirs(subdirectory)

        print(f"Descargando {file_name} a {destination_path}")
        blob.download_to_filename(destination_path)

# Función para parsear un archivo CSV multilínea
def parse_csv_file(file_path):
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]
    return data

# Función para parsear todos los archivos .csv en una carpeta
def parse_csv_files_in_folder(folder_path):
    all_data = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                print(f"Parseando archivo {file_path}")
                with open(file_path, mode='r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        all_data.append(row)
    return all_data

# Insertar un artista en PostgreSQL
def insert_artist_into_postgres(artist, cursor):
    try:
        # Obtener y limpiar los datos de popularidad
        popularity = artist.get('Popularity')
        if popularity == 'NA' or not popularity:
            popularity = None
        else:
            popularity = float(popularity)  # Convertir a número decimal

        # Inserción en la tabla Artists
        cursor.execute(
            """
            INSERT INTO Artists (artist_name, genres, popularity, link)
            VALUES (%s, %s, %s, %s)
            """,
            (artist['Artist'], artist.get('Genres'), popularity, artist.get('Link'))
        )
        print(f"Artista insertado en PostgreSQL: {artist['Artist']}")

    except Exception as e:
        print(f"Error insertando artista en PostgreSQL {artist['Artist']} con datos: {artist}: {e}")

# Insertar una canción en PostgreSQL
def insert_song_into_postgres(song, cursor):
    try:
        # Verificar si hay un artista relacionado
        cursor.execute("SELECT artist_id FROM Artists WHERE link = %s", (song['ALink'],))
        artist_id = cursor.fetchone()

        # Si no hay artista, artist_id será None
        artist_id = artist_id[0] if artist_id else None

        # Manejo de valores nulos en los demás campos
        song_name = song.get('SName')
        song_link = song.get('SLink')
        lyric = song.get('Lyric')
        language = song.get('language')

        if not (song_name and song_link and lyric and language):
            print(f"Saltando canción con datos faltantes: {song_name}")
            return

        # Inserción en la tabla Songs
        cursor.execute(
            """
            INSERT INTO Songs (artist_id, song_name, song_link, lyric, language)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (artist_id, song_name, song_link, lyric, language)
        )
        print(f"Canción insertada en PostgreSQL: {song_name}")

    except Exception as e:
        print(f"Error insertando canción en PostgreSQL {song['SName']}: {e}")

# Insertar un artista en MongoDB
def insert_artist_into_mongodb(artist, songs, collection):
    try:
        # Crear el documento del artista con las canciones relacionadas
        document = {
            "artist": artist['Artist'],
            "genres": artist.get('Genres'),
            "popularity": artist.get('Popularity'),
            "link": artist.get('Link'),
            "songs": songs
        }

        # Insertar el documento en la colección de MongoDB
        collection.insert_one(document)
        print(f"Artista insertado en MongoDB: {artist['Artist']}")

    except Exception as e:
        print(f"Error insertando artista en MongoDB {artist['Artist']}: {e}")

# Insertar una canción en MongoDB
def insert_song_into_mongodb(song):
    song_document = {
        "song_name": song['SName'],
        "song_link": song['SLink'],
        "lyric": song['Lyric'],
        "language": song['language']
    }
    print(f"Canción insertada en MongoDB: {song_document['song_name']}")  # Agregar el print aquí
    return song_document


# Función que inserta los datos en ambas bases de datos
def insert_data(artists_data, lyrics_data):
    # Conectar a PostgreSQL
    connection = pg8000.connect(
        user=POSTGRE_USER,
        password=POSTGRE_PASSWORD,
        host=POSTGRE_HOST,
        port=POSTGRE_PORT,
        database=POSTGRE_DBNAME
    )
    cursor = connection.cursor()

    # Conectar a MongoDB
    client = MongoClient(MONGO_CLIENT,
                        tls=True,
                        tlsAllowInvalidCertificates=True
    )
    db = client['LyricsDB']
    collection = db['LyricsCollection']

    for artist in artists_data:
        # Insertar artistas en PostgreSQL
        insert_artist_into_postgres(artist, cursor)
        connection.commit()

        # Obtener canciones relacionadas con el artista
        related_songs = [
            song for song in lyrics_data if song['ALink'] == artist['Link']
        ]

        # Insertar canciones en PostgreSQL
        for song in related_songs:
            insert_song_into_postgres(song, cursor)
            connection.commit()

        # Crear canciones para MongoDB
        artist_songs_mongo = [
            insert_song_into_mongodb(song) for song in related_songs
            if song.get('SName') and song.get('SLink') and song.get('Lyric') and song.get('language')
        ]

        # Insertar el artista y sus canciones en MongoDB
        if artist_songs_mongo:
            insert_artist_into_mongodb(artist, artist_songs_mongo, collection)

    cursor.close()
    connection.close()

# Función principal que ejecuta todo el proceso
def run_loader():
    bucket_name = "ic4302-202402"
    destination_folder = XPATH

    # Descargar archivos del bucket
    download_files_from_gcs(bucket_name, destination_folder)

    # Parsear archivo de artistas
    artists_data = parse_csv_file(os.path.join(destination_folder, 'artists-data.csv'))

    # Parsear todos los archivos en la carpeta 'lyrics/'
    lyrics_folder = os.path.join(destination_folder, 'lyrics')
    lyrics_data = parse_csv_files_in_folder(lyrics_folder)

    # Insertar en PostgreSQL y MongoDB
    insert_data(artists_data, lyrics_data)

# Llamar a la función
if __name__ == "__main__":
    print("Ejecutando...")
    run_loader()




























# import os
# import csv
# from time import sleep
# from google.cloud import storage
# from pymongo import MongoClient
# import pg8000

# XPATH = os.getenv('XPATH')
# GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# POSTGRE_HOST = os.getenv('postgre_host')
# POSTGRE_USER = os.getenv('postgre_user')
# POSTGRE_PASSWORD = os.getenv('postgre_password')
# POSTGRE_DBNAME = os.getenv('postgre_dbname')
# POSTGRE_PORT = os.getenv('postgre_port')

# MONGO_CLIENT = os.getenv('mongo_client')

# # Descargar archivos desde Google Cloud Storage
# def download_files_from_gcs(bucket_name, destination_folder):
#     # Crear cliente de Google Cloud Storage
#     client = storage.Client()
#     bucket = client.bucket(bucket_name)
    
#     # Listar y descargar los archivos del bucket
#     blobs = bucket.list_blobs()
#     if not os.path.exists(destination_folder):
#         os.makedirs(destination_folder)

#     for blob in blobs:
#         file_name = blob.name
#         # Filtrar solo archivos .csv
#         if not file_name.endswith('.csv'):
#             print(f"Omitiendo archivo no relevante: {file_name}")
#             continue

#         destination_path = os.path.join(destination_folder, file_name)
#         # Crear subdirectorios si no existen
#         subdirectory = os.path.dirname(destination_path)
#         if not os.path.exists(subdirectory):
#             os.makedirs(subdirectory)

#         print(f"Descargando {file_name} a {destination_path}")
#         blob.download_to_filename(destination_path)

# # Función para parsear un archivo CSV multilínea
# def parse_csv_file(file_path):
#     with open(file_path, mode='r', encoding='utf-8') as csvfile:
#         reader = csv.DictReader(csvfile)
#         data = [row for row in reader]
#     return data

# # Función para parsear todos los archivos .csv en una carpeta
# def parse_csv_files_in_folder(folder_path):
#     all_data = []
#     for root, dirs, files in os.walk(folder_path):
#         for file in files:
#             if file.endswith('.csv'):
#                 file_path = os.path.join(root, file)
#                 print(f"Parseando archivo {file_path}")
#                 with open(file_path, mode='r', encoding='utf-8') as csvfile:
#                     reader = csv.DictReader(csvfile)
#                     for row in reader:
#                         all_data.append(row)
#     return all_data

# # Insertar datos en PostgreSQL
# def insert_into_postgres(artists_data, lyrics_data):
#     try:
#         # Conectar a la base de datos PostgreSQL
#     # TODO PONER EN VARIABLES DE ENTORNO
#         connection = pg8000.connect(
#             user=POSTGRE_USER,
#             password=POSTGRE_PASSWORD,
#             host=POSTGRE_HOST,
#             port=POSTGRE_PORT,
#             database=POSTGRE_DBNAME
#         )
#         cursor = connection.cursor()

#         # Insertar datos de artistas en PostgreSQL
#         for artist in artists_data:
#             try:
#                 # Obtener y limpiar los datos de popularidad
#                 popularity = artist.get('Popularity')
#                 if popularity == 'NA' or not popularity:
#                     popularity = None
#                 else:
#                     popularity = float(popularity)  # Convertir a número decimal

#                 # Inserción en la tabla Artists
#                 cursor.execute(
#                     """
#                     INSERT INTO Artists (artist_name, genres, popularity, link)
#                     VALUES (%s, %s, %s, %s)
#                     """,
#                     (artist['Artist'], artist.get('Genres'), popularity, artist.get('Link'))
#                 )
#                 print(f"Artista insertado: {artist['Artist']}")

#             except Exception as e:
#                 print(f"Error insertando artista {artist['Artist']} con datos: {artist}: {e}")

#         # Confirmar la inserción de artistas
#         connection.commit()

#         # Insertar datos de canciones
#         for song in lyrics_data:
#             try:
#                 # Verificar si hay un artista relacionado
#                 cursor.execute("SELECT artist_id FROM Artists WHERE link = %s", (song['ALink'],))
#                 artist_id = cursor.fetchone()

#                 # Si no hay artista, artist_id será None
#                 artist_id = artist_id[0] if artist_id else None

#                 # Manejo de valores nulos en los demás campos
#                 song_name = song.get('SName') if song.get('SName') else None
#                 song_link = song.get('SLink') if song.get('SLink') else None
#                 lyric = song.get('Lyric') if song.get('Lyric') else None
#                 language = song.get('language') if song.get('language') else None
#                 if song_name == None:
#                     continue
#                 elif song_link == None:
#                     continue
#                 elif lyric == None:
#                     continue
#                 elif language == None:
#                     continue
#                 else:
#                     # Inserción en la tabla Songs
#                     cursor.execute(
#                         """
#                         INSERT INTO Songs (artist_id, song_name, song_link, lyric, language)
#                         VALUES (%s, %s, %s, %s, %s)
#                         """,
#                         (artist_id, song_name, song_link, lyric, language)
#                     )
#                     connection.commit()  # Confirmar después de cada inserción exitosa
#                     print(f"Canción insertada: {song_name}")

#             except Exception as e:
#                 connection.rollback()  # Revertir transacción si hay un error
#                 print(f"Error insertando canción {song.get('SName', 'sin nombre')}: {e}")
#     except Exception as error:
#         print(f"Error en PostgreSQL: {error}")

#     finally:
#         if connection:
#             cursor.close()
#             connection.close()

# # Insertar datos en MongoDB
# def insert_into_mongodb(artists_data, lyrics_data):
#     # Conectar a la base de datos MongoDB (usa variables de entorno si lo prefieres)
#     client = MongoClient(MONGO_CLIENT)
#     db = client['LyricsDB']
#     collection = db['LyricsCollection']

#     for artist in artists_data:
#         try:
#             # Filtrar canciones relacionadas con el artista actual
#             artist_songs = [
#                 {
#                     "song_name": song['SName'],
#                     "song_link": song['SLink'],
#                     "lyric": song['Lyric'],
#                     "language": song['language']
#                 }
#                 for song in lyrics_data
#                 if song['ALink'] == artist['Link']
#                 and song.get('SName')  # Filtrar por canciones que tengan un nombre
#                 and song.get('SLink')  # Filtrar por canciones que tengan un enlace
#                 and song.get('Lyric')  # Filtrar por canciones que tengan letra
#                 and song.get('language')  # Filtrar por canciones que tengan un idioma
#             ]

#             # Si no hay canciones válidas, omitir el artista
#             if not artist_songs:
#                 print(f"Omitiendo artista {artist['Artist']} sin canciones válidas")
#                 continue

#             # Crear el documento del artista
#             document = {
#                 "artist": artist['Artist'],
#                 "genres": artist.get('Genres'),
#                 "popularity": artist.get('Popularity'),
#                 "link": artist.get('Link'),
#                 "songs": artist_songs
#             }

#             # Insertar el documento en la colección de MongoDB
#             collection.insert_one(document)
#             print(f"Artista insertado en MongoDB: {artist['Artist']}")

#         except Exception as e:
#             print(f"Error insertando artista {artist['Artist']} en MongoDB: {e}")

# # Función principal que ejecuta todo el proceso
# def run_loader():
#     bucket_name = "ic4302-202402"
#     destination_folder = XPATH

#     # Descargar archivos del bucket
#     download_files_from_gcs(bucket_name, destination_folder)

#     # Parsear archivo de artistas
#     artists_data = parse_csv_file(os.path.join(destination_folder, 'artists-data.csv'))

#     # Parsear todos los archivos en la carpeta 'lyrics/'
#     lyrics_folder = os.path.join(destination_folder, 'lyrics')
#     lyrics_data = parse_csv_files_in_folder(lyrics_folder)

#     # Insertar en PostgreSQL
#     insert_into_postgres(artists_data, lyrics_data)

#     # Insertar en MongoDB
#     insert_into_mongodb(artists_data, lyrics_data)

# # Llamar a la función
# if __name__ == "__main__":
#     print("Ejecutando...")
#     run_loader()

