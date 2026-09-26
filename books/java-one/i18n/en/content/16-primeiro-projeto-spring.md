---
source_hash: 471a80651c9f
title: "The first Spring Boot project"
number: 16
part: p3
kicker: "Three minutes between a form on the web and an application running on port 8080."
goal: >-
  Generate a project with Spring Initializr, understand every folder and
  every line of the `pom.xml`, and start the application for the first
  time.
---

No more loose files. From here on the project has structure, dependencies
and a command to run it. And, anticlimactic as it may seem, the most
important step of this chapter is understanding what each folder does —
because that is where the next twenty-six chapters are going to live.

## Generating the project

Go to `start.spring.io` and fill in:

| Field | Value |
|---|---|
| Project | Maven |
| Language | Java |
| Spring Boot | 3.x (the most recent stable version) |
| Group | `com.store` |
| Artifact | `catalog` |
| Packaging | Jar |
| Java | 21 |

Table: The form's choices. `Group` is your reversed domain; `Artifact` is
the project's name.

Under **Dependencies**, add two for now:

- **Spring Web** — the embedded server and REST support;
- **Spring Boot DevTools** — automatic restart on save.

Download the ZIP and unzip it. Or, if you prefer the command line:

```bash title="The same project, without a browser"
curl https://start.spring.io/starter.zip \
  -d dependencies=web,devtools \
  -d groupId=com.store -d artifactId=catalog \
  -d javaVersion=21 -d type=maven-project \
  -o catalog.zip
```

:::trivia
Spring Initializr has existed since 2013 and is itself a Spring Boot
application. The team uses it as a showcase and as a trial by fire: every
new version of the framework has to generate a project that compiles on the
first try. That is why the "getting started" experience in Java is better
today than in many newer languages.
:::

## The structure, folder by folder

:::tree title="What came in the ZIP"
catalog/
  pom.xml               # dependencies and build
  src/
    main/
      java/
        com/store/catalog/
          CatalogApplication.java   # the main
      resources/
        application.properties      # configuration
        static/                     # files served as they are
        templates/                  # HTML pages (we won't use them)
    test/
      java/
        com/store/catalog/
          CatalogApplicationTests.java
  mvnw                  # embedded Maven (Linux/Mac)
  mvnw.cmd              # embedded Maven (Windows)
:::

Three important conventions in this tree.

**`src/main/java` and `src/test/java`** are separate on purpose: test code
never goes into the final package. **`src/main/resources`** holds
everything that is not code — configuration, SQL, images. And **the `main`
class's package is the root of the scan**: Spring looks for annotations
from it downward, which explains why a class outside `com.store.catalog` is
simply not found.

:::pitfall
Creating the class in a sibling package (`com.store.web`, for example) and
spending half an hour not understanding why the endpoint answers `404` is a
rite of passage. There is no error message because, as far as Spring is
concerned, that class never existed. Keep everything below the main
class's package.
:::

## The main class

```java title="CatalogApplication.java" numbered
package com.store.catalog;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class CatalogApplication {
    public static void main(String[] args) {
        SpringApplication.run(CatalogApplication.class, args);
    }
}
```

That `public static void main(String[] args)` from chapter 2 is back,
whole. The same signature, for the same reason: the JVM needs a starting
point. The difference is the line inside.

:::anatomy title="The annotation that does three things"
lang: java
code: |
  @SpringBootApplication
  public class CatalogApplication {
      public static void main(String[] args) {
          SpringApplication.run(
                  CatalogApplication.class, args);
      }
  }
notes:
  - { line: 1, text: "It is equivalent to three annotations: `@Configuration`, `@EnableAutoConfiguration` and `@ComponentScan`." }
  - { line: 1, text: "`@ComponentScan` is what defines the root of the scan: this package and the ones below." }
  - { line: 4, text: "`run` creates the container, assembles the beans, starts Tomcat and returns the context." }
  - { line: 5, text: "`args` gets here: `--server.port=9090` on the command line works." }
:::

## `pom.xml`: the dependencies

