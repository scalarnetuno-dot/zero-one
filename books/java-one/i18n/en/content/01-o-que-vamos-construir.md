---
source_hash: ff0799823adf
title: "What we are going to build"
number: 1
part: p1
kicker: "Before the first line of code, the destination. Nobody learns a trip well without knowing where it ends."
epigraph: "I had no idea I was writing a programming language for the internet. I was writing one for toasters."
epigraph_by: "James Gosling, creator of Java"
goal: >-
  Explain, with the right words, what a REST API is, what a CRUD is and
  what the difference is between Java, Spring and Spring Boot — and have the
  environment installed and tested.
---

At the end of this book there is a program running. It has no screen, no
button, and nobody is going to compliment how it looks. It waits, and when
someone asks the right thing, it answers:

:::http title="The question and the answer you are going to build"
GET /products/7
Accept: application/json
---
200 OK
Content-Type: application/json

{
  "id": 7,
  "name": "Mechanical keyboard",
  "price": 349.90,
  "quantity": 12
}
:::

That is an **API**. There is no mystery in the acronym: *Application
Programming Interface*, an interface for programs instead of people. The
browser, the phone app and the customer's website talk to it over the same
protocol you use to read the news — HTTP.

## A program that serves, instead of one that runs

An ordinary program starts, does its work and ends. A server does not end:
it starts, opens a port and waits. That difference changes how you think
about the code.

:::diagram type="blocks" caption="The path of a request: each layer solves one problem and passes it on."
rows:
  - [{ text: "Client", note: "browser, app, curl" }]
  - [{ text: "Controller", note: "turns HTTP into a method call" }]
  - [{ text: "Service", note: "the business rules" }]
  - [{ text: "Repository", note: "talks to the database" }]
  - [{ text: "PostgreSQL", note: "where the data lives when nobody is looking" }]
:::

These four layers are the skeleton of the project. They show up in chapter
21 and stay until the end. Remember the order: the request goes down, the
response comes up.

:::story The twenty-minute meeting
The meeting was scheduled for twenty minutes and lasted an hour and ten.

"We need an API," said Roberto at the whiteboard, writing the word API and
underlining it twice, as if underlining solved anything.

"An API for what?" asked Marina.

"For the app to talk to the system."

"And what does the app need to ask?"

Roberto was quiet for three seconds, which on his scale is an eternity.
Then he looked at Cláudia, who looked at her notebook, which had eleven
post-its and no answer.

"Products," Cláudia ventured. "It needs to list products. And register
them. And edit them. And... delete them, I guess."

"That has a name," said Marina. "It's called CRUD."

"Great!" Roberto wrote CRUD on the board and underlined it twice. "Three
weeks is enough, right?"

Carlos, who had three weeks at the company and zero lines of Java written,
slowly raised his hand. Nobody saw.
:::

## CRUD: four verbs and nothing more

Most of any system is storing things, showing things, changing things and
deleting things. Someone named that **CRUD** — *create, read, update,
delete* — and HTTP already had a verb for each:

| Operation | HTTP verb | Path | What it returns |
|---|---|---|---|
| Create | `POST` | `/products` | `201` and the created resource |
| List | `GET` | `/products` | `200` and a page of items |
| Fetch one | `GET` | `/products/{id}` | `200` or `404` |
| Update | `PUT` | `/products/{id}` | `200` or `404` |
| Delete | `DELETE` | `/products/{id}` | `204` or `404` |

Table: The CRUD you will build in Part 4. Memorize the table and you have
memorized half of a backend's job.

:::trivia
The term CRUD appeared in 1983, in James Martin's book *Managing the Data
Base Environment* — fifteen years before there was a REST API to call it
its own. The idea is older than the web and will outlive it.
:::

## Java, Spring and Spring Boot are not the same thing

This confusion costs beginners weeks. The three names show up together in
every tutorial and solve different problems:

- **Java** is the language. The words, the grammar, the types. It is what
  you learn in Parts 1 and 2.
- **Spring** is a set of libraries that handles an application's plumbing:
  who creates the objects, who wires one to another, who opens the database
  transaction.
- **Spring Boot** is Spring with the decisions already made. It brings an
  embedded server, configuration by convention and a single command to run
  everything.

:::diagram type="blocks" caption="Each layer adds decisions already made — and charges for them in abstraction."
flow: false
rows:
  - [{ text: "Spring Boot", note: "embedded server, autoconfiguration" }]
  - [{ text: "Spring Framework", note: "dependency injection, transactions, MVC" }]
  - [{ text: "Java + JVM", note: "the language and the machine that runs it" }]
:::

