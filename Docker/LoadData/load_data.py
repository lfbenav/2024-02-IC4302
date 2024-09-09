import pandas as pd
import pymysql
import psycopg2
import os

# Configuración de las bases de datos
#Configuración de mariadb
mariadb_config = {
    'host': os.getenv('maria_host'),
    'user': os.getenv('maria_user'),
    'password': os.getenv('maria_password'),
    'database': os.getenv('maria_database')
}

#Configuración de postgresql
postgresql_config = {
    'host': os.getenv('postgre_host'),
    'user': os.getenv('postgre_user'),
    'password': os.getenv('postgre_password'),
    'dbname': os.getenv('postgre_dbname')
}

print("Haciendo conexión con mariadb")
connectionMariadb = pymysql.connect(**mariadb_config)
cursorMariadb = connectionMariadb.cursor()

print("Haciendo conexión con postgresql")
connectionPostgresql = psycopg2.connect(**postgresql_config)
cursorPostgresql = connectionPostgresql.cursor()

# ----------------------- MariaDb -----------------------
def load_csv_to_mariadb(file_path, table_name, columns):
    df = pd.read_csv(file_path)
    
    # Crear la consulta SQL para insertar datos
    column_names = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(columns))
    sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
    
    # Insertar cada fila en la base de datos
    for row in df.itertuples(index=False):
        cursorMariadb.execute(sql, row)
    
    connectionMariadb.commit()

# ----------------------- PostgreSql -----------------------
def load_csv_to_postgresql(file_path, table_name, columns):
    df = pd.read_csv(file_path)
    
    # Crear la consulta SQL para insertar datos
    column_names = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(columns))
    sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
    
    # Insertar cada fila en la base de datos
    for row in df.itertuples(index=False):
        cursorPostgresql.execute(sql, row)
    
    connectionPostgresql.commit()

# ----------------------- Cargar Datos -----------------------
try:
    print("Cargando datos")
    # Cargar datos desde archivos CSV
    load_csv_to_mariadb('movies.csv', 'movies', ['movieId', 'title', 'genres'])
    load_csv_to_mariadb('ratings.csv', 'ratings', ['userId', 'movieId', 'rating', 'timestamp'])

    # Cerrar la conexión
    cursorMariadb.close()
    connectionMariadb.close()

    print("Datos cargados exitosamente en MariaDb.")
except pymysql.err.IntegrityError as e:
    print(f"Otro error de integridad: {e}")

try:
    # Cargar datos desde archivos CSV
    load_csv_to_postgresql('movies.csv', 'movies', ['movieId', 'title', 'genres'])
    load_csv_to_postgresql('ratings.csv', 'ratings', ['userId', 'movieId', 'rating', 'timestamp'])

    # Cerrar la conexión
    cursorPostgresql.close()
    connectionPostgresql.close()

    print("Datos cargados exitosamente en PostgreSql.")
except psycopg2.errors.UniqueViolation as e:
    print(f"Otro error de integridad: {e}")

# import time
# while True:
#     print("waiting")
#     time.sleep(20)

