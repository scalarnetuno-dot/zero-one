---
source_hash: 3708bd1d8b58
title: "What Spring is"
number: 15
part: p3
kicker: "You stop creating objects with new. In exchange, someone creates them for you — and you need to understand who."
epigraph: "A framework is a library that calls your code, instead of being called by it."
epigraph_by: "Martin Fowler, on inversion of control"
goal: >-
  Explain inversion of control and dependency injection with a code
  example, and say what a *bean* is and what the container is.
---

Up to chapter 14 you created every object in the program. From here on,
the framework creates them. That inversion has a name, has a reason and has
a price — and this chapter is about all three. We are not installing
anything yet: first the idea.

## The problem Spring solves

Consider the structure you built in chapter 11:

```java title="Who assembles these pieces?" numbered
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }
}
```

Someone has to write:

```java title="The manual assembly" numbered
var dataSource = new PostgresDataSource(url, user, pass);
var repository = new JdbcProductRepository(dataSource);
var service = new ProductService(repository);
var controller = new ProductController(service);
```

With four classes it is acceptable. A real API has forty: e-mail service,
HTTP client, cache, transaction, authentication, and each one depends on
three others. That assembly becomes a three-hundred-line file nobody wants
to open — and it has to be redone in every test.

:::key
Spring does nothing you couldn't do by hand. It does the **assembly** for
you, always the same way, and takes care of the order. It is a builder of
object graphs, not a magic power.
:::

:::story The word framework
Roberto came back from a conference with a new word and a certainty.

"We need a framework."

"What for?" asked Marina.

"To speed things up. The guy on the panel said it cuts development time by
70%."

"It cuts the time to write the plumbing. We haven't written the plumbing
or anything else yet."

Roberto wrote "70%" in his notebook and circled it. Two weeks later, that
number showed up on a slide, without context, next to the delivery
deadline.

Marina did what she always did: she opened the project and showed Carlos
the four lines of manual assembly that existed in `main`.

"This is what the framework is going to do for us. It's not nothing. But
it's not 70% of anything either."
:::

## Inversion of control

The expression describes exactly the trade:

:::compare left="Control in your code" right="Inverted control"
class ProductService {
  private Repo repo =
      new JdbcRepo();
}
---
class ProductService {
  private final Repo repo;

  ProductService(Repo repo) {
    this.repo = repo;
  }
}
:::

On the left, the class decides which implementation to use — and is stuck
with it forever. On the right, the class **declares what it needs** and
receives it from outside. Whoever assembles becomes the one who decides.

That second form has its own name: **constructor dependency injection**.
It is the only one this book uses, and the one officially recommended by
Spring, for three reasons: the object is born complete, the attribute can
be `final`, and the class stays testable without any framework.

## The container and the *beans*

```java title="What Spring reads" numbered
@Service
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }
}
```

One annotation, and the agreement changes. `@Service` tells Spring: *"this
class is mine, create an instance of it and keep it"*. That kept instance is
a **bean**, and the place where it lives is the **container** (formally,
the *application context*).

:::diagram type="blocks" caption="The container assembles the graph at startup, looking at the annotations and the constructors."
rows:
  - [{ text: "@SpringBootApplication", note: "scans the package looking for annotations" }]
  - [{ text: "ApplicationContext", note: "the container: creates, keeps and wires the beans" }]
  - [{ text: "@Controller", note: "receives HTTP" }, { text: "@Service", note: "rules" }, { text: "@Repository", note: "database" }]
:::

At startup, Spring scans the package, finds the annotated classes, looks at
the constructors, works out the order in which to create each one and
assembles everything. If a piece is missing, it fails **at startup** — not
on the customer's request.

:::anatomy title="How Spring decides what to inject"
lang: java
code: |
  @Service
  public class ProductService {
      private final ProductRepository repo;

      public ProductService(ProductRepository repo) {
          this.repo = repo;
      }
  }
notes:
  - { line: 1, text: "The annotation marks the class as a bean candidate." }
  - { line: 3, text: "`final` guarantees the dependency doesn't change after assembly." }
  - { line: 5, text: "A single constructor: Spring doesn't even need `@Autowired` since version 4.3." }
  - { line: 5, text: "The parameter's **type** is the lookup key: it searches for a bean that works as a `ProductRepository`." }
:::

## Four annotations that say the same thing

| Annotation | Layer | Real difference |
|---|---|---|
| `@Component` | any | the generic form |
| `@Service` | business rules | none technically; it communicates intent |
| `@Repository` | data access | translates database exceptions |
| `@Controller` | HTTP entry | enables route mapping |

