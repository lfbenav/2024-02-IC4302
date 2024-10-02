
import boto3
from langdetect import detect, DetectorFactory
#Conectar al bucket

BUCKET= "2024-02-ic4302-gr1"
ACCESS_KEY= "AKIAQ2VOGXQDTWAX4PUY"
SECRET_KEY= "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"
PREFIX = "spotify/"

#Conexion al bucket
session = boto3.Session(
    aws_access_key_id= ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)

# Crear un cliente de S3
s3 = session.client('s3')

# Descargar archivo CSV desde el bucket
def descargar_archivo_csv(nombre_archivo, bucket, local_path):
    try:
        s3.download_file(bucket, nombre_archivo, local_path)
        print(f"Archivo {nombre_archivo} descargado exitosamente.")
    except Exception as e:
        print(f"Error al descargar el archivo: {e}")

# Listar archivos en el bucket y filtrar solo los archivos CSV
def list_files_in_bucket(bucket, prefix):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    archivos_csv = [content['Key'] for content in response.get('Contents', []) if content['Key'].endswith('.csv')]
    return archivos_csv


# Obtén la lista de archivos CSV en el bucket
# lista_archivos_csv = list_files_in_bucket(BUCKET, PREFIX)
# if lista_archivos_csv:
#     # Descargar el primer archivo CSV
#     archivo_a_descargar = lista_archivos_csv[0]
#     descargar_archivo_csv(archivo_a_descargar, BUCKET, archivo_a_descargar.split('/')[-1])
# else:
#     print("No se encontraron archivos CSV en el bucket.")

DetectorFactory.seed = 0
print(detect("Hola"))
print(detect("""Silver bells have started ringing
 Christmas choirs join their singing
 Little children get a'wishing
 For that jolly hOLA MI NOMBRE ES PEDRUCO St. Nick
 Houses lit up head to toe now
 Little wreaths and trees to show how
 There's a light and joy and hope in
 Every heart that will believe
 Ooh believe
 I'm going to find that childlike wonder
 Hoping that the cold will bring the snow
 Ooh, Christmastime is here
 We're going to sit here by the fire
 Talking about the joys of days of old
 Ooh, Christmastime is here
 Get the pies and cookies baking
 Bing Crosby serenading
 Get the ornaments and angels
 Just right upon the tree
 Christmas Eve is fast approaching
 So I'll keep eyes wide open
 I don't want to miss a moment
 Of the magic in the air
 I'm going to find that childlike wonder
 Hoping that the cold will bring the snow
 Ooh, Christmastime is here
 We're going to sit here by the fire
 Talking about joys of days of old
 Ooh, Christmastime is here"""))
print(detect("This is an example"))