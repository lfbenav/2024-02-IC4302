# Pruebas y Resultados

Las pruebas se realizaron utilizando Gatling. Para la ejecución de las mismas se descargó una **demo** en la página oficial. Esta demo maneja los paquetes utilizando maven. Además, el dataset que se utilizó es de películas y sus ratings.

## MariaDB

### Primera prueba:
```Java
public class MariaDBLoadTest extends Simulation {

    // Definición de los diferentes endpoints
    private final String[] endpoints = {
            "/mariadb/movies/rating",
            "/mariadb/movies/best",
            "/mariadb/movies/trend",
            "/mariadb/movies/inconsistent"
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random MariaDB Endpoints Load Test")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:51674")
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(10).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Primera prueba:
Empieza en 15:15
Los cortes que se ven en los gráficos es porque el pod de MariaDB estaba inestable.
![1MariaDB1](images/1MariaDB1.png)
![1MariaDB2](images/1MariaDB2.png)
![1MariaDB3](images/1MariaDB3.png)
![1MariaDB4](images/1MariaDB4.png)
![1MariaDB5](images/1MariaDB5.png)

---

### Segunda Prueba:
Esta prueba es con redis
```Java
public class MariaDBLoadTestWithRedis extends Simulation {

    // Definición de los diferentes endpoints, incluyendo el uso de Redis
    private final String[] endpoints = {
            "/mariadb/movies/rating?cache=redis",
            "/mariadb/movies/best?cache=redis",
            "/mariadb/movies/trend?cache=redis",
            "/mariadb/movies/inconsistent?cache=redis"
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random MariaDB Endpoints Load Test with Redis Cache")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268") 
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(10).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Segunda prueba:
Empieza en 16:35
![2MariaDB](images/2MariaDB1.png) ![2MariaDB](images/2MariaDB2.png) ![2MariaDB](images/2MariaDB3.png) ![2MariaDB](images/2MariaDB4.png) ![2MariaDB](images/2MariaDB5.png) ![2MariaDB](images/2MariaDB6.png) ![2MariaDB](images/2MariaDB7redis.png) ![2MariaDB](images/2MariaDB8redis.png)
Para esta prueba se incluyeron los gráficos de redis. Se puede ver que la cantidad de queries disminuyo con respecto a la primera prueba.

---

### Tercera Prueba:
Esta prueba es con memcached
```Java
public class MariaDBLoadTestWithMemcached extends Simulation {

    // Definición de los diferentes endpoints, incluyendo solo el uso de Memcached
    private final String[] endpoints = {
            "/mariadb/movies/rating?cache=memcached",
            "/mariadb/movies/best?cache=memcached",
            "/mariadb/movies/trend?cache=memcached",
            "/mariadb/movies/inconsistent?cache=memcached"
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random MariaDB Endpoints Load Test with Memcached Cache")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268") 
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(10).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Tercera prueba:
Empieza en 17:05
![3MariaDB](images/3MariaDB1.png) ![3MariaDB](images/3MariaDB2.png) ![3MariaDB](images/3MariaDB3.png) ![3MariaDB](images/3MariaDB4.png) ![3MariaDB](images/3MariaDB5.png) ![3MariaDB](images/3MariaDB6.png) ![3MariaDB](images/3MariaDB7memcached.png)  
Para esta prueba se incluyeron los gráficos de memcached. Se puede ver que la cantidad de queries disminuyo con respecto a la primera prueba.

---

### Cuarta Prueba:
```Java
public class MariaDBLoadTest2 extends Simulation {

    // Definición de los diferentes endpoints
    private final String[] endpoints = {
            "/mariadb/movies/rating",
            "/mariadb/movies/best",
            "/mariadb/movies/trend",
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random MariaDB Endpoints Load Test")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268")
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(5).during(Duration.ofSeconds(900)) // 5 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Cuarta prueba:  
Empieza en 21:06  

![4MariaDB](images/4MariaDB1.png) ![4MariaDB](images/4MariaDB2.png) ![4MariaDB](images/4MariaDB3.png) ![4MariaDB](images/4MariaDB4.png) ![4MariaDB](images/4MariaDB5.png)  
Esta prueba se realiza haciendo la conexión con tres endpoints y con la mitad de usuarios por segundo(5)

---

### Quinta prueba:
```Java
public class MariaDBLoadTest3 extends Simulation {

    // Se define el endpoint específico
    private final String endpoint = "/mariadb/movies/rating";

    // Escenario con solicitudes al primer endpoint
    ScenarioBuilder scn = scenario("MariaDB Endpoint Load Test for Rating")
            .exec(http("Rating Endpoint Request")
                    .get(endpoint) // Llama siempre al primer endpoint
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268")
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(20).during(Duration.ofSeconds(900)) 
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Quinta prueba:
Empieza en 21:30
![5MariaDB](images/5MariaDB1.png) ![5MariaDB](images/5MariaDB2.png) ![5MariaDB](images/5MariaDB3.png) ![5MariaDB](images/5MariaDB4.png) ![5MariaDB](images/5MariaDB5.png) ![5MariaDB](images/5MariaDB6.png)  

Esta prueba se realiza haciendo la conexión con solo un endpoint específico y simulando un total de 20 usuarios concurrentes.

---

## PostgreSQL

### Primera Prueba:
```Java
public class postgresqlLoadTest extends Simulation {

    // Definición de los diferentes endpoints
    private final String[] endpoints = {
            "/postgresql/movies/rating",
            "/postgresql/movies/best",
            "/postgresql/movies/trend",
            "/postgresql/movies/inconsistent"
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random postgresql Endpoints Load Test")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:51674")
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(10).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Primera prueba:
Empieza en 17:45
![1Postgres](images/1Postgres1.png) ![1Postgres](images/1Postgres2.png) ![1Postgres](images/1Postgres3.png) ![1Postgres](images/1Postgres4.png)

---

### Segunda Prueba:
Esta prueba es con redis
```Java
public class postgresqlLoadTestWithRedis extends Simulation {

    // Definición de los diferentes endpoints, incluyendo el uso de Redis
    private final String[] endpoints = {
            "/postgresql/movies/rating?cache=redis",
            "/postgresql/movies/best?cache=redis",
            "/postgresql/movies/trend?cache=redis",
            "/postgresql/movies/inconsistent?cache=redis",
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random postgresql Endpoints Load Test with Redis Cache")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268") 
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(10).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Segunda prueba:
Empieza en 18:05
![2Postgres](images/2Postgres1.png) ![2Postgres](images/2Postgres2.png) ![2Postgres](images/2Postgres3.png) ![2Postgres](images/2Postgres4.png) ![2Postgres](images/2Postgres5redis.png) ![2Postgres](images/2Postgres6redis.png)  
Se incluyen los gráficos de redis

---

### Tercera Prueba:
Esta prueba es con memcached 
```Java
public class postgresqlLoadTestWithMemcached extends Simulation {

    // Definición de los diferentes endpoints, incluyendo solo el uso de Memcached
    private final String[] endpoints = {
            "/postgresql/movies/rating?cache=memcached",
            "/postgresql/movies/best?cache=memcached",
            "/postgresql/movies/trend?cache=memcached",
            "/postgresql/movies/inconsistent?cache=memcached"
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random postgresql Endpoints Load Test with Memcached Cache")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268") 
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(10).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Tercera prueba:
Empieza en 18:29
![3Postgres](images/3Postgres1.png) ![3Postgres](images/3Postgres2.png) ![3Postgres](images/3Postgres3.png) ![3Postgres](images/3Postgres4.png) ![3Postgres](images/3Postgres5memcached.png) ![3Postgres](images/3Postgres6memcached.png)  
Se incluyen los gráficos de redis

---

### Cuarta Prueba:
```Java
public class postgresqlLoadTest2 extends Simulation {

    // Definición de los diferentes endpoints
    private final String[] endpoints = {
            "/postgresql/movies/rating",
            "/postgresql/movies/best",
            "/postgresql/movies/trend",
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random postgresql Endpoints Load Test")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268")
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(5).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Cuarta prueba:
Empieza en 18:50
![4Postgres](images/4Postgres1.png) ![4Postgres](images/4Postgres2.png) ![4Postgres](images/4Postgres3.png) ![4Postgres](images/4Postgres4.png)  

Esta prueba se realiza haciendo la conexión con tres endpoints y con la mitad de usuarios por segundo(5)

---

### Quinta prueba:
```Java
public class postgresqlLoadTest3 extends Simulation {

    // Se define el endpoint específico
    private final String endpoint = "/postgresql/movies/rating";

    // Escenario con solicitudes al primer endpoint
    ScenarioBuilder scn = scenario("postgresql Endpoint Load Test for Rating")
            .exec(http("Rating Endpoint Request")
                    .get(endpoint) // Llama siempre al primer endpoint
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268")
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(20).during(Duration.ofSeconds(900)) 
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Primera prueba:
Empieza en 19:10
 ![5Postgres](images/5Postgres1.png) ![5Postgres](images/5Postgres2.png) ![5Postgres](images/5Postgres3.png) ![5Postgres](images/5Postgres4.png)

Esta prueba se realiza haciendo la conexión con solo un endpoint específico y simulando un total de 20 usuarios concurrentes.

---

## Elastic Search

### Primera Prueba:
```Java
public class elasticsearchLoadTest extends Simulation {

    // Definición de los diferentes endpoints
    private final String[] endpoints = {
            "/elasticsearch/movies/rating",
            "/elasticsearch/movies/best",
            "/elasticsearch/movies/trend",
            "/elasticsearch/movies/inconsistent"
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random elasticsearch Endpoints Load Test")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:51674")
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(10).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Primera prueba:
Empieza en 16:05
![elastic-p1-1](./images/elastic-p1-1.png "elastic-p1-1")
![elastic-p1-2](./images/elastic-p1-2.png "elastic-p1-2")

---

### Segunda Prueba:
Esta prueba es con redis
```Java
public class elasticsearchLoadTestWithRedis extends Simulation {

    // Definición de los diferentes endpoints, incluyendo el uso de Redis
    private final String[] endpoints = {
            "/elasticsearch/movies/rating?cache=redis",
            "/elasticsearch/movies/best?cache=redis",
            "/elasticsearch/movies/trend?cache=redis",
            "/elasticsearch/movies/inconsistent?cache=redis",
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random elasticsearch Endpoints Load Test with Redis Cache")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268") 
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(10).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Segunda prueba:
Empieza en 16:50
![elastic-p2-1](./images/elastic-p2-1.png "elastic-p2-1")
![elastic-p2-2](./images/elastic-p2-2.png "elastic-p2-2")
![elastic-p2-3](./images/elastic-p2-3.png "elastic-p2-3")

---

### Tercera Prueba:
Esta prueba es con memcached 
```Java
public class elasticsearchLoadTestWithMemcached extends Simulation {

    // Definición de los diferentes endpoints, incluyendo solo el uso de Memcached
    private final String[] endpoints = {
            "/elasticsearch/movies/rating?cache=memcached",
            "/elasticsearch/movies/best?cache=memcached",
            "/elasticsearch/movies/trend?cache=memcached",
            "/elasticsearch/movies/inconsistent?cache=memcached"
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random elasticsearch Endpoints Load Test with Memcached Cache")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268") 
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(10).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Tercera prueba:
Empieza en 17:20
![elastic-p3-1](./images/elastic-p3-1.png "elastic-p3-1")
![elastic-p3-2](./images/elastic-p3-2.png "elastic-p3-2")
![elastic-p3-3](./images/elastic-p3-3.png "elastic-p3-3")

---

### Cuarta Prueba:
```Java
public class elasticsearchLoadTest2 extends Simulation {

    // Definición de los diferentes endpoints
    private final String[] endpoints = {
            "/elasticsearch/movies/rating",
            "/elasticsearch/movies/best",
            "/elasticsearch/movies/trend",
    };

    // Escenario con solicitudes aleatorias a los endpoints
    ScenarioBuilder scn = scenario("Random elasticsearch Endpoints Load Test")
            .exec(http("Random Endpoint Request")
                    .get(session -> endpoints[ThreadLocalRandom.current().nextInt(endpoints.length)])
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268")
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(5).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Cuarta prueba:
Empieza en 17:40
![elastic-p4-1](./images/elastic-p4-1.png "elastic-p4-1")
![elastic-p4-2](./images/elastic-p4-2.png "elastic-p4-2")

---

### Quinta prueba:
```Java
public class MariaDBLoadTest3 extends Simulation {

    // Se define el endpoint específico
    private final String endpoint = "/elasticsearch/movies/rating";

    // Escenario con solicitudes al primer endpoint
    ScenarioBuilder scn = scenario("elasticsearch Endpoint Load Test for Rating")
            .exec(http("Rating Endpoint Request")
                    .get(endpoint) // Llama siempre al primer endpoint
                    .check(status().is(200))
            );

    {
        // Configuración de HTTP
        HttpProtocolBuilder httpProtocol = http
                .baseUrl("http://localhost:49268")
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(20).during(Duration.ofSeconds(900)) 
                ).protocols(httpProtocol)
        );
    }
}
```
### Resultados de la Quinta prueba:
Empieza en 18:25
![elastic-p5-1](./images/elastic-p5-1.png "elastic-p5-1")
![elastic-p5-2](./images/elastic-p5-2.png "elastic-p5-2")

---
