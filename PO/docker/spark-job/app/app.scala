import org.apache.spark.sql.{SparkSession, DataFrame}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.SaveMode

object SparkJob {
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder
      .appName("Crossref Processing")
      .config("spark.master", "local")
      .getOrCreate()

    // Cargar archivos JSON desde el directorio especificado
    val jsonFiles = "/ruta/a/los/archivos/*.json" // Cambia esta ruta a la ubicación de tus archivos JSON
    val df = spark.read.json(jsonFiles)

    // Transformar campos de fecha
    val transformedDF = df.withColumn("message.indexed.date", date_format(col("message.indexed.date-time"), "MM-dd-yyyy"))
      .withColumn("message.created.date", date_format(col("message.created.date-time"), "MM-dd-yyyy"))

    // Agregar campo con nombres de autores
    val withAuthorsDF = transformedDF.withColumn("message.author_names", 
      concat_ws(", ", col("message.author.family"), col("message.author.given")))

    // Agregar campo con títulos de referencias que tienen DOI
    val withReferencesDF = withAuthorsDF.withColumn("message.reference_title", 
      expr("filter(message.reference, x -> x.DOI is not null)").getField("title"))

    // Guardar el resultado en Elasticsearch
    withReferencesDF.write
      .format("org.elasticsearch.spark.sql")
      .option("es.nodes", "localhost")
      .option("es.port", "9200")
      .option("es.resource", "crossref_index/doc")
      .mode(SaveMode.Append)
      .save()

    // Parar la sesión de Spark
    spark.stop()
  }
}