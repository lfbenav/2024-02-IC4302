import org.apache.spark.SparkContext
import org.apache.spark.SparkConf
import org.apache.spark.sql.SparkSession
import org.elasticsearch.spark.sql._
import org.apache.spark.sql.functions._
import scala.util.{Try, Success, Failure}
import org.apache.spark.sql.DataFrame


// Intentar detener instancias previas de Spark
// Esto es útil para evitar conflictos con sesiones anteriores que pueden estar activas.
val stopPreviousInstances = Try {
  SparkContext.getOrCreate().stop()
  SparkSession.builder().getOrCreate().stop()
}

// Verifica si se logró detener las instancias previas exitosamente
stopPreviousInstances match {

  case Success(_) => println("Instancias previas de Spark detenidas exitosamente.")
  case Failure(e) => println(s"Error al detener instancias previas de Spark: ${e.getMessage}")
}

// Configuración de Spark
val conf = new SparkConf()
  .setAppName("Spark Elasticsearch Job")
  .set("es.index.auto.create", "true")
  .set("es.nodes", "http://ic4302-es-http:9200/")
  .set("es.net.http.auth.user", "elastic")
  .set("es.net.http.auth.pass", System.getenv("ELASTIC_PASS"))
  .set("es.port", "9200")
  .set("es.nodes.wan.only", "true")


// Crear un nuevo SparkContext utilizando la configuración definida previamente
val sc = new SparkContext(conf)

// Crear una nueva SparkSession utilizando la configuración del SparkContext
val spark = SparkSession.builder().config(sc.getConf).getOrCreate()

// Leer el archivo JSON
val tmpData = Try {
  // Imprime un mensaje indicando que se está intentando leer el archivo JSON
  println("Attempting to read JSON file from /data")
  // Lee el archivo JSON ubicado en la ruta /data y lo carga en un DataFrame
  spark.read.json("/data")
}

tmpData match {
  case Success(data) => 
    println("Archivo JSON leído exitosamente.")
    data.printSchema()  // Imprime el esquema del DataFrame
    data.show(false)    // Muestra algunas filas del DataFrame
  case Failure(e) => 
    println(s"Error al leer el archivo JSON: ${e.getMessage}")
    e.printStackTrace()
    sc.stop()
    spark.stop()
    sys.exit(1)
}

// Aplicar transformaciones
// Intentar aplicar varias transformaciones al DataFrame temporal 'tmpData' y capturar cualquier error que pueda ocurrir

val transformedData: Try[DataFrame] = tmpData.flatMap { data =>
  Try {
    data
       // Crear una nueva columna 'message.indexed.date' a partir de 'message.indexed.date-time'
      // Si 'message.indexed.date-time' no es nulo, convierte su valor a formato 'yyyy-MM-dd', de lo contrario, establece la columna en null
      .withColumn("message.indexed.date", 
                  when(col("message.indexed.date-time").isNotNull, 
                       date_format(col("message.indexed.date-time").cast("timestamp"), "yyyy-MM-dd"))
                  .otherwise(lit(null)))
      // Crear una nueva columna 'message.created.date' a partir de 'message.created.date-time'
      // Si 'message.created.date-time' no es nulo, convierte su valor a formato 'yyyy-MM-dd', de lo contrario, establece la columna en null
      .withColumn("message.created.date", 
                  when(col("message.created.date-time").isNotNull, 
                       date_format(col("message.created.date-time").cast("timestamp"), "yyyy-MM-dd"))
                  .otherwise(lit(null)))
       // Crear una nueva columna 'message.published.date' a partir de 'message.published-print.date-parts'
      // Si 'message.published-print.date-parts' no es nulo, concatena el año y mes, asignando el día como '01', y convierte el valor a formato 'yyyy-MM-dd', de lo contrario, establece la columna en null
      .withColumn("message.published.date", 
                  when(col("message.published-print.date-parts").isNotNull, 
                       date_format(
                         concat(
                           col("message.published-print.date-parts")(0)(0).cast("string"), 
                           lit("-"), 
                           col("message.published-print.date-parts")(0)(1).cast("string"), 
                           lit("-01")
                         ).cast("timestamp"), 
                         "yyyy-MM-dd"
                       )
                  )
                  .otherwise(lit(null))
                )
      // Crear una nueva columna 'message.author_names' concatenando los apellidos y nombres de los autores
      // Si 'message.author' no es nulo, transforma la lista de autores en un formato 'Apellido, Nombre', de lo contrario, establece la columna en null
      .withColumn("message.author_names", 
                  when(col("message.author").isNotNull, 
                       expr("transform(message.author, x -> concat(x.family, ', ', x.given))"))
                  .otherwise(lit(null)))
      // Crear una nueva columna 'message.reference_title' que filtra y transforma los elementos de 'message.reference' para obtener solo los DOIs no nulos
      // Si 'message.reference' no es nulo, aplica una transformación para filtrar las referencias que tengan un DOI, de lo contrario, establece la columna en null
      .withColumn("message.reference_title", 
                  when(col("message.reference").isNotNull, 
                       expr("filter(transform(message.reference, x -> if(x.DOI is not null, x.DOI, null)), x -> x is not null)"))
                  .otherwise(lit(null)))
  }
}
// Manejar el resultado de las transformaciones
transformedData match {
  // Si las transformaciones se aplicaron con éxito, muestra los datos resultantes en la consola
  case Success(data) => data.show(false)
  // Si hubo un error al aplicar las transformaciones
  case Failure(e) => 
    println(s"Error al aplicar las transformaciones: ${e.getMessage}")
    e.printStackTrace()
    sc.stop()
    spark.stop()
    sys.exit(1)
}

// Guardar los resultados en Elasticsearch
// Intentar guardar los datos transformados en un índice de Elasticsearch y capturar cualquier error que pueda ocurrir
val saveResult = transformedData.flatMap {
  case data =>
    Try {
      // Guardar el DataFrame en Elasticsearch en el índice "data"
      data.saveToEs("data")
    }
}
// Verificar si el guardado fue exitoso o si ocurrió un error
saveResult match {
  // Si los datos se guardaron exitosamente, imprime un mensaje de éxito
  case Success(_) => println("Datos guardados en Elasticsearch exitosamente.")
  // Si ocurrió un error durante el guardado, imprime un mensaje con la descripción del error y la traza de la excepción
  case Failure(e) => 
    println(s"Error al guardar los resultados en Elasticsearch: ${e.getMessage}")
    e.printStackTrace()
}

// Detener el contexto de Spark
// Intentar detener el SparkContext y SparkSession, y capturar cualquier error que pueda ocurrir

val stopContext = Try {
  sc.stop()
  spark.stop()
}
// Verificar si el contexto de Spark se detuvo exitosamente o si ocurrió un error
stopContext match {
  // Si el contexto de Spark se detuvo sin problemas, imprime un mensaje de éxito
  case Success(_) => println("Contexto de Spark detenido exitosamente.")
  // Si ocurrió un error al detener el contexto de Spark, imprime un mensaje con la descripción del error
  case Failure(e) => println(s"Error al detener el contexto de Spark: ${e.getMessage}")
}
