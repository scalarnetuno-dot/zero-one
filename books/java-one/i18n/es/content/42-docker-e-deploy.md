---
source_hash: 62a8a79586b9
title: "Docker y deploy"
number: 42
part: p10
kicker: "Un programa que solo corre en tu máquina es un pasatiempo. El que corre en cualquier máquina es un sistema."
goal: >-
  Empaquetar la aplicación en una imagen Docker, levantar todo con Docker
  Compose, configurar por variables de entorno y saber qué mirar una vez que
  está en el aire.
---

La API está lista, probada y documentada, y corre en un solo lugar. Este
capítulo cierra el libro sacando el proyecto de tu máquina.

## Por qué Docker

Una imagen es el sistema operativo mínimo, más Java, más tu JAR, más la
configuración: todo congelado en un archivo. La misma imagen corre en tu
computadora, en el servidor de integración continua y en producción.

:::key
Docker no resuelve "en mi máquina funciona" por arte de magia. Lo resuelve
porque la máquina **pasa a viajar** con el programa. Lo que pruebas es
exactamente lo que se despliega.
:::

## El Dockerfile en dos etapas

```dockerfile title="Dockerfile" numbered
# etapa 1: compilar
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -B dependency:go-offline
COPY src ./src
RUN mvn -B clean package -DskipTests

# etapa 2: solo lo que hace falta para correr
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --from=build /app/target/*.jar app.jar
USER app
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

:::anatomy title="Cada línea del Dockerfile resuelve un problema"
lang: dockerfile
code: |
  FROM maven:3.9-eclipse-temurin-21 AS build
  COPY pom.xml .
  RUN mvn -B dependency:go-offline
  COPY src ./src
  RUN mvn -B clean package -DskipTests

  FROM eclipse-temurin:21-jre-alpine
  COPY --from=build /app/target/*.jar app.jar
  USER app
notes:
  - { line: 2, text: "Copiar el `pom.xml` solo aprovecha la caché: las dependencias solo se vuelven a bajar si él cambia." }
  - { line: 4, text: "El código viene después, porque cambia en cada commit e invalidaría la caché." }
  - { line: 7, text: "La segunda etapa usa **JRE**, no JDK: 180 MB en vez de 450 MB." }
  - { line: 8, text: "`--from=build` copia solo el JAR. Maven, el código fuente y la caché quedan atrás." }
  - { line: 9, text: "Correr como usuario común: si alguien escapa del proceso, no escapa como root." }
:::

```bash
docker build -t aurora/catalog:1.0 .
docker run -p 8080:8080 aurora/catalog:1.0
```

## Docker Compose: la aplicación y la base juntas

```yaml title="docker-compose.yml" numbered
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: catalog
      POSTGRES_USER: catalog
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - datos:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U catalog"]
      interval: 5s
      retries: 5

  api:
    build: .
    depends_on:
      db:
        condition: service_healthy
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://db:5432/catalog
      SPRING_DATASOURCE_USERNAME: catalog
      SPRING_DATASOURCE_PASSWORD: ${DB_PASSWORD}
      JWT_SECRET: ${JWT_SECRET}
    ports:
      - "8080:8080"

volumes:
  datos:
```

```bash
echo "DB_PASSWORD=$(openssl rand -hex 16)" > .env
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env
docker compose up --build
```

Tres detalles separan esto de un ejemplo de tutorial. El **volumen** hace
que los datos sobrevivan al `docker compose down`. El **healthcheck** impide
que la API arranque antes de que la base acepte conexiones. Y el `.env`
—que **no** va a Git— guarda los secretos.

:::pitfall
`depends_on` solo espera a que el contenedor **arranque**, no a que la base
esté lista. Sin `condition: service_healthy`, la API sube primero, intenta
conectarse, falla y se reinicia, y funciona por accidente en el segundo
intento. En producción, ese accidente es una ventana de indisponibilidad en
cada deploy.
:::

## Configuración por entorno, nunca por archivo

```properties title="application.properties — con valor por defecto de desarrollo"
# la URL completa viene del entorno; el valor local está en el compose
spring.datasource.url=${SPRING_DATASOURCE_URL}
spring.datasource.username=${SPRING_DATASOURCE_USERNAME:postgres}
spring.datasource.password=${SPRING_DATASOURCE_PASSWORD:secreto}
app.jwt.secret=${JWT_SECRET:solo-desarrollo-32-bytes-o-mas-ok}
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.open-in-view=false
```

| | Desarrollo | Producción |
|---|---|---|
| Base | contenedor local | servicio gestionado |
| Contraseña | `.env` local | bóveda de secretos |
| `ddl-auto` | `validate` | `validate` |
| Log de SQL | encendido | apagado |
| Swagger | abierto | protegido o apagado |

Tabla: La misma imagen en los dos; solo cambian las variables. Eso es lo que
permite promover exactamente el artefacto probado.

## Qué mirar cuando está en el aire

```xml title="pom.xml"
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

```properties
management.endpoints.web.exposure.include=health,info,metrics
management.endpoint.health.probes.enabled=true
```

:::http title="El endpoint que consulta el orquestador"
GET /actuator/health
---
200 OK

{
  "status": "UP",
  "components": {
    "db": { "status": "UP" },
    "diskSpace": { "status": "UP" }
  }
}
:::

`/actuator/health/readiness` responde "estoy lista para recibir tráfico" y
`/actuator/health/liveness`, "estoy viva". La diferencia importa: una
aplicación puede estar viva y todavía cargando, y mandarle tráfico en ese
momento genera errores.