The order matters: you cannot understand Spring without understanding
objects, and you cannot understand Spring Boot without understanding
Spring. That is why this book spends fourteen chapters on Java before
installing the framework.

:::history
Spring was born in 2003 as a reaction. The standard of the time,
Enterprise JavaBeans, required three files and two XML descriptors to write
a class that added two numbers. Rod Johnson published a thousand-page book
showing a simpler way — and the book's sample code became the most used
framework on the platform.
:::

:::story
Carlos wrote in his notebook: *"API = a program that answers another
program"*.

Then he crossed it out and wrote: *"API = the moment two departments of the
company finally try to talk — and find out they speak different
languages"*.

Marina, walking behind him, read it over his shoulder and said the second
definition was better.
:::

## Thirty years on one page

Java was not designed for servers. It was designed for home appliances, and
almost all of its quirks come from there.

:::diagram type="timeline" caption="Why the language is the way it is: the milestones that still affect the code you are going to write."
width: 112
events:
  - { year: "1991", text: "Green Project, at Sun: a language for cable TV and toasters" }
  - { year: "1995", text: "Java 1.0 and the promise: write once, run anywhere", mark: true }
  - { year: "2004", text: "Java 5: generics, enums, for-each — the language turns modern", mark: true }
  - { year: "2006", text: "Java becomes free software (the OpenJDK project)" }
  - { year: "2010", text: "Oracle buys Sun" }
  - { year: "2014", text: "Java 8: lambdas and streams change the style of the code", mark: true }
  - { year: "2018", text: "Six-month cycle: a new version every semester" }
  - { year: "2023", text: "Java 21: records, pattern matching and virtual threads", mark: true }
:::

Two dates deserve one more sentence. **1995** is the origin of the JVM, the
virtual machine that runs the bytecode — the reason the same compiled file
runs on your computer and on the server. **2014** is when Java stopped
being an objects-only language and got functions as values, which you will
use in chapter 14 without even noticing.

:::trivia
The name was **Oak**, after an oak tree outside James Gosling's window. The
legal department found a trademark with the same name, the team went out
for coffee and came back with *Java* — the island the beans came from.
That is why the logo is a steaming mug.
:::

## Installing the environment

You need three things, in this order.

**1. The JDK.** Download Temurin 21 (at `adoptium.net`) or use your
system's package manager. Confirm:

```bash
java -version
javac -version
```

**2. An editor.** Any editor with syntax highlighting will do for Part 1.
From chapter 16 on, an IDE really helps — IntelliJ IDEA Community or VS
Code with the Java extension. You do not need it yet.

**3. A folder.** Create a folder for the book and go into it. Every command
in this book assumes you are at the root of the project.

:::tree title="Where we are now"
java-one/
  App.java  # the next chapter creates this file
:::

:::pitfall
Do not install JDK 8 because an old video said it is "the most stable".
Half the syntax in this book — `var`, `record`, `switch` with an arrow —
does not exist there. If your company uses Java 8, you will know how to
deal with it after learning the modern version; the other way around is
much harder.
:::

## The whole path, in one picture

Ten parts, forty-two chapters, one project:

```text title="The backbone of the book"
Java  →  OOP  →  HTTP  →  Spring Boot  →  REST  →  JPA
      →  PostgreSQL  →  CRUD  →  Validation  →  Security
      →  Tests  →  Final project
```

If at any moment you get lost, come back to this line and find where you
are. Each arrow is a new decision about the same program.

:::summary
- An API is a program that answers other programs, over HTTP.
- CRUD is four operations; HTTP already had a verb for each one.
- Java is the language, Spring is the plumbing, Spring Boot is Spring with
  the decisions already made.
- The project's architecture has four layers: controller, service,
  repository, database.
:::

:::checkpoint
You can explain what a REST API is and what a CRUD is, you know the
difference between Java, Spring and Spring Boot, and you have a JDK
installed that compiles and runs.
:::

:::milestone
Environment ready and destination known. Not one line of code written —
and that is right: chapter 1 of a project is always about deciding what to
build.
:::

:::exercise level=1
Write, in your own words and in three sentences, what your API is going to
do. Keep the paper. In chapter 41 you will compare it with what you built.

:::answer
There is no right answer, but there is a good one: it talks about *data*
and *operations*, not technology. "Store a shop's products, allow searching
by name and price, and only let an administrator register them" is a better
description than "an API in Spring Boot with PostgreSQL".
:::

:::exercise level=2
Open the terminal and run `java -version`. Then look up the version number
on the OpenJDK release notes page and find a feature your version has that
the previous one did not.

:::answer
The point of the exercise is not the answer, it is the habit: knowing which
version you are on and where to read what it changed. A Java programmer who
does not know their own version is going to copy code that does not
compile.
:::
