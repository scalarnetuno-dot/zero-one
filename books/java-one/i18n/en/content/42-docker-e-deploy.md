---
source_hash: 62a8a79586b9
title: "Docker and deploy"
number: 42
part: p10
kicker: "A program that only runs on your machine is a hobby. One that runs on any machine is a system."
goal: >-
  Package the application in a Docker image, bring everything up with
  Docker Compose, configure it through environment variables, and know what
  to watch once it's live.
---

The API is ready, tested and documented — and it runs in one place only.
This chapter closes the book by getting the project off your machine.

## Why Docker

An image is the minimal operating system, plus Java, plus your JAR, plus
the configuration — all frozen into one file. The same image runs on your
computer, on the continuous integration server and in production.

:::key
Docker doesn't fix "works on my machine" by magic. It fixes it because the
machine **starts traveling along** with the program. What you test is
exactly what goes live.
:::

## The two-stage Dockerfile

```dockerfile title="Dockerfile" numbered
# stage 1: compile
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -B dependency:go-offline
COPY src ./src
RUN mvn -B clean package -DskipTests

# stage 2: only what's needed to run
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --from=build /app/target/*.jar app.jar
USER app
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

:::anatomy title="Each line of the Dockerfile solves a problem"
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
  - { line: 2, text: "Copying `pom.xml` on its own uses the cache: dependencies are only downloaded again if it changes." }
  - { line: 4, text: "The code comes after, because it changes on every commit and would invalidate the cache." }
  - { line: 7, text: "The second stage uses a **JRE**, not a JDK: 180 MB instead of 450 MB." }
  - { line: 8, text: "`--from=build` copies only the JAR. Maven, source code and cache stay behind." }
  - { line: 9, text: "Run as a regular user: if someone escapes the process, they don't escape as root." }
:::

```bash
docker build -t aurora/catalog:1.0 .
docker run -p 8080:8080 aurora/catalog:1.0
```

## Docker Compose: the application and the database together

```yaml title="docker-compose.yml" numbered
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: catalog
      POSTGRES_USER: catalog
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - data:/var/lib/postgresql/data
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
  data:
