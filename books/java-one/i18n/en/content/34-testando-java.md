---
source_hash: 7a1c5b285f5f
title: "Testing Java"
number: 34
part: p8
kicker: "Testing isn't about proving it works. It's about being able to touch the code without fear on Friday."
goal: >-
  Write tests with JUnit 5 and AssertJ, name a test so it documents the
  rule, and know what isn't worth testing.
---

The API is ready and nobody has ever really tested it. Every validation so
far was a hand-typed `curl`, looking at the response and deciding, by eye,
whether it was right.

That works once. The problem is the second time.

## What a test buys you

:::key
A test doesn't prove the code is right — it proves it keeps doing what it
did when you wrote the test. The value isn't in finding today's bug: it's
in **warning you tomorrow** that someone broke the day-before-yesterday's
rule.
:::

## The first test

```java title="src/test/java/.../ProductTest.java" numbered
package com.store.catalog.product;

import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.*;

class ProductTest {

    @Test
    void shouldNotAcceptNegativePrice() {
        assertThatThrownBy(() ->
                new Product("Keyboard",
                        new BigDecimal("-10"), 5))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("price");
    }

    @Test
    void shouldDecreaseStockAndMarkSoldOut() {
        Product p = new Product("Keyboard",
                new BigDecimal("349.90"), 3);

        p.decreaseStock(3);

        assertThat(p.getQuantity()).isZero();
        assertThat(p.getStatus()).isEqualTo(Status.SOLD_OUT);
    }
}
```

```bash
./mvnw test
```

```text title="Output"
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

:::anatomy title="The anatomy of a test, in three acts"
lang: java
code: |
  @Test
  void shouldDecreaseStockAndMarkSoldOut() {
      Product p = new Product("Keyboard",
              new BigDecimal("349.90"), 3);

      p.decreaseStock(3);

      assertThat(p.getStatus())
              .isEqualTo(Status.SOLD_OUT);
  }
notes:
  - { line: 1, text: "`@Test` marks the method. It doesn't need to be public since JUnit 5." }
  - { line: 2, text: "The **name** is the documentation: it describes the rule, not the method being tested." }
  - { line: 3, text: "**Arrange**: sets up the scenario. Only what the test needs, nothing more." }
  - { line: 6, text: "**Act**: one line. If there are three, the test is checking three things." }
  - { line: 8, text: "**Assert**: what should have happened, written as a statement." }
:::

## AssertJ: the assertion that reads

```java title="The same check, two libraries" numbered
// plain JUnit
assertEquals(Status.SOLD_OUT, p.getStatus());

// AssertJ
assertThat(p.getStatus()).isEqualTo(Status.SOLD_OUT);
```

The second form has two practical advantages: it reads in natural order
("I assert that the status is equal to sold out") and the IDE's
autocomplete shows every possible check for that type after the dot.
`spring-boot-starter-test` already brings AssertJ — there's nothing to
install.

```java title="The assertions you will use" numbered
assertThat(value).isEqualTo(expected);
assertThat(list).hasSize(3).contains(item);
assertThat(list).isEmpty();
assertThat(text).startsWith("Key").containsIgnoringCase("MECHANICAL");
assertThat(number).isPositive().isLessThan(100);
assertThat(optional).isPresent().get()
        .extracting(Product::getName).isEqualTo("Keyboard");
assertThatThrownBy(() -> method())
        .isInstanceOf(IllegalStateException.class);
```

## The test's name is the specification

:::compare left="A name that doesn't help" right="A name that documents"
@Test
void testDecreaseStock() {
  ...
}

@Test
void test2() {
  ...
}
---
@Test
void shouldRejectDecrease
GreaterThanStock() {
  ...
}
:::

When a test breaks on a Friday, the only thing that shows up in the
terminal is its name. `test2 failed` forces you to open the file;
`shouldRejectDecreaseGreaterThanStock failed` has already told you what was
lost.

:::tip
A naming pattern that ages well: **should** + the expected behavior +
**when** + the condition. `shouldMarkSoldOutWhenStockReachesZero`. It gets
long and that's fine: a test name is never typed twice.
:::

## Organizing: `@Nested` and `@DisplayName`

```java title="Tests grouped by behavior" numbered
@DisplayName("Product")
class ProductTest {

    @Nested
    @DisplayName("when decreasing stock")
    class DecreaseStock {

        @Test
        @DisplayName("marks it sold out when it reaches zero")
        void soldOut() { ... }

