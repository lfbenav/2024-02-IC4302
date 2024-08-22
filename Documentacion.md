# Documentación del Proyecto Opcional

Andrés Bonilla Solano - 2023101220  
Luis Fernando Benavides Villegas - 2023072689  
Juan Diego Jiménez - 2019199111  
Alex Naranjo - 2023063599 

## **Instrucciones para ejecutar el proyecto:**
Para ejecutar el proyecto...
## **Pruebas realizadas:** 

Revisión de pods para verificar si están funcionando.
Para las pruebas unitarias solo hay que ejecutar el proyecto y luego revisar en los pod logs si las pruebas tuvieron exito. Esto se verá parte por parte en el siguiente apartado donde se mostraran los resultados de las pruebas unitarias.

## **Resultados de las pruebas unitarias:**
Para las pruebas unitarias, se utilizó la librería de unittest que viene incluida en las versiones más recientes de python. En caso de que las pruebas sean existosas en los logs del pods debería aparecer "RAN {numero_de_tests} in {tiempo_de_ejecución}" y luego un "OK". En caso contrario en lugar del "OK", aparece FAILED (failures={numero_de_fails}) y indica en que linea falló y que tipo de error ocurrió.  
En la siguiente imagen, está el resultado de las pruebas unitarias del s3-spider. Para esta parte del proyecto, se usaron cinco funciones principales: **list_s3_objects, download_s3_object, create_jobs, save_jobs_to_db, publish_jobs_to_rabbitmq.** Para estas funciones se creó un entorno simulado para el bucket y también se utilizaron datos de prueba que se asemejan a los del proyecto. Asimismo, se utilizó la librería **moto** para simular los servicios de AWS y el módulo mock de unit test para simular objetos y partes de las funciones.

 ![alt text](image-1.png) 

 En el caso del downloader, se intentó hacer un unit test pero había un elemento de la función de procesar mensajes que no se podía imitar utilizando las librerías mencionadas anteriormente. Sin embargo al ejecutar el proyecto, en los pods logs aparece que se estan esperando mensajes por lo que se garantizá que esta funcionando correctamente.
 Para el spark-job no se hicieron pruebas unitarias como tal ya que es un archivo .scala. 

## **Recomendaciones y conclusiones (al menos 10 de cada una):**

### Recomendaciones:

- Para los unit test, hacer un archivo aparte e importar los módulos necesarios.
- Utilizar las librerías unittest y moto para las pruebas unitarias. 
- Hacer las pruebas localmente y luego en Docker.
- 

### Concluciones:

+ Para el componente S3-spider del proyecto. Concluimos que ha sido de suma importancia para la automatización del procesamiento de datos ya que interactua eficientemente con el S3 bucket. Este componente no solo crea una lista de los objetos que se encuentran en el bucket sino que también permite descargarlos para luego crear jobs para organizar los DOIs. Finalmente, se guardan los jobs en la base de datos y se publican a una cola de rabbitmq. Este flujo es ideal ya que se manejan grandes cantidades de datos.
+ En el caso del componente downloader del proyecto ...
+ Por otro lado, el componente spark-job esta desarrollado en ...
+ El uso de unit tests es fundamental para garantizar el funcionamiento individual de las diferentes partes del proyecto. Con la implementación de pruebas unitarias se pueden localizar diferentes errores y verificar que todo este funcionando como debería. Además, hace que sea más fácil revisar el código y posteriormente mantenerlo.
+ También, para concluir con el tema de los unit tests, hay dos librerías que fueron clave para realizar las pruebas. Estas son: **unit test y moto.** El módulo de unit test ofrece herramientas para construir y ejecutar pruebas. Para probar un caso lo que se hace es crear una clase que subclasifique unittest.TestCase. Algunas funciones para ver si se estan obteniendo los resultados esperados son: **assertEqual(), assertTrue(),   assertFalse() y assertRaises().** Para la librería de moto en el proyecto, lo que se realizó fue una simulación de los servicios de AWS. Este módulo permite simular varios servicios usando decoradores y se suele utilizar para las pruebas unitarias.
+ En este proyecto todo debía estar en contenedores de Docker. El trabajo que hace Docker es empaquetar las aplicaciones que se van a usar en contenedores. En este caso se usó la herramienta llamada Docker Desktop que es una aplicación que proporciona todo el entorno necesario para desarrollar contenedores localmente y posteriormente ejecutarlos en diferentes sistemas operativos como pueden ser Linux o Windows.
+ Junto con Docker se utilizó Kubernetes. Lo que hace Kubernetes es manejar o orquestar los contenedores creados por Docker. En este proyecto, se utilizó Lens para interactuar con los clusters de Kubernetes. En Lens, se pueden revisar los servicios y los pods que estan corriendo durante la ejecución del proyecto. Se pueden ver los pods logs para detectar fallos o revisar si todo está funcionando como debería. En caso de que un Pod de error y no funcione, en Lens se podrá ver el error detalladamente.
+ Una herramienta importante que se usó en este proyecto fue Helm. Helm nos permite administrar paquetes para Kubernetes. Con los Helm charts se pueden instalar y actualizar aplicaciones en Kubernetes de manera sencila. Además, parte del trabajo de los helm charts es desplegar los contenedores que son creados por docker en un cluster de Kubernetes. Durante este proyecto, se utilizó Helm Chartas para instalar MariaDB, RabbitMQ, ElasticSearch y Kibana.
+ Este proyecto está automatizado en su totalidad por herramientas mencionadas anteriormente, Docker y Helm Charts ...  
+ 

● La documentación debe cubrir todos los componentes implementados o instalados/configurados,
en caso de que algún componente no se encuentre implementado, no se podrá documentar y
tendrá un impacto en la completitud de la documentación.

## Referencias bibliográficas  

Alyssa Shames(30 de Noviembre de 2023). *Docker and Kubernetes: How They Work Together*. Docker. https://www.docker.com/blog/docker-and-kubernetes/ 

Cloud Native Computing Foundation(2024). *Uso de Helm*. Helm Docs. 
https://helm.sh/es/docs/intro/using_helm/ 

Python(2024). *unittest — Unit testing framework.* The Python Standard Library
https://docs.python.org/3/library/unittest.html 

Steve Pulec(2015). *Getting Started with Moto*. Moto. https://docs.getmoto.org/en/latest/docs/getting_started.html 
