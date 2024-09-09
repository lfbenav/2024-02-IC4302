get_elasticsearch_password() {
  echo "Obteniendo la contraseña de Elasticsearch desde el secreto de Kubernetes..."
  elastic_pass=$(kubectl get secret ic4302-es-elastic-user -o jsonpath='{.data.elastic}' | base64 --decode)
  
  sleep 10

  if [ -z "$elastic_pass" ]; then
    echo "Error: No se pudo obtener la contraseña del secreto."
    exit 1
  else
    echo "Contraseña obtenida exitosamente."
    echo $elastic_pass
  fi
}

# Función para obtener la IP del nodo de Kubernetes
get_node_ip() {
  echo "Obteniendo la IP del nodo de Kubernetes..."
  node_ip=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
  
  if [ -z "$node_ip" ]; then
    echo "Error: No se pudo obtener la IP del nodo."
    exit 1
  else
    echo "IP del nodo obtenida: $node_ip"
  fi
}
cargar_datos() {
  # Ruta de los archivos JSON
  archivo_movies="./movies_bulk.json"
  archivo_ratings="./ratings_bulk.json"

  # Verificar si los archivos existen
  if [ ! -f "$archivo_movies" ]; then
    echo "Error: El archivo $archivo_movies no existe."
    exit 1
  fi

  if [ ! -f "$archivo_ratings" ]; then
    echo "Error: El archivo $archivo_ratings no existe."
    exit 1
  fi

  # Cargar el archivo JSON en el índice 'movies'
  echo "Cargando datos en el índice movies desde $archivo_movies..."
  response=$(curl -u "elastic:$elastic_pass" -s -o response_output_movies.txt -w "%{http_code}" \
    -X POST "$elastic_url/movies/_bulk?pretty" \
    -H "Content-Type: application/json" \
    --data-binary "@$archivo_movies")

  # Verificar si la carga fue exitosa
  if [ "$response" -eq 200 ] || [ "$response" -eq 201 ]; then
    echo "Datos de movies cargados exitosamente."
  else
    echo "Error al cargar los datos de movies. Código de respuesta: $response."
    echo "Contenido de la respuesta:"
    cat response_output_movies.txt
  fi

  # Cargar el archivo JSON en el índice 'ratings'
  echo "Cargando datos en el índice ratings desde $archivo_ratings..."
  response=$(curl -u "elastic:$elastic_pass" -s -o response_output_ratings.txt -w "%{http_code}" \
    -X POST "$elastic_url/ratings/_bulk?pretty" \
    -H "Content-Type: application/json" \
    --data-binary "@$archivo_ratings")

  # Verificar si la carga fue exitosa
  if [ "$response" -eq 200 ] || [ "$response" -eq 201 ]; then
    echo "Datos de ratings cargados exitosamente."
  else
    echo "Error al cargar los datos de ratings. Código de respuesta: $response."
    echo "Contenido de la respuesta:"
    cat response_output_ratings.txt
  fi
}
crear_indice() {
  # Realizar port-forwarding a Elasticsearch desde Kubernetes al puerto 9200 local
  echo "Realizando port-forwarding a Elasticsearch..."
  
  # Ejecuta port-forward en segundo plano
  kubectl port-forward svc/ic4302-es-http 9200:9200 &

  # Guardar el ID del proceso de port-forward para detenerlo después
  port_forward_pid=$!

  # Verificar si el proceso de port-forwarding se inició correctamente
  if ps -p $port_forward_pid > /dev/null
  then
    echo "Port-forwarding iniciado correctamente (PID: $port_forward_pid)."
  else
    echo "Error: Fallo al iniciar el port-forwarding."
    exit 1
  fi

  # Esperar unos segundos para que el port-forwarding se establezca
  sleep 60

  # URL de Elasticsearch en el puerto local 9200
  elastic_url="http://localhost:9200"

  # Crear los indices movies y ratings  
  # Nombre del índice 
  index_name_movies="movies"
  index_name_ratings="ratings"

  # Definir el esquema del índice (mapping)
  index_mapping_movies='{
    "mappings": {
      "properties": {
        "movieId": {
          "type": "integer"
        },
        "title": {
          "type": "text"
        },
        "genres": {
          "type": "text"
        }
      }
    }
  }'

  index_mapping_ratings='{
    "mappings": {
      "properties": {
        "userId": {
          "type": "integer"
        },
        "movieId": {
          "type": "integer"
        },
        "rating": {
          "type": "float"
        },
        "timestamp": {
          "type": "long"
        }
      }
    }
  }'

  # Crear el índice usando curl con autenticación básica
  echo "Intentando crear el índice $index_name_movies en Elasticsearch..."
  
  # Utiliza la contraseña de Elasticsearch almacenada en la variable de entorno elastic_pass
  response=$(curl -u "elastic:$elastic_pass" -s -o response_output.txt -w "%{http_code}" \
    -X PUT "$elastic_url/$index_name_movies" \
    -H "Content-Type: application/json" \
    -d "$index_mapping_movies")

  # Verificar si la creación fue exitosa
  if [ "$response" -eq 200 ] || [ "$response" -eq 201 ]; then
    echo "Índice $index_name_movies creado exitosamente."
  else
    echo "Error al crear el índice $index_name_movies. Código de respuesta: $response."
    echo "Contenido de la respuesta:"
    cat response_output.txt
  fi

  # Crear el índice usando curl con autenticación básica
  echo "Intentando crear el índice $index_name_ratings en Elasticsearch..."
  
  # Utiliza la contraseña de Elasticsearch almacenada en la variable de entorno elastic_pass
  response=$(curl -u "elastic:$elastic_pass" -s -o response_output.txt -w "%{http_code}" \
    -X PUT "$elastic_url/$index_name_ratings" \
    -H "Content-Type: application/json" \
    -d "$index_mapping_ratings")

  # Verificar si la creación fue exitosa
  if [ "$response" -eq 200 ] || [ "$response" -eq 201 ]; then
    echo "Índice $index_name_ratings creado exitosamente."
  else
    echo "Error al crear el índice $index_name_ratings. Código de respuesta: $response."
    echo "Contenido de la respuesta:"
    cat response_output.txt
  fi


  # Cargar datos en los indices
  cargar_datos


}

kubectl create secret generic ic4302-es-elastic-user \
    --from-literal=elastic=1234 \
    --dry-run=client -o yaml | kubectl apply -f -
echo MTIzNA== | base64 --decode

get_elasticsearch_password
crear_indice