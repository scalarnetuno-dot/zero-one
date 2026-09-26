---
source_hash: 41c088731d81
title: "Before you begin"
matter: front
numbered: false
kicker: "A short book about a language that is usually taught far too long."
---

There are two ways to teach Java. The first presents the whole language —
thirty years of features, four kinds of loop, eight modifiers, the
collections hierarchy in a diagram the size of a wall — and promises that
one day all of it becomes a program. The second picks a program and teaches
only the Java it demands, when it demands it.

This book is the second kind. It has one project: a product catalog REST
API, with a database, validation, authentication, tests and documentation.
You are going to build it. Each language concept shows up in the chapter
where the project needs it, and not before.

:::key
This book is not a Java reference. It is a path to a working API. If you
want the complete reference later, it fits on a website; the path is the
hard part to find.
:::

## How this book works

The project grows in a straight line. In chapter 2 you print a line in the
terminal; in chapter 17 you answer an HTTP request; in 23 you have a
complete CRUD; in 32 you protect that CRUD with a token; in 42 you ship
everything in a container. Each chapter ends with the state of the project
at that point:

:::milestone
You have: nothing yet. An open terminal, an installed JDK and an empty
folder. That is exactly where all software starts.
:::

The path is not clean, on purpose. You will write code that breaks, read
the whole error message and fix it. That is how programming is really
learned — and it is the part tutorials edit out.

## What you need

A JDK 21 or newer, a text editor and a terminal. A PostgreSQL database
shows up in Part 4, and chapter 19 explains how to start one in two
minutes. Nothing else.

```bash title="Check that everything is in place"
java -version
javac -version
```

If both answer with a version number, you are ready.

:::pitfall
`java -version` answering and `javac -version` not answering is the classic
symptom of having installed a JRE instead of a JDK. The JRE only runs; the
JDK compiles. You need the second one.
:::

## The cast

Between one explanation and the next, you will find scenes from a company.
It is called Aurora Comércio, it sells everything online, and it has just
decided it needs an API — ideally by yesterday.

The scenes are not decoration: they exist because an abstract concept
sticks better when it comes attached to a situation you recognize. When the
book explains `NullPointerException`, you will remember Mr. Antônio.

:::story The five you are going to meet
**Carlos** joined three weeks ago. He knows logic, does not know Java, and
was assigned to "that little API project". He is you.

**Marina** is the senior developer. She has seen this movie, knows how it
ends and still insists on reviewing every *pull request* line by line.

**Roberto** is the manager. He does not write code, he writes deadlines. To
him, any request fits in the sentence "it's just a tiny change".

**Cláudia** owns the product. She brings new requirements as casually as
someone bringing coffee — including the day before delivery.

**Mr. Antônio**, 68, is the store's first customer. In two minutes of use he
finds bugs the team cannot reproduce in two weeks.
:::

:::art caption="The Aurora Comércio team on the first day of the project." src="o-time-da-aurora-comercio-no-primeiro-dia-do-projeto.png"
Ilustração editorial minimalista em traço limpo: cinco personagens de corpo
inteiro lado a lado, como um retrato de elenco, sobre fundo branco. Carlos,
jovem desenvolvedor segurando um notebook novo demais e uma expressão de
otimismo ingênuo. Marina, desenvolvedora sênior de braços cruzados, caneca
de café, olhar de quem já sabe o que vem. Roberto, gerente de camisa social,
apontando para um cronograma impresso onde se lê apenas "3 SEMANAS".
Cláudia, product owner com um caderno cheio de post-its coloridos
transbordando. Seu Antônio, senhor de 68 anos com óculos na ponta do nariz,
segurando um celular na horizontal e apertando a tela com o dedo indicador.
Humor sutil, poucos elementos, sem cenário elaborado, estética de revista de
tecnologia, personagens expressivos, sem estética infantil.
:::

## Conventions

Snippets like `System.out.println` appear in code font when quoted in the
middle of a sentence. Larger blocks come with the file name at the top — in
Java that name matters more than in almost any other language, and chapter
2 explains why.

Five marks appear in the margins of the text, and they are worth
recognizing in advance:

:::trivia
**Did you know** brings the curiosity, the history, the design decision
that stuck. It can be skipped without loss — but it is what lets you tell
the story at a bar table.
:::

:::pitfall
**Common mistake** shows the trap before you fall into it. It is almost
always a mistake I have made.
:::

:::history
**Behind the scenes** tells why the language is the way it is. Java has
many strange decisions, and almost all of them have a dated reason.
:::

:::checkpoint
**Checkpoint** closes the chapter listing what you can already do — not
what you read, what you *can do*.
:::

And **The project now** is the chapter's milestone: one sentence about
where the API stands. If you open the book in the middle, it is the first
thing to look for.
