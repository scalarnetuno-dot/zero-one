---
source_hash: 330531921db4
title: "First program in Java"
number: 2
part: p1
kicker: "Two commands, one file and the most famous line in programming."
goal: >-
  Write, compile and run a Java program from the terminal, explain every
  word of the `main` signature and read a compiler error message without
  panicking.
---

In Python you write and run. In Java you write, **compile** and run. That
extra step is the first thing that scares people coming from another
language, and it is also the one that gives back the most: compilation is
where someone reads your code before you do.

:::diagram type="flowchart" caption="From text to program: the compiler sits in the middle on purpose."
nodes:
  - { id: src, type: io,      text: "App.java" }
  - { id: cc,  type: process, text: "javac App.java" }
  - { id: cls, type: io,      text: "App.class (bytecode)" }
  - { id: jvm, type: process, text: "java App" }
  - { id: out, type: start,   text: "Output in the terminal" }
edges:
  - { from: src, to: cc }
  - { from: cc,  to: cls, label: "no errors" }
  - { from: cls, to: jvm }
  - { from: jvm, to: out }
:::

The `.class` file is not machine code: it is **bytecode**, an intermediate
format any JVM knows how to run. That is why the same compiled file runs on
your Windows machine and on the Linux server without recompiling — the
promise from 1995 that still holds.

## The file

Create a file called `App.java`. The name is not decoration: a public
class has to live in a file with the same name.

```java title="App.java" numbered
public class App {
    public static void main(String[] args) {
        System.out.println("The first program");
    }
}
```

Compile and run:

```bash
javac App.java
java App
```

The first command creates `App.class` in the same folder. The second hands
that file to the virtual machine, which looks for a method called `main`
and starts there. Notice that `java App` has no extension: you are not
running a file, you are asking a class to start.

## The most copied signature in history

Five words before the method name, and each one solves a concrete problem.
It is worth spending a page on this because you will write this line for
the rest of your life.

:::anatomy title="The main signature, word by word"
lang: java
code: |
  public class App {
      public static void main(String[] args) {
          System.out.println("The first program");
      }
  }
notes:
  - { line: 1, text: "`public class App` — the class is the wrapper; in Java nothing lives outside one." }
  - { line: 2, text: "`public` lets the JVM see the method from outside the file." }
  - { line: 2, text: "`static` allows calling it without creating an object — at the start of the program there are none." }
  - { line: 2, text: "`void` because it returns nothing to the caller." }
  - { line: 2, text: "`String[] args` receives what you typed after the program name." }
  - { line: 3, text: "`System.out` is standard output; `println` writes and moves to the next line." }
:::

:::trivia
`System.out.println` takes 18 characters to do what Python does with 5.
The reason is consistency: `System` is a class, `out` is one of its fields
and `println` is a method of that field. Java chose not to make an
exception in its grammar even for the most written line in the world. In
2023, thirty years later, the language finally got a bare `println` in
implicit classes — and the community is still arguing about whether it was
a good idea.
:::

:::story Is it in production already?
Carlos ran `javac App.java`. He waited. Nothing happened.

He stared at the terminal for about ten seconds, convinced it had frozen.
He typed `java App`. And then, on the black screen, appeared:

```text
The first program
```

He spun around in his chair and announced, too loud for an open office:

"IT COMPILED!"

Roberto, walking by with a coffee in his hand, stopped.

"It compiled? So it's in production already?"

"No. It prints a sentence."

"A sentence for the customer?"

"A sentence for me."

Roberto nodded slowly, the way someone does who did not understand but is
going to repeat the information at the next meeting as if he had.
:::

## Arguments: the program receiving the world

`String[] args` is not decoration. Replace the body of `main`:

```java title="Greeting.java" numbered
public class Greeting {
    public static void main(String[] args) {
        System.out.println("Hello, " + args[0]);
    }
}
```

```bash
javac Greeting.java
java Greeting Ana
```

```text title="Output"
Hello, Ana
```

You have just written a program with input. It is not much, but it is the
difference between an exercise and a tool.

:::pitfall
Run `java Greeting` without the name. The answer is
`ArrayIndexOutOfBoundsException: Index 0 out of bounds for length 0` — you
asked for the first item of an empty list. Keep that message in mind: it
comes back in chapter 6, and it always tells you exactly which index you
tried to use.
:::

## When the compiler complains

Delete the semicolon on line 3 and compile again:

```text title="Terminal"
Greeting.java:3: error: ';' expected
        System.out.println("Hello, " + args[0])
                                               ^
1 error
```

Four pieces of information in three lines: the file, the line, what was
missing and an arrow pointing at the exact spot. A compile error costs ten
seconds. The same defect, in a language without this step, would cost a
broken run in front of a user.

:::key
Read the **first** message, not the last. A syntax error confuses the
compiler, which then starts complaining about correct things right below.
Fix the first one, compile again, and half the list disappears.
:::

## Two words you will hear a lot

:::term JDK
*Java Development Kit*: the package that compiles and runs. It brings
`javac`, `java`, the debugger and the libraries.
:::

:::term JRE
*Java Runtime Environment*: it only runs. It has no `javac`. It was
distributed separately for years and is the cause of half the frustrated
installations of people starting out.
:::

:::history
Up to Java 8, installing Java on the desktop installed a JRE with a browser
plugin — the origin of those endless "Java Update" prompts. Applets died,
the plugin was removed in Java 11 and today the standard distribution is a
JDK. If a tutorial tells you to download "the JRE", it is from another
decade.
:::

## What about the IDE?

Nothing so far required one. That is deliberate: an IDE's green button
hides exactly the two steps you needed to see. From chapter 16 on, when the
project has dozens of files and dependencies, an IDE stops being a comfort
and becomes a tool — and the book will use one.

:::tree title="Where we are now"
java-one/
  App.java       # prints a line
  App.class      # generated by javac
  Greeting.java  # receives an argument
:::

:::summary
- Java compiles before it runs: `javac` produces bytecode, `java` runs it.
- A public class lives in a file with the same name.
- `main` is where the JVM starts, and each word of the signature solves a
  concrete problem.
- The compile error is the cheapest review there is. Read the first
  message.
:::

:::checkpoint
You write, compile and run a Java program from the terminal, you can
explain `public static void main(String[] args)` and you know what to do
when `javac` complains.
:::

:::milestone
The project has one class that prints and one that takes an argument.
Neither survives chapter 16 — but the habit of compiling before running
outlives the book.
:::

:::exercise level=1
Write a `Sum.java` that takes two numbers as arguments and prints their
sum. Hint: `Integer.parseInt(args[0])` turns text into a number.

:::answer
```java
public class Sum {
    public static void main(String[] args) {
        int a = Integer.parseInt(args[0]);
        int b = Integer.parseInt(args[1]);
        System.out.println(a + b);
    }
}
```
Without `parseInt`, `args[0] + args[1]` concatenates text: `2` and `3`
become `"23"`. It is the first encounter with an idea from the next chapter
— the type decides what `+` means.
:::

:::exercise level=2
Break the program on purpose three times: change `String[]` to `String`,
delete a `}` brace and write `Sistem.out.println`. Read the three messages
before fixing them.

:::answer
The first compiles and fails at run time with `NoSuchMethodError: main` —
the signature has to be exact. The second gives `reached end of file while
parsing`. The third gives `cannot find symbol`, with an arrow pointing at
`Sistem`. Three messages, three categories: signature, syntax and name.
:::