Table: They all create a bean. Choosing the right one is documentation —
and, in two cases, behavior too.

:::pitfall
`@Autowired` on an attribute (*field injection*) still shows up in many
tutorials:

```java
@Autowired
private ProductRepository repository;   // avoid
```

It works and charges dearly: the attribute cannot be `final`, the class
lies about its dependencies (the constructor does not declare them) and the
unit test needs reflection to fill the field. Use the constructor. Always.
:::

## Scope: how many objects exist

By default, a bean is a **singleton**: there is **one** for the whole
application, and every request uses the same object. That has a
consequence that scares those who find out late:

:::pitfall
A singleton bean **cannot hold request state**. If `ProductService` has a
`private Product current` attribute, two simultaneous requests will
overwrite each other — and customer A will receive customer B's data. The
rule is simple: **a bean's attributes are only its dependencies**. Request
data lives in parameters and local variables.
:::

## What exactly Spring Boot adds

Spring Framework solves the assembly. Spring Boot solves the
configuration:

- **embedded server**: Tomcat comes inside the JAR; there is no server to
  install;
- **autoconfiguration**: saw PostgreSQL on the classpath? it configures
  the connection; saw Jackson? it configures JSON;
- **`application.properties`**: one file, keys with predictable names;
- **single startup**: `java -jar app.jar` and it is up.

:::history
In 2003, writing the same application required a `web.xml` file, two
`ejb-jar.xml` descriptors, an application server installed separately and
a *build-deploy* cycle of several minutes. Spring Boot dates from 2014 and
its proposal was to cut all that: convention over configuration. The
community called it "opinionated" — the framework has opinions, and you
only argue when you need to.
:::

## Where the magic charges its price

It is worth saying this now, before the enchantment begins:

- the error gets long. A Spring stack trace has sixty lines, and the three
  that matter are in the middle;
- the creation order is implicit. When two classes depend on each other,
  the error is `circular reference` and the solution is to rethink the
  design;
- the annotation hides behavior. `@Transactional` changes what happens
  around the method without showing up in its body — and chapter 30 shows
  what that means in practice.

None of this is a reason not to use it. It is a reason to know what is
happening, which is the difference between using the framework and being
used by it.

:::term Bean
An object whose life cycle is controlled by Spring: it creates it, injects
the dependencies, keeps it and destroys it.
:::

:::term Container (ApplicationContext)
The registry of all the application's beans. It assembles the graph at
startup and hands the instance to whoever asks for it by type.
:::

:::summary
- Inversion of control: the class declares what it needs; someone else
  decides what to hand over.
- Constructor injection is the only recommended form — `final` attribute,
  complete object, testing without a framework.
- `@Service`, `@Repository`, `@Controller` and `@Component` create beans.
- A bean is a singleton by default: don't keep request state in it.
- Spring assembles; Spring Boot configures.
:::

:::checkpoint
You explain inversion of control with an example, know why constructor
injection wins, recognize the four annotations and know why a bean cannot
hold request state.
:::

:::milestone
No new project line, but chapter 11's structure has just gained meaning:
`ProductService` receiving `ProductRepository` is exactly the shape Spring
expects to find. Chapter 16 installs the framework.
:::

:::exercise level=1
Rewrite this chapter's four-line manual assembly, explaining in one
sentence per line which dependency each object receives.

:::answer
The `DataSource` receives the connection configuration; the repository
receives the `DataSource`; the service receives the repository; the
controller receives the service. Each layer knows **only the one below** —
and that is the chain Spring will assemble on its own.
:::

:::exercise level=2
Write two classes, `EmailSender` (an interface), `SmtpEmailSender` and
`FakeEmailSender`, and an `OrderService` that receives the interface in its
constructor. Assemble both combinations by hand, without a framework.

:::answer
```java
var real = new OrderService(new SmtpEmailSender());
var test = new OrderService(new FakeEmailSender());
```
Two lines, two configurations of the same system. You have just done, by
hand, exactly what chapter 36's `@MockBean` does — and that is why
constructor injection makes testing trivial.
:::

:::exercise level=3
Explain, without using the word "magic", what happens between `java -jar
app.jar` and the first request served.

:::answer
The JVM loads the main class; Spring Boot creates the `ApplicationContext`;
the container scans the packages looking for annotations; for each class
found, it resolves the constructor's dependencies (creating them first, if
needed) and keeps the bean; autoconfiguration starts the embedded Tomcat
and registers the controllers' routes; the port opens. None of this is
magic: it is a graph being assembled in topological order.
:::
