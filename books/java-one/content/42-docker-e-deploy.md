---
title: "Docker e deploy"
number: 42
part: p10
kicker: "Um programa que só roda na sua máquina é um hobby. O que roda em qualquer máquina é um sistema."
goal: >-
  Empacotar a aplicação em uma imagem Docker, subir tudo com Docker Compose,
  configurar por variável de ambiente e saber o que olhar depois que ela está
  no ar.
---

A API está pronta, testada e documentada — e roda em um lugar só. Este
capítulo fecha o livro tirando o projeto da sua máquina.

## Por que Docker

Uma imagem é o sistema operacional mínimo, mais o Java, mais o seu JAR, mais
a configuração — tudo congelado em um arquivo. A mesma imagem roda no seu
computador, no servidor de integração contínua e em produção.

:::key
Docker não resolve "funciona na minha máquina" por mágica. Ele resolve
porque a máquina **passa a ir junto** com o programa. O que você testa é
exatamente o que sobe.
:::

## O Dockerfile em dois estágios

```dockerfile title="Dockerfile" numbered
# estágio 1: compilar
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -B dependency:go-offline
COPY src ./src
RUN mvn -B clean package -DskipTests

# estágio 2: só o que precisa rodar
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --from=build /app/target/*.jar app.jar
USER app
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

:::anatomy title="Cada linha do Dockerfile resolve um problema"
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
  - { line: 2, text: "Copiar o `pom.xml` sozinho aproveita o cache: dependência só é baixada de novo se ele mudar." }
  - { line: 4, text: "O código vem depois, porque ele muda a cada commit e invalidaria o cache." }
  - { line: 7, text: "O segundo estágio usa **JRE**, não JDK: 180 MB em vez de 450 MB." }
  - { line: 8, text: "`--from=build` copia só o JAR. Maven, código-fonte e cache ficam para trás." }
  - { line: 9, text: "Rodar como usuário comum: se alguém escapar do processo, não escapa como root." }
:::

```bash
docker build -t aurora/catalog:1.0 .
docker run -p 8080:8080 aurora/catalog:1.0
```

## Docker Compose: a aplicação e o banco juntos

```yaml title="docker-compose.yml" numbered
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: catalog
      POSTGRES_USER: catalog
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - dados:/var/lib/postgresql/data
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
  dados:
```

```bash
echo "DB_PASSWORD=$(openssl rand -hex 16)" > .env
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env
docker compose up --build
```

Três detalhes que separam isto de um exemplo de tutorial. O **volume** faz os
dados sobreviverem ao `docker compose down`. O **healthcheck** impede a API de
subir antes de o banco aceitar conexão. E o `.env` — que **não** vai para o
Git — guarda os segredos.

:::pitfall
`depends_on` sozinho espera o contêiner **iniciar**, não o banco ficar
pronto. Sem `condition: service_healthy`, a API sobe primeiro, tenta conectar,
falha e reinicia — funcionando por acidente na segunda tentativa. Em produção,
esse acidente é uma janela de indisponibilidade a cada deploy.
:::

## Configuração por ambiente, nunca por arquivo

```properties title="application.properties — com valor padrão de desenvolvimento"
# a URL completa vem do ambiente; o padrão local fica no compose
spring.datasource.url=${SPRING_DATASOURCE_URL}
spring.datasource.username=${SPRING_DATASOURCE_USERNAME:postgres}
spring.datasource.password=${SPRING_DATASOURCE_PASSWORD:senha}
app.jwt.secret=${JWT_SECRET:desenvolvimento-apenas-32-bytes-ok}
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.open-in-view=false
```

| | Desenvolvimento | Produção |
|---|---|---|
| Banco | contêiner local | serviço gerenciado |
| Senha | `.env` local | cofre de segredos |
| `ddl-auto` | `validate` | `validate` |
| Log de SQL | ligado | desligado |
| Swagger | aberto | protegido ou desligado |

Tabela: A mesma imagem em ambos; só as variáveis mudam. É isso que permite
promover exatamente o artefato testado.

## O que olhar quando está no ar

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

:::http title="O endpoint que o orquestrador consulta"
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

`/actuator/health/readiness` responde "estou pronta para receber tráfego" e
`/actuator/health/liveness`, "estou viva". A diferença importa: uma aplicação
pode estar viva e ainda carregando — e mandar tráfego para ela nesse momento
gera erro.

:::pitfall
`management.endpoints.web.exposure.include=*` expõe `/actuator/env`, que
mostra **todas as variáveis de ambiente** — incluindo senha de banco e
segredo do JWT. Exponha apenas o que você precisa, e proteja o caminho
`/actuator/**` na configuração de segurança.
:::

## Integração contínua, em vinte linhas

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

O Testcontainers do capítulo 37 funciona aqui sem configuração: o runner do
GitHub já tem Docker. A partir deste arquivo, todo *pull request* roda a
suíte inteira antes de alguém revisar — e o ramo protegido do capítulo 40
passa a ter dentes.

:::story Deploy na sexta
A última funcionalidade ficou pronta numa sexta, às 16h40.

— Sobe hoje? — perguntou Roberto.

Houve um silêncio na sala que qualquer pessoa da área reconheceria.

Marina abriu o histórico de incidentes dos últimos oito meses e mostrou uma
coluna simples, feita de somar chamados: dos onze incidentes graves, sete
tinham acontecido entre sexta 16h e sábado 2h.

— Não é superstição — ela disse. — É que sexta à noite tem menos gente
acordada, menos gente disponível e mais vontade de ir embora. O deploy não é
mais perigoso na sexta. **A gente** é.

Subiu na terça de manhã.

Deu problema — sempre dá alguma coisa. Um índice faltando na migração, a
listagem lenta por doze minutos. Quatro pessoas estavam na frente do
computador, a correção saiu em oito minutos, ninguém precisou ser acordado.

Na retrospectiva, Roberto perguntou se dava para "garantir que não dê
problema nenhum no deploy".

Marina disse que não. Disse que dá para garantir outra coisa: que, quando der,
tenha gente por perto e um caminho de volta.

Foi a última pergunta do trimestre. Na semana seguinte ele chegou com um
pedido novo:

— É só uma alteraçãozinha.
:::

:::art caption="Não é que sexta seja perigosa. É que sexta tem menos gente acordada."
src="nao-e-que-sexta-seja-perigosa-e-que-sexta-tem-menos-gente-acordada.png"
Charge editorial minimalista: calendário de parede com os dias da semana;
sobre a sexta-feira, um grande botão vermelho de "DEPLOY" com uma mão
hesitando acima dele. Ao lado do calendário, um relógio marcando 16h40 e uma
fileira de cadeiras de escritório vazias, com apenas uma ocupada. Ao fundo,
uma janela com o céu já escuro. Fundo branco, poucos elementos, humor visual
seco, estética editorial de tecnologia.
:::

## O que vem depois deste livro

Você construiu uma API completa. O que fica de fora — e agora você tem base
para estudar sozinho:

- **versionamento de API** (`/v1/products`) e política de depreciação;
- **cache** com Redis, e o problema difícil de invalidá-lo;
- **mensageria** (RabbitMQ, Kafka) para desacoplar operações lentas;
- **observabilidade**: log estruturado, métricas, rastreamento distribuído;
- **bloqueio otimista** e concorrência, que apareceu no capítulo 41;
- **arquitetura hexagonal**, quando o projeto crescer a ponto de doer.

Nenhum desses assuntos é pré-requisito do outro. Escolha o que o seu problema
atual pedir — que é, afinal, o método que este livro inteiro usou.

:::summary
- Dockerfile em dois estágios: compila em um, roda no outro, com JRE e
  usuário comum.
- Compose junta aplicação e banco, com volume e healthcheck.
- Configuração por variável de ambiente; segredo nunca no repositório.
- Actuator responde `health`, `readiness` e `liveness` — exponha só o
  necessário.
- CI roda a suíte em todo *pull request*; o ramo protegido faz o resto.
:::

:::checkpoint
Você empacota a aplicação em uma imagem, sobe tudo com um comando, configura
por ambiente e sabe o que monitorar depois que está no ar.
:::

:::milestone
Fim. Do `System.out.println` do capítulo 2 a uma API REST autenticada,
testada, documentada e em contêiner. É o mesmo projeto, quarenta e dois
capítulos depois — e agora ele é seu.
:::

:::exercise level=1
Construa a imagem e rode `docker compose up`. Confirme que a API responde e
que os dados sobrevivem a um `docker compose restart`.

:::answer
Se os dados sumirem, falta o `volumes:` no serviço do banco. É o erro mais
comum de quem começa com Compose, e o mais assustador quando acontece em um
ambiente compartilhado.
:::

:::exercise level=2
Compare o tamanho da imagem com e sem o segundo estágio. Depois compare
`temurin:21-jre-alpine` com `temurin:21-jdk`.

:::answer
Um estágio só, com JDK: cerca de 450 MB. Dois estágios, com JRE alpine: cerca
de 180 MB. A diferença não é estética — ela aparece no tempo de cada deploy,
multiplicada pelo número de instâncias e pelo número de vezes que você sobe
por dia.
:::

:::exercise level=3
Configure o workflow de CI e faça um *pull request* com um teste quebrado de
propósito. Confirme que o GitHub bloqueia o merge.

:::answer
Ver o botão de merge desabilitado por um teste vermelho é o momento em que
todas as partes deste livro se conectam: o teste do capítulo 34 impede, no
capítulo 42, que um defeito chegue à produção. Foi para isso que os
quarenta e dois capítulos existiram.
:::