        @Test
        @DisplayName("rejects a quantity above what's available")
        void rejectsExcess() { ... }
    }
}
```

The report starts reading like a specification:

```text
Product
  when decreasing stock
    ✔ marks it sold out when it reaches zero
    ✔ rejects a quantity above what's available
```

## Repeated cases: `@ParameterizedTest`

```java title="One test, five scenarios" numbered
@ParameterizedTest
@ValueSource(strings = {"", " ", "   "})
void shouldNotAcceptBlankName(String name) {
    assertThatThrownBy(() ->
            new Product(name, BigDecimal.TEN, 1))
            .isInstanceOf(IllegalArgumentException.class);
}

@ParameterizedTest
@CsvSource({
    "10, 3, 7",
    "3,  3, 0",
    "1,  1, 0"
})
void shouldSubtractFromStock(int initial, int taken, int expected) {
    Product p = new Product("X", BigDecimal.TEN, initial);
    p.decreaseStock(taken);
    assertThat(p.getQuantity()).isEqualTo(expected);
}
```

## What not to test

:::pitfall
Don't test getters, setters, trivial constructors or the framework. A test
that checks whether `getName()` returns the name protects against nothing
and has to be maintained forever. Test **decisions**: `if`, calculation,
validation, transformation. Where there is no decision, there is nothing to
break.
:::

| Worth testing | Not worth it |
|---|---|
| business rules | getters and setters |
| calculation and rounding | trivial DTO mapping |
| validation and exceptions | framework configuration |
| edge cases (zero, empty, null) | third-party libraries |

Table: The question is always the same: *if this breaks, will anyone
notice?*

## Coverage: a number that lies

```bash
./mvnw verify   # with the JaCoCo plugin configured
```

Coverage measures **lines executed** by the tests, not rules verified. A
test that calls the method and asserts nothing gives 100% coverage and zero
guarantee.

:::trivia
The "80% coverage" target is probably the most distorted metric in
software engineering. It was born as an empirical observation and became a
target — and every metric that becomes a target stops being a metric. The
classic symptom: tests written to cover lines, with `assertTrue(true)` at
the end, approved because the number went up.
:::

:::story Doesn't testing slow us down?
"How long does it take to write these tests?" asked Roberto.

"About thirty percent more at the beginning."

Roberto wrote it down. Thirty percent more is, on his spreadsheet, thirty
percent more.

Marina waited a bit and returned the question in the currency he
understood:

"How many hours did we spend last month fixing things that had already
worked before?"

Roberto didn't know. He went to check. He came back the next day with a
number he had added up himself from the tickets: sixty-two percent of the
team's time.

It didn't become a rule immediately. It became one after chapter 33's
incident — when a four-line test would have kept thirty-one people from
being able to delete the catalog.
:::

:::summary
- A test protects the future, not the present: it warns you when someone
  breaks the rule.
- Arrange, act, assert — and the method's name is the documentation.
- AssertJ reads in natural order and is discoverable through autocomplete.
- `@ParameterizedTest` trades five identical tests for one with five
  inputs.
- Test decisions; don't test getters or the framework. High coverage is no
  guarantee.
:::

:::checkpoint
You write unit tests with JUnit and AssertJ, name them so the report
documents the rule, use parameterized tests and know what to leave out.
:::

:::milestone
`Product`'s rules are covered by tests that run in milliseconds, with no
database and no Spring. The next chapter tests the service — which has
dependencies.
:::

:::exercise level=1
Write three tests for `decreaseStock`: success, zero quantity and a
quantity greater than the stock.

:::answer
The third is the most valuable: it checks that the right exception is
thrown. Testing the happy path proves the code works; testing the refused
path proves it **protects**.
:::

:::exercise level=2
Convert the three tests above into a `@ParameterizedTest` with
`@CsvSource`. Then decide whether it got better or worse and justify it.

:::answer
Better for the calculation cases, which vary only in the numbers. Worse
for the exception cases, which check different types — forcing them into
the same table requires a column with the exception's name, and the test
ends up with an `if`. A test with an `if` inside is a test that needs a
test.
:::

:::exercise level=3
Write a test that fails on purpose and read AssertJ's output carefully.
Then do the same with JUnit's `assertEquals` and compare the messages.

:::answer
AssertJ shows the expected and the actual in separate blocks, highlighting
the difference; for collections, it points out the missing and extra
elements. The quality of the failure message is the practical reason to
prefer it — because the message is read in a hurry, almost always with the
build red.
:::