```

```bash
echo "DB_PASSWORD=$(openssl rand -hex 16)" > .env
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env
docker compose up --build
```

Three details separate this from a tutorial example. The **volume** makes
the data survive `docker compose down`. The **healthcheck** keeps the API
from starting before the database accepts connections. And the `.env` —
which does **not** go into Git — holds the secrets.

:::pitfall
`depends_on` alone waits for the container to **start**, not for the
database to be ready. Without `condition: service_healthy`, the API comes up
first, tries to connect, fails and restarts — working by accident on the
second try. In production, that accident is a window of downtime on every
deploy.
:::

## Configuration by environment, never by file

```properties title="application.properties — with a development default"
# the full URL comes from the environment; local default: compose
spring.datasource.url=${SPRING_DATASOURCE_URL}
spring.datasource.username=${SPRING_DATASOURCE_USERNAME:postgres}
spring.datasource.password=${SPRING_DATASOURCE_PASSWORD:secret}
app.jwt.secret=${JWT_SECRET:development-only-32-bytes-long-ok}
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.open-in-view=false
```

| | Development | Production |
|---|---|---|
| Database | local container | managed service |
| Password | local `.env` | secrets vault |
| `ddl-auto` | `validate` | `validate` |
| SQL log | on | off |
| Swagger | open | protected or off |

Table: The same image in both; only the variables change. That is what
lets you promote exactly the artifact that was tested.

## What to watch once it's live

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

:::http title="The endpoint the orchestrator checks"
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

`/actuator/health/readiness` answers "I'm ready to receive traffic" and
`/actuator/health/liveness`, "I'm alive". The difference matters: an
application can be alive and still loading — and sending traffic to it at
that moment produces errors.

:::pitfall
`management.endpoints.web.exposure.include=*` exposes `/actuator/env`,
which shows **every environment variable** — including the database
password and the JWT secret. Expose only what you need, and protect the
`/actuator/**` path in the security configuration.
:::

## Continuous integration, in twenty lines

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

Chapter 37's Testcontainers works here with no configuration: GitHub's
runner already has Docker. From this file on, every *pull request* runs
the whole suite before anyone reviews it — and chapter 40's protected
branch gets teeth.

:::story Friday deploy
The last feature was ready on a Friday, at 4:40 p.m.

"Does it go live today?" asked Roberto.

There was a silence in the room anyone in the field would recognize.

Marina opened the incident history for the last eight months and showed a
simple column, made by adding up tickets: of the eleven serious incidents,
seven had happened between Friday 4 p.m. and Saturday 2 a.m.

"It's not superstition," she said. "It's that on Friday night there are
fewer people awake, fewer people available and more urge to go home. The
deploy isn't more dangerous on Friday. **We** are."

It went live on Tuesday morning.

There was a problem — there always is something. A missing index in the
migration, the listing slow for twelve minutes. Four people were at their
computers, the fix went out in eight minutes, nobody had to be woken up.

At the retrospective, Roberto asked whether they could "guarantee there
won't be any problem at all with the deploy".

Marina said no. She said something else can be guaranteed: that, when
there is one, there are people around and a way back.

It was the last question of the quarter. The next week he showed up with a
new request:

"It's just a tiny change."
:::

:::art caption="It's not that Friday is dangerous. It's that on Friday fewer people are awake."
src="nao-e-que-sexta-seja-perigosa-e-que-sexta-tem-menos-gente-acordada.png"
Charge editorial minimalista: calendário de parede com os dias da semana;
sobre a sexta-feira, um grande botão vermelho de "DEPLOY" com uma mão
hesitando acima dele. Ao lado do calendário, um relógio marcando 16h40 e uma
fileira de cadeiras de escritório vazias, com apenas uma ocupada. Ao fundo,
uma janela com o céu já escuro. Fundo branco, poucos elementos, humor visual
seco, estética editorial de tecnologia.
:::

## What comes after this book

You built a complete API. What's left out — and you now have the
foundation to study on your own:

- **API versioning** (`/v1/products`) and deprecation policy;
- **caching** with Redis, and the hard problem of invalidating it;
- **messaging** (RabbitMQ, Kafka) to decouple slow operations;
- **observability**: structured logging, metrics, distributed tracing;
- **optimistic locking** and concurrency, which showed up in chapter 41;
- **hexagonal architecture**, when the project grows to the point of pain.

None of these topics is a prerequisite for another. Pick whichever your
current problem asks for — which is, after all, the method this whole book
used.

:::summary
- Two-stage Dockerfile: compile in one, run in the other, with a JRE and a
  regular user.
- Compose brings the application and database together, with a volume and
  a healthcheck.
- Configuration through environment variables; secrets never in the
  repository.
- Actuator answers `health`, `readiness` and `liveness` — expose only what's
  needed.
- CI runs the suite on every *pull request*; the protected branch does the
  rest.
:::

:::checkpoint
You package the application in an image, bring everything up with one
command, configure by environment and know what to monitor once it's
live.
:::

:::milestone
The end. From chapter 2's `System.out.println` to an authenticated, tested,
documented, containerized REST API. It's the same project, forty-two
chapters later — and now it's yours.
:::

:::exercise level=1
Build the image and run `docker compose up`. Confirm the API responds and
that the data survives a `docker compose restart`.

:::answer
If the data disappears, the `volumes:` is missing from the database
service. It's the most common mistake of people starting with Compose, and
the scariest when it happens in a shared environment.
:::

:::exercise level=2
Compare the image size with and without the second stage. Then compare
`temurin:21-jre-alpine` with `temurin:21-jdk`.

:::answer
A single stage, with a JDK: about 450 MB. Two stages, with JRE alpine:
about 180 MB. The difference isn't cosmetic — it shows up in the time of
every deploy, multiplied by the number of instances and by how many times a
day you deploy.
:::

:::exercise level=3
Set up the CI workflow and open a *pull request* with a test broken on
purpose. Confirm GitHub blocks the merge.

:::answer
Seeing the merge button disabled by a red test is the moment every part of
this book connects: chapter 34's test prevents, in chapter 42, a defect
from reaching production. That is what the forty-two chapters were for.
:::
