import os
from pymongo import MongoClient, TEXT
MONGO_CLIENT = "mongodb+srv://AlexNaranjo:S4vpz219@cluster0.vqij1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(
            MONGO_CLIENT,
            tls=True,
            tlsAllowInvalidCertificates=True
        )
mongo_db = mongo_client['LyricsDB']
lyrics_collection = mongo_db['LyricsCollection']


def funcion(query):
    # Realizar búsqueda en MongoDB usando el pipeline de búsqueda
    search_pipeline = [
        {
            "$search": {
                "index": "default",  # Nombre del índice de búsqueda
                "text": {
                    "query": query,
                    "path": ["artist", "genres", "songs.song_name", "songs.lyric", "songs.language", "popularity"]  # Solo buscar en estos campos
                }
            }
        },
        {
            "$project": {
                "artist": 1,
                "genres": 1,
                "popularity": 1,
                "link": 1,  # Incluir el enlace del artista
                "score": {"$meta": "searchScore"},  # Relevancia de la búsqueda
                "matching_songs": {
                    "$filter": {
                        "input": "$songs",
                        "as": "song",
                        "cond": {
                            "$or": [
                                {"$regexMatch": {"input": "$$song.song_name", "regex": query, "options": "i"}},
                                {"$regexMatch": {"input": "$$song.lyric", "regex": query, "options": "i"}}
                            ]
                        }
                    }
                }
            }
        },
        {
            "$match": {
                "matching_songs": {"$ne": []}  # Filtrar documentos sin canciones coincidentes
            }
        }
    ]

    results = list(lyrics_collection.aggregate(search_pipeline))

    # Procesar los resultados
    processed_results = []
    for doc in results:
        artist = doc['artist']
        genres = doc['genres']
        popularity = doc['popularity']
        artist_link = doc['link']  # Link del artista
        score = doc['score']
        for song in doc['matching_songs']:
            processed_results.append({
                "artist": artist,
                "genres": genres,
                "song_name": song['song_name'],
                "lyric": song['lyric'],
                "language": song.get('language', "Unknown Language"),
                "popularity": popularity,
                "artist_link": artist_link,  # Añadir link del artista
                "song_link": song['song_link'],  # Añadir link de la canción
                "score": score  # Relevancia de la búsqueda
            })

    results = processed_results

    for result in results:
        print("*")
        print(f"Artist: {result['artist']}")
        print(f"Genres: {result['genres']}")
        print(f"Popularity: {result['popularity']}")
        print(f"Score: {result['score']}")
        print(f"Song Name: {result['song_name']}")
        try:
            print(f"Lyric:\n{result['lyric']}")
        except UnicodeEncodeError:
            print("Error al imprimir la letra de la canción")
        print(f"Language: {result.get('language', 'Unknown Language')}")
        print(f"Artist Link: {result['artist_link']}")
        print(f"Song Link: {result['song_link']}")
        print("---------------------------------------------------------------------------------------")


# Ejemplo de búsqueda
search_query = "Wish you were here"  # Cambia esto a lo que quieras buscar
#search_lyrics(search_query)


genres_result_temp = lyrics_collection.distinct("genres")

generos_unicos = set()

# Separar los géneros y agregarlos al conjunto
for genero in genres_result_temp:
    generos_separados = genero.split('; ')
    for g in generos_separados:
        generos_unicos.add(g.strip())  # Usar strip() para eliminar espacios en blanco

# Convertir el conjunto de vuelta a una lista (opcional)
genres_result = list(generos_unicos)

# Imprimir los géneros únicos
print(genres_result)





#print(lyrics_collection.distinct("songs.language"))

languages_result_temp = lyrics_collection.distinct("songs.language")

languages_result = []
for lang in languages_result_temp:
    if(len(lang)==2):
        languages_result.append(lang)

# Intentar convertir cada lenguaje a cadena
#for lang in languages_result:
#    print(lang)

# funcion(search_query)