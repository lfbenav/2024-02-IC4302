package com.gatling;
import io.gatling.javaapi.core.*;
import io.gatling.javaapi.http.HttpDsl.*;

import java.time.Duration;
import java.util.concurrent.ThreadLocalRandom;

import static io.gatling.javaapi.core.CoreDsl.*;
import static io.gatling.javaapi.http.HttpDsl.*;
import io.gatling.javaapi.http.HttpProtocolBuilder;

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
                .baseUrl("http://localhost:58650") 
                .acceptHeader("application/json");

        // Simulación de usuarios concurrentes
        setUp(
                scn.injectOpen(
                        constantUsersPerSec(10).during(Duration.ofSeconds(900)) // 10 usuarios por segundo durante 15 minutos
                ).protocols(httpProtocol)
        );
    }
}