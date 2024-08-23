# Usar la imagen base de Spark
FROM bitnami/spark:3.5.1

# Directorio de trabajo
WORKDIR /app

# Copiar archivos de la aplicación
COPY app /app

# Establecer la codificación como UTF-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Agregar las dependencias de Elasticsearch
COPY app/elasticsearch-spark-30_2.12-8.14.3.jar /opt/bitnami/spark/jars/

# Comando para ejecutar tu aplicación directamente desde el archivo .scala
CMD ["spark-shell", "-i", "/app/app.scala"]
