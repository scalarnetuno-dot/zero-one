---
title: "O primeiro projeto Spring Boot"
number: 16
part: p3
kicker: "Três minutos entre um formulário na web e uma aplicação rodando na porta 8080."
goal: >-
  Gerar um projeto no Spring Initializr, entender cada pasta e cada linha do
  `pom.xml`, e subir a aplicação pela primeira vez.
---

Chega de arquivo solto. A partir daqui o projeto tem estrutura, dependências e
um comando para rodar. E, por mais anticlimático que pareça, o passo mais
importante deste capítulo é entender o que cada pasta faz — porque é nelas que
os próximos vinte e seis capítulos vão morar.

## Gerando o projeto

Vá a `start.spring.io` e preencha:

| Campo | Valor |
|---|---|
| Project | Maven |
| Language | Java |
| Spring Boot | 3.x (a versão estável mais recente) |
| Group | `com.loja` |
| Artifact | `catalog` |
| Packaging | Jar |
| Java | 21 |

Tabela: As escolhas do formulário. `Group` é o seu domínio invertido;
`Artifact` é o nome do projeto.

Em **Dependencies**, acrescente duas por enquanto:

- **Spring Web** — o servidor embutido e o suporte a REST;
- **Spring Boot DevTools** — reinício automático ao salvar.

Baixe o ZIP e descompacte. Ou, se preferir a linha de comando:

```bash title="O mesmo projeto, sem navegador"
curl https://start.spring.io/starter.zip \
  -d dependencies=web,devtools \
  -d groupId=com.loja -d artifactId=catalog \
  -d javaVersion=21 -d type=maven-project \
  -o catalog.zip
```

:::trivia
O Spring Initializr existe desde 2013 e é, ele próprio, uma aplicação Spring
Boot. A equipe o usa como vitrine e como teste de fogo: cada nova versão do
framework precisa gerar um projeto que compile na primeira tentativa. É a
razão de a experiência de "começar" em Java ser hoje melhor que em muitas
linguagens mais novas.
:::

## A estrutura, pasta por pasta

:::tree title="O que veio no ZIP"
catalog/
  pom.xml               # dependências e build
  src/
    main/
      java/
        com/loja/catalog/
          CatalogApplication.java   # o main
      resources/
        application.properties      # configuração
        static/                     # arquivos servidos direto
        templates/                  # páginas HTML (não vamos usar)
    test/
      java/
        com/loja/catalog/
          CatalogApplicationTests.java
  mvnw                  # Maven embutido (Linux/Mac)
  mvnw.cmd              # Maven embutido (Windows)
:::

Três convenções importantes nessa árvore.

**`src/main/java` e `src/test/java`** são separados de propósito: o código de
teste nunca vai para o pacote final. **`src/main/resources`** guarda tudo que
não é código — configuração, SQL, imagens. E **o pacote do `main` é a raiz da
varredura**: o Spring procura anotações a partir dele e para baixo, o que
explica por que uma classe fora de `com.loja.catalog` simplesmente não é
encontrada.

:::pitfall
Criar a classe em um pacote irmão (`com.loja.web`, por exemplo) e passar meia
hora sem entender por que o endpoint responde `404` é um rito de passagem. A
mensagem não existe porque, para o Spring, aquela classe nunca existiu.
Mantenha tudo abaixo do pacote da classe principal.
:::

## A classe principal

```java title="CatalogApplication.java" numbered
package com.loja.catalog;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class CatalogApplication {
    public static void main(String[] args) {
        SpringApplication.run(CatalogApplication.class, args);
    }
}
```

Aquele `public static void main(String[] args)` do capítulo 2 está de volta,
inteiro. É a mesma assinatura, pelo mesmo motivo: a JVM precisa de um ponto de
partida. A diferença é a linha de dentro.

:::anatomy title="A anotação que faz três coisas"
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
  - { line: 1, text: "Equivale a três anotações: `@Configuration`, `@EnableAutoConfiguration` e `@ComponentScan`." }
  - { line: 1, text: "É o `@ComponentScan` que define a raiz da varredura: este pacote e os de baixo." }
  - { line: 4, text: "`run` cria o contêiner, monta os beans, sobe o Tomcat e devolve o contexto." }
  - { line: 5, text: "`args` chega até aqui: `--server.port=9090` na linha de comando funciona." }
:::

## `pom.xml`: as dependências

```xml title="pom.xml (o essencial)" numbered
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

Duas ideias aqui valem mais que a sintaxe.

O **`parent`** é um catálogo de versões. É ele que permite declarar a
dependência sem `<version>`: o Spring Boot já sabe qual versão de cada
biblioteca funciona com qual. Essa é a resposta para o inferno de
compatibilidade que dominou o Java na década de 2000.

Um **`starter`** é um pacote de dependências relacionadas.
`spring-boot-starter-web` traz o Spring MVC, o Jackson (JSON), o Tomcat
embutido e a validação — dez bibliotecas em uma linha.

:::pitfall
`<scope>test</scope>` significa "só na compilação e execução de testes". Sem
ele, bibliotecas de teste iriam para o JAR de produção. Se você já viu um JAR
de 300 MB, provavelmente o motivo foi este.
:::

## Rodando

```bash title="Três formas, a mesma coisa"
./mvnw spring-boot:run          # Linux, Mac
mvnw.cmd spring-boot:run        # Windows

