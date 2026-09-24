---
title: "O que vamos construir"
number: 1
part: p1
kicker: "Antes da primeira linha de código, o destino. Ninguém aprende bem uma viagem sem saber onde ela termina."
epigraph: "Eu não tinha ideia de que estava escrevendo uma linguagem de programação para a internet. Eu estava escrevendo uma para torradeiras."
epigraph_by: "James Gosling, criador do Java"
goal: >-
  Explicar, com as palavras certas, o que é uma API REST, o que é um CRUD e
  qual é a diferença entre Java, Spring e Spring Boot — e ter o ambiente
  instalado e testado.
---

No fim deste livro existe um programa rodando. Ele não tem tela, não tem
botão e ninguém vai elogiar o visual dele. Ele fica esperando, e quando
alguém pergunta a coisa certa, ele responde:

:::http title="A pergunta e a resposta que você vai construir"
GET /products/7
Accept: application/json
---
200 OK
Content-Type: application/json

{
  "id": 7,
  "name": "Teclado mecânico",
  "price": 349.90,
  "quantity": 12
}
:::

Isso é uma **API**. Não tem mistério na sigla: *Application Programming
Interface*, uma interface para programas em vez de para pessoas. O
navegador, o aplicativo de celular e o site do cliente falam com ela pelo
mesmo protocolo que você usa para ler notícias — HTTP.

## Um programa que atende, em vez de um que roda

Um programa comum começa, faz o trabalho e termina. Um servidor não termina:
ele sobe, abre uma porta e fica aguardando. Essa diferença muda como você
pensa o código.

:::diagram type="blocks" caption="O caminho de uma requisição: cada camada resolve um problema e passa adiante."
rows:
  - [{ text: "Cliente", note: "navegador, app, curl" }]
  - [{ text: "Controller", note: "traduz HTTP em chamada de método" }]
  - [{ text: "Service", note: "as regras do negócio" }]
  - [{ text: "Repository", note: "conversa com o banco" }]
  - [{ text: "PostgreSQL", note: "onde o dado fica quando ninguém está olhando" }]
:::

Essas quatro camadas são o esqueleto do projeto. Elas aparecem no capítulo
21 e ficam até o fim. Guarde a ordem: a requisição desce, a resposta sobe.

:::story A reunião de vinte minutos
A reunião estava marcada para vinte minutos e durava uma hora e dez.

— A gente precisa de uma API — disse Roberto, no quadro branco, escrevendo a
palavra API e sublinhando duas vezes, como se sublinhar resolvesse.

— Uma API para quê? — perguntou Marina.

— Para o aplicativo conversar com o sistema.

— E o que o aplicativo precisa perguntar?

Roberto ficou quieto por três segundos, o que na escala dele é uma
eternidade. Depois olhou para Cláudia, que olhou para o caderno, que tinha
onze post-its e nenhuma resposta.

— Produtos — arriscou Cláudia. — Ele precisa listar produtos. E cadastrar. E
editar. E... apagar, acho.

— Isso tem nome — disse Marina. — Chama-se CRUD.

— Ótimo! — Roberto escreveu CRUD no quadro, sublinhou duas vezes. — Em três
semanas dá, né?

Carlos, que tinha três semanas de empresa e zero linha de Java escrita,
levantou a mão devagar. Ninguém viu.
:::

## CRUD: quatro verbos e nada mais

A maior parte de qualquer sistema é guardar coisa, mostrar coisa, mudar
coisa e apagar coisa. Alguém batizou isso de **CRUD** — *create, read,
update, delete* — e o HTTP já tinha um verbo para cada:

| Operação | Verbo HTTP | Caminho | O que devolve |
|---|---|---|---|
| Criar | `POST` | `/products` | `201` e o recurso criado |
| Listar | `GET` | `/products` | `200` e uma página de itens |
| Buscar um | `GET` | `/products/{id}` | `200` ou `404` |
| Atualizar | `PUT` | `/products/{id}` | `200` ou `404` |
| Apagar | `DELETE` | `/products/{id}` | `204` ou `404` |

Tabela: O CRUD que você vai construir na Parte 4. Decore a tabela e você
decorou metade do trabalho de um backend.

:::trivia
O termo CRUD apareceu em 1983, no livro *Managing the Data Base
Environment*, de James Martin — quinze anos antes de existir uma API REST
para chamar de sua. A ideia é mais velha que a web e vai sobreviver a ela.
:::

## Java, Spring e Spring Boot não são a mesma coisa

Essa confusão custa semanas a quem começa. Os três nomes aparecem juntos em
todo tutorial e resolvem problemas diferentes:

- **Java** é a linguagem. As palavras, a gramática, os tipos. É o que você
  aprende nas Partes 1 e 2.
- **Spring** é um conjunto de bibliotecas que resolve o encanamento de uma
  aplicação: quem cria os objetos, quem liga um no outro, quem abre a
  transação do banco.
- **Spring Boot** é o Spring com as decisões já tomadas. Ele traz um
  servidor embutido, configuração por convenção e um único comando para
  rodar tudo.

:::diagram type="blocks" caption="Cada camada acrescenta decisões já tomadas — e cobra por elas em abstração."
flow: false
rows:
  - [{ text: "Spring Boot", note: "servidor embutido, autoconfiguração" }]
  - [{ text: "Spring Framework", note: "injeção de dependência, transações, MVC" }]
  - [{ text: "Java + JVM", note: "a linguagem e a máquina que executa" }]
:::

A ordem importa: você não pode entender Spring sem entender objetos, e não
pode entender Spring Boot sem entender Spring. É por isso que este livro
gasta quatorze capítulos em Java antes de instalar o framework.