:::pitfall
`management.endpoints.web.exposure.include=*` expone `/actuator/env`, que
muestra **todas las variables de entorno**, incluidas la contraseña de la
base y el secreto del JWT. Expón solo lo que necesitas, y protege la ruta
`/actuator/**` en la configuración de seguridad.
:::

## Integración continua, en veinte líneas

```yaml title=".github/workflows/ci.yml" numbered
name: CI
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: temurin
          cache: maven
      - run: ./mvnw -B verify
```

El Testcontainers del capítulo 37 funciona aquí sin configuración: el runner
de GitHub ya tiene Docker. A partir de este archivo, todo *pull request*
corre la suite entera antes de que alguien lo revise, y la rama protegida
del capítulo 40 pasa a tener dientes.

:::story Deploy un viernes
La última funcionalidad quedó lista un viernes, a las 16:40.

—¿Sube hoy? —preguntó Roberto.

Hubo en la sala un silencio que cualquier persona del área reconocería.

Marina abrió el historial de incidentes de los últimos ocho meses y mostró
una columna simple, hecha sumando tickets: de los once incidentes graves,
siete habían pasado entre el viernes a las 16 y el sábado a las 2.

—No es superstición —dijo ella—. Es que el viernes a la noche hay menos
gente despierta, menos gente disponible y más ganas de irse. El deploy no es
más peligroso el viernes. **Nosotros** lo somos.

Subió el martes a la mañana.

Hubo un problema: siempre hay algo. Un índice faltante en la migración, el
listado lento durante doce minutos. Había cuatro personas frente a la
computadora, la corrección salió en ocho minutos, nadie tuvo que despertarse.

En la retrospectiva, Roberto preguntó si se podía "garantizar que el deploy
no dé ningún problema".

Marina dijo que no. Dijo que se puede garantizar otra cosa: que, cuando lo
dé, haya gente cerca y un camino de vuelta.

Fue la última pregunta del trimestre. A la semana siguiente él llegó con un
pedido nuevo:

—Es solo un cambiecito.
:::

:::art caption="No es que el viernes sea peligroso. Es que el viernes hay menos gente despierta."
src="nao-e-que-sexta-seja-perigosa-e-que-sexta-tem-menos-gente-acordada.png"
Charge editorial minimalista: calendário de parede com os dias da semana;
sobre a sexta-feira, um grande botão vermelho de "DEPLOY" com uma mão
hesitando acima dele. Ao lado do calendário, um relógio marcando 16h40 e uma
fileira de cadeiras de escritório vazias, com apenas uma ocupada. Ao fundo,
uma janela com o céu já escuro. Fundo branco, poucos elementos, humor visual
seco, estética editorial de tecnologia.
:::

## Lo que viene después de este libro

Construiste una API completa. Lo que queda afuera, y para lo que ahora
tienes base para estudiar por tu cuenta:

- **versionado de API** (`/v1/products`) y política de deprecación;
- **caché** con Redis, y el problema difícil de invalidarla;
- **mensajería** (RabbitMQ, Kafka) para desacoplar operaciones lentas;
- **observabilidad**: log estructurado, métricas, trazas distribuidas;
- **bloqueo optimista** y concurrencia, que apareció en el capítulo 41;
- **arquitectura hexagonal**, cuando el proyecto crezca hasta doler.

Ninguno de estos temas es requisito previo del otro. Elige el que pida tu
problema actual, que es, al fin y al cabo, el método que usó este libro
entero.

:::summary
- Dockerfile en dos etapas: compila en una, corre en la otra, con JRE y
  usuario común.
- Compose junta aplicación y base, con volumen y healthcheck.
- Configuración por variables de entorno; los secretos, nunca en el
  repositorio.
- Actuator responde `health`, `readiness` y `liveness`: expón solo lo
  necesario.
- La CI corre la suite en todo *pull request*; la rama protegida hace el
  resto.
:::

:::checkpoint
Empaquetas la aplicación en una imagen, levantas todo con un comando,
configuras por entorno y sabes qué monitorear una vez que está en el aire.
:::

:::milestone
Fin. Del `System.out.println` del capítulo 2 a una API REST autenticada,
probada, documentada y en contenedor. Es el mismo proyecto, cuarenta y dos
capítulos después, y ahora es tuyo.
:::

:::exercise level=1
Construye la imagen y corre `docker compose up`. Confirma que la API
responde y que los datos sobreviven a un `docker compose restart`.

:::answer
Si los datos desaparecen, falta el `volumes:` en el servicio de la base. Es
el error más común de quien empieza con Compose, y el más aterrador cuando
pasa en un entorno compartido.
:::

:::exercise level=2
Compara el tamaño de la imagen con y sin la segunda etapa. Después compara
`temurin:21-jre-alpine` con `temurin:21-jdk`.

:::answer
Una sola etapa, con JDK: unos 450 MB. Dos etapas, con JRE alpine: unos
180 MB. La diferencia no es estética: aparece en el tiempo de cada deploy,
multiplicada por el número de instancias y por las veces que despliegas por
día.
:::

:::exercise level=3
Configura el workflow de CI y abre un *pull request* con una prueba rota a
propósito. Confirma que GitHub bloquea el merge.

:::answer
Ver el botón de merge deshabilitado por una prueba en rojo es el momento en
que todas las partes de este libro se conectan: la prueba del capítulo 34
impide, en el capítulo 42, que un defecto llegue a producción. Para eso
existieron los cuarenta y dos capítulos.
:::