./mvnw package                  # gera o JAR
java -jar target/catalog-0.0.1-SNAPSHOT.jar
```

```text title="Saída (recortada)"
  .   ____          _            __ _ _
 /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
 \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
  '  |____| .__|_| |_|_| |_\__, | / / / /

Tomcat initialized with port 8080 (http)
Started CatalogApplication in 1.284 seconds
```

O `mvnw` é o **Maven Wrapper**: um script que baixa a versão certa do Maven na
primeira execução. Ele existe para que o projeto rode em qualquer máquina sem
instalação prévia — inclusive na do servidor de integração contínua, no
capítulo 40.

:::checkpoint
Se você vê `Started CatalogApplication` e a aplicação não encerra, está certo.
Ela agora é um servidor: fica esperando. `Ctrl+C` encerra.
:::

## `application.properties`

```properties title="src/main/resources/application.properties"
spring.application.name=catalog
server.port=8080

# log mais falante durante o desenvolvimento
logging.level.org.springframework.web=INFO
```

Este arquivo cresce ao longo do livro: banco no capítulo 19, JWT no 32,
OpenAPI no 38. A convenção de nomes é previsível — `server.port`,
`spring.datasource.url` — e a documentação oficial lista todas as chaves.

:::tip
Prefira `application.properties` a configuração em código. Um valor em
arquivo pode ser sobrescrito por variável de ambiente sem recompilar nada — e
é assim que o capítulo 42 vai passar a senha do banco em produção sem
escrevê-la em nenhum arquivo.
:::

## Um endpoint de teste, só para provar que está vivo

```java title="HelloController.java" numbered
package com.loja.catalog;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

    @GetMapping("/hello")
    public String hello() {
        return "Java One no ar";
    }
}
```

:::http title="O primeiro diálogo do projeto"
GET /hello
---
200 OK
Content-Type: text/plain

Java One no ar
:::

Quatro linhas úteis e você tem um servidor HTTP funcionando. O capítulo 17
explica cada anotação — aqui a única questão era provar que a máquina liga.

:::summary
- O Initializr gera um projeto Maven com dependências compatíveis.
- `src/main/java` é código, `src/main/resources` é configuração,
  `src/test/java` não vai para produção.
- Toda classe precisa estar abaixo do pacote da classe `@SpringBootApplication`.
- Um *starter* é um pacote de dependências; o `parent` resolve as versões.
- `mvnw` dispensa instalar Maven.
:::

:::checkpoint
Você gera um projeto, reconhece cada pasta, sabe o que o `pom.xml` declara,
sobe a aplicação e responde uma requisição HTTP.
:::

:::milestone
O projeto existe de verdade: `catalog`, na porta 8080, respondendo
`GET /hello`. Daqui até o capítulo 42 nada é criado do zero — tudo é
acrescentado a esta base.
:::

:::exercise level=1
Mude a porta para 9090 pelo `application.properties`, reinicie e confirme.
Depois faça o mesmo sem alterar o arquivo, usando a linha de comando.

:::answer
No arquivo: `server.port=9090`. Na linha de comando:
`java -jar app.jar --server.port=9090`. A segunda forma vence a primeira — a
ordem de precedência de configuração do Spring Boot tem doze níveis, e
argumento de linha de comando fica quase no topo.
:::

:::exercise level=2
Crie um segundo endpoint `GET /version` que devolva a versão do projeto. Leia
o valor de `application.properties` com `@Value("${app.version}")`.

:::answer
```java
@RestController
public class VersionController {
    private final String versao;

    public VersionController(
            @Value("${app.version}") String versao) {
        this.versao = versao;
    }

    @GetMapping("/version")
    public String versao() {
        return versao;
    }
}
```
Repare que `@Value` entrou pelo **construtor**, não pelo atributo — o mesmo
princípio do capítulo 15. E se a chave não existir, a aplicação falha na
partida, que é onde você quer descobrir.
:::

:::exercise level=3
Mova `HelloController` para o pacote `com.loja.web`, reinicie e observe o
`404`. Depois conserte de duas formas diferentes e explique qual você
preferiria em um projeto real.

:::answer
Opção 1: mover a classe de volta para dentro de `com.loja.catalog`. Opção 2:
declarar `@SpringBootApplication(scanBasePackages = "com.loja")`. A primeira é
melhor: a convenção de pacote é o que permite a qualquer pessoa nova no
projeto saber onde as coisas estão sem ler configuração.
:::