:::history
O Spring nasceu em 2003 como uma reação. O padrão da época, Enterprise
JavaBeans, exigia três arquivos e dois descritores XML para escrever uma
classe que somasse dois números. Rod Johnson publicou um livro de mil
páginas mostrando um jeito mais simples — e o código de exemplo do livro
virou o framework mais usado da plataforma.
:::

:::story
Carlos anotou no caderno: *"API = programa que responde a outro programa"*.

Depois riscou e escreveu: *"API = o momento em que dois departamentos da
empresa finalmente tentam conversar — e descobrem que falam idiomas
diferentes"*.

Marina, passando por trás, leu por cima do ombro e disse que a segunda
definição era melhor.
:::

## Trinta anos em uma página

Java não foi desenhado para servidores. Ele foi desenhado para
eletrodomésticos, e quase todas as suas esquisitices vêm daí.

:::diagram type="timeline" caption="Por que a linguagem é assim: os marcos que ainda afetam o código que você vai escrever."
width: 112
events:
  - { year: "1991", text: "Projeto Green, na Sun: uma linguagem para TV a cabo e torradeiras" }
  - { year: "1995", text: "Java 1.0 e a promessa: escreva uma vez, rode em qualquer lugar", mark: true }
  - { year: "2004", text: "Java 5: genéricos, enums, for-each — a linguagem fica moderna", mark: true }
  - { year: "2006", text: "Java vira software livre (projeto OpenJDK)" }
  - { year: "2010", text: "A Oracle compra a Sun" }
  - { year: "2014", text: "Java 8: lambdas e streams mudam o estilo do código", mark: true }
  - { year: "2018", text: "Ciclo de seis meses: uma versão nova a cada semestre" }
  - { year: "2023", text: "Java 21: records, pattern matching e threads virtuais", mark: true }
:::

Duas datas valem uma frase a mais. **1995** é a origem da JVM, a máquina
virtual que executa o bytecode — a razão pela qual o mesmo arquivo compilado
roda no seu computador e no servidor. **2014** é a data em que Java deixou
de ser uma linguagem só de objetos e ganhou funções como valor, que você vai
usar no capítulo 14 sem nem perceber.

:::trivia
O nome era **Oak**, por causa de um carvalho na frente da janela de James
Gosling. O departamento jurídico achou uma marca registrada com o mesmo
nome, a equipe foi tomar café e voltou com *Java* — a ilha de onde vinha o
grão. É por isso que o logotipo é uma caneca fumegando.
:::

## Instalando o ambiente

Você precisa de três coisas, e a ordem é esta.

**1. O JDK.** Baixe o Temurin 21 (em `adoptium.net`) ou use o gerenciador do
seu sistema. Confirme:

```bash
java -version
javac -version
```

**2. Um editor.** Qualquer um com realce de sintaxe serve para a Parte 1. A
partir do capítulo 16, uma IDE ajuda de verdade — IntelliJ IDEA Community ou
VS Code com a extensão de Java. Você não precisa dela ainda.

**3. Uma pasta.** Crie uma pasta para o livro e entre nela. Todo comando
deste livro supõe que você está na raiz do projeto.

:::tree title="Onde estamos agora"
java-one/
  App.java  # o próximo capítulo cria este arquivo
:::

:::pitfall
Não instale o JDK 8 porque um vídeo antigo disse que "é o mais estável".
Metade da sintaxe deste livro — `var`, `record`, `switch` com seta — não
existe lá. Se a sua empresa usa Java 8, você vai saber lidar depois de
aprender a versão moderna; o contrário é bem mais difícil.
:::

## O caminho inteiro, em uma imagem

Dez partes, quarenta e dois capítulos, um projeto:

```text title="A espinha dorsal do livro"
Java  →  OOP  →  HTTP  →  Spring Boot  →  REST  →  JPA
      →  PostgreSQL  →  CRUD  →  Validação  →  Segurança
      →  Testes  →  Projeto final
```

Se em algum momento você se perder, volte a esta linha e localize onde
está. Cada flecha é uma decisão nova sobre o mesmo programa.

:::summary
- Uma API é um programa que responde a outros programas, por HTTP.
- CRUD são quatro operações; o HTTP já tinha um verbo para cada uma.
- Java é a linguagem, Spring é o encanamento, Spring Boot é o Spring com as
  decisões prontas.
- A arquitetura do projeto tem quatro camadas: controller, service,
  repository, banco.
:::

:::checkpoint
Você sabe explicar o que é uma API REST e o que é um CRUD, sabe a diferença
entre Java, Spring e Spring Boot, e tem um JDK instalado que compila e
executa.
:::

:::milestone
Ambiente pronto e destino conhecido. Nenhuma linha de código escrita — e
isso está certo: o capítulo 1 de um projeto é sempre sobre decidir o que
construir.
:::

:::exercise level=1
Escreva, com suas palavras e em três frases, o que a sua API vai fazer.
Guarde o papel. No capítulo 41 você vai comparar com o que construiu.

:::answer
Não há resposta certa, mas há uma resposta boa: ela fala de *dados* e de
*operações*, não de tecnologia. "Guardar produtos de uma loja, permitir
buscar por nome e preço, e só deixar um administrador cadastrar" é uma
descrição melhor do que "uma API em Spring Boot com PostgreSQL".
:::

:::exercise level=2
Abra o terminal e rode `java -version`. Depois procure o número da versão na
página de notas de lançamento do OpenJDK e descubra uma funcionalidade que a
sua versão tem e a anterior não tinha.

:::answer
O objetivo do exercício não é a resposta, é o hábito: saber em qual versão
você está e onde se lê o que ela mudou. Um programador Java que não sabe a
própria versão vai copiar código que não compila.
:::