```xml title="pom.xml (the essentials)" numbered
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.3.0</version>
</parent>

<properties>
    <java.version>21</java.version>
</properties>

<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

Two ideas here are worth more than the syntax.

The **`parent`** is a catalog of versions. It is what lets you declare the
dependency without `<version>`: Spring Boot already knows which version of
each library works with which. That is the answer to the compatibility hell
that dominated Java in the 2000s.

A **`starter`** is a package of related dependencies.
`spring-boot-starter-web` brings Spring MVC, Jackson (JSON), the embedded
Tomcat and validation — ten libraries in one line.

:::pitfall
`<scope>test</scope>` means "only when compiling and running tests".
Without it, test libraries would go into the production JAR. If you have
ever seen a 300 MB JAR, this was probably why.
:::

## Running it

```bash title="Three ways, the same thing"
./mvnw spring-boot:run          # Linux, Mac
mvnw.cmd spring-boot:run        # Windows

./mvnw package                  # builds the JAR
java -jar target/catalog-0.0.1-SNAPSHOT.jar
```

```text title="Output (trimmed)"
  .   ____          _            __ _ _
 /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
 \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
  '  |____| .__|_| |_|_| |_\__, | / / / /

Tomcat initialized with port 8080 (http)
Started CatalogApplication in 1.284 seconds
```

`mvnw` is the **Maven Wrapper**: a script that downloads the right version
of Maven on its first run. It exists so the project runs on any machine
without prior installation — including the continuous integration server's,
in chapter 40.

:::checkpoint
If you see `Started CatalogApplication` and the application does not exit,
that is right. It is now a server: it waits. `Ctrl+C` ends it.
:::

## `application.properties`

```properties title="src/main/resources/application.properties"
spring.application.name=catalog
server.port=8080

# chattier logging during development
logging.level.org.springframework.web=INFO
```

This file grows throughout the book: the database in chapter 19, JWT in
32, OpenAPI in 38. The naming convention is predictable — `server.port`,
`spring.datasource.url` — and the official documentation lists every key.

:::tip
Prefer `application.properties` to configuration in code. A value in a
file can be overridden by an environment variable without recompiling
anything — and that is how chapter 42 will pass the database password in
production without writing it in any file.
:::

## A test endpoint, just to prove it's alive

```java title="HelloController.java" numbered
package com.store.catalog;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

    @GetMapping("/hello")
    public String hello() {
        return "Java One is live";
    }
}
```

:::http title="The project's first dialogue"
GET /hello
---
200 OK
Content-Type: text/plain

Java One is live
:::

Four useful lines and you have a working HTTP server. Chapter 17 explains
each annotation — here the only question was proving the machine turns on.

:::summary
- Initializr generates a Maven project with compatible dependencies.
- `src/main/java` is code, `src/main/resources` is configuration,
  `src/test/java` does not go to production.
- Every class has to be below the package of the `@SpringBootApplication`
  class.
- A *starter* is a package of dependencies; the `parent` resolves the
  versions.
- `mvnw` saves you from installing Maven.
:::

:::checkpoint
You generate a project, recognize each folder, know what the `pom.xml`
declares, start the application and answer an HTTP request.
:::

:::milestone
The project really exists: `catalog`, on port 8080, answering
`GET /hello`. From here to chapter 42 nothing is created from scratch —
everything is added to this base.
:::

:::exercise level=1
Change the port to 9090 through `application.properties`, restart and
confirm. Then do the same without changing the file, using the command
line.

:::answer
In the file: `server.port=9090`. On the command line:
`java -jar app.jar --server.port=9090`. The second form beats the first —
Spring Boot's configuration precedence order has twelve levels, and a
command-line argument sits near the top.
:::

:::exercise level=2
Create a second endpoint `GET /version` that returns the project's
version. Read the value from `application.properties` with
`@Value("${app.version}")`.

:::answer
```java
@RestController
public class VersionController {
    private final String version;

    public VersionController(
            @Value("${app.version}") String version) {
        this.version = version;
    }

    @GetMapping("/version")
    public String version() {
        return version;
    }
}
```
Notice that `@Value` came in through the **constructor**, not the attribute
— the same principle as chapter 15. And if the key does not exist, the
application fails at startup, which is where you want to find out.
:::

:::exercise level=3
Move `HelloController` to the `com.store.web` package, restart and observe
the `404`. Then fix it in two different ways and explain which you would
prefer in a real project.

:::answer
Option 1: move the class back inside `com.store.catalog`. Option 2: declare
`@SpringBootApplication(scanBasePackages = "com.store")`. The first is
better: the package convention is what lets anyone new to the project know
where things are without reading configuration.
:::
