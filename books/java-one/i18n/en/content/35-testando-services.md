---
source_hash: 1a91b0c145c5
title: "Testing services"
number: 35
part: p8
kicker: "To test the rule, the database has to get out of the way — and someone has to pretend to be it."
goal: >-
  Isolate the service with Mockito, check calls with `verify`, and
  recognize when a mock stopped helping and started testing itself.
---

Chapter 22's `ProductService` depends on `ProductRepository`. Testing it
with a real database is slow and brittle; testing it with nothing is
impossible. The way out is to hand it a **fake** repository, which does
whatever the test says.

And that is only possible because of a decision from chapter 15:
constructor injection.

## The mock

```java title="ProductServiceTest.java" numbered
@ExtendWith(MockitoExtension.class)
class ProductServiceTest {

    @Mock
    ProductRepository repository;

    @InjectMocks
    ProductService service;

    @Test
    void shouldThrowWhenProductDoesNotExist() {
        when(repository.findById(99L))
                .thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.find(99L))
                .isInstanceOf(ProductNotFoundException.class)
                .hasMessageContaining("99");
    }
}
```

:::anatomy title="The four pieces of a test with a mock"
lang: java
code: |
  @ExtendWith(MockitoExtension.class)
  class ProductServiceTest {

      @Mock
      ProductRepository repository;

      @InjectMocks
      ProductService service;

      @Test
      void shouldThrowWhenMissing() {
          when(repository.findById(99L))
                  .thenReturn(Optional.empty());
          ...
      }
  }
notes:
  - { line: 1, text: "Mockito's extension processes the annotations. No Spring is loaded." }
  - { line: 4, text: "`@Mock` creates a double: every method returns empty or null until you teach it." }
  - { line: 7, text: "`@InjectMocks` assembles the service with the mocks — through the constructor." }
  - { line: 12, text: "`when(...).thenReturn(...)` teaches the double to answer in that case." }
:::

:::key
Notice what this test does **not** do: it doesn't start Spring, doesn't
open a connection, doesn't touch a database. It runs in milliseconds and
tests exactly one thing — that the service turns "not found" into a
`ProductNotFoundException`.
:::

## Checking what was called

```java title="Sometimes what matters is the effect" numbered
@Test
void shouldSaveNewProduct() {
    var data = new ProductRequest("Keyboard", null,
            new BigDecimal("349.90"), 12);

    when(repository.existsByNameIgnoreCase("Keyboard"))
            .thenReturn(false);
    when(repository.save(any(Product.class)))
            .thenAnswer(inv -> inv.getArgument(0));

    service.create(data);

    ArgumentCaptor<Product> captor =
            ArgumentCaptor.forClass(Product.class);
    verify(repository).save(captor.capture());

    assertThat(captor.getValue().getName())
            .isEqualTo("Keyboard");
    assertThat(captor.getValue().getStatus())
            .isEqualTo(Status.ACTIVE);
}
```

The `ArgumentCaptor` keeps the object the service passed to the repository
— it is how you check **what** would be saved without saving anything.

```java title="And what must not happen" numbered
@Test
void shouldNotSaveWhenNameIsDuplicate() {
    when(repository.existsByNameIgnoreCase("Keyboard"))
            .thenReturn(true);

    assertThatThrownBy(() -> service.create(data))
            .isInstanceOf(DuplicateProductException.class);

    verify(repository, never()).save(any());
}
```

`verify(..., never())` is often more valuable than the `assert`: it proves
the operation was **aborted before** touching the database.

## Mockito's minimum vocabulary

| Command | What for |
|---|---|
| `when(x).thenReturn(y)` | teaches the answer |
| `when(x).thenThrow(e)` | teaches it to fail |
| `verify(mock).method()` | confirms it was called |
| `verify(mock, never())` | confirms it **wasn't** |
| `verify(mock, times(2))` | confirms how many times |
| `any()`, `eq(value)` | matches arguments |
| `ArgumentCaptor` | captures what was passed |

Table: Seven constructs cover 95% of service tests.

:::pitfall
`when(repository.save(any()))` without `thenReturn` returns `null`. If the
service uses the return value (`return repository.save(p).getId()`), the
test fails with a `NullPointerException` — and it's not the code's fault,
it's the badly taught mock's. When the return value matters, use
`thenAnswer(inv -> inv.getArgument(0))` to return the object itself.
:::

## When the mock starts getting in the way

:::story The test that tested the mock
The test had ninety lines and seven mocks.

It checked that the service called the repository, which called the
mapper, which called the validator, which called the event publisher — each
one taught to answer exactly what the service expected.

It always passed. It passed even in the week the order total calculation
was off by one cent, because the mapper's mock returned a fixed value
nobody had updated.

"This test doesn't test the service," said Marina, at the review. "It tests
my ability to predict what the service is going to call. If I change the
order of the calls without changing the result, it breaks. If I break the
result without changing the order, it passes."

Carlos asked what to do.

"When the test has more mocks than assertions, the problem isn't the test.
It's the class, which depends on too many things."

`OrderService` became two: one that calculates and depends on nothing, and
one that orchestrates. The first got twelve tests without a single mock.
The second kept two.
:::

:::art caption="When the test has more stand-ins than actors, it has become a rehearsal."
src="quando-o-teste-tem-mais-dubles-que-atores-ele-virou-ensaio.png"
Charge editorial minimalista: palco de teatro visto de frente, com um único
ator real no centro e sete manequins de madeira posicionados ao redor, cada
um com uma plaquinha pendurada no pescoço: "repositório", "mapeador",
"validador". Na plateia, uma única pessoa aplaude com cara de dúvida. Fundo
branco, poucos elementos, humor visual seco, estética editorial de
tecnologia.
:::

:::pitfall
Three signs the mock has become the problem: the test has more `when` lines
than `assertThat` lines; the test breaks when you refactor without changing
behavior; the test passes when the result is wrong. Any of the three is a
request to split the class.
:::

## The alternative: the hand-written double

```java title="A fake repository, for real" numbered
class InMemoryProductRepository implements ProductRepository {

    private final Map<Long, Product> data = new HashMap<>();
    private long sequence = 0;

    @Override
    public <S extends Product> S save(S p) {
        if (p.getId() == null) {
            p.setId(++sequence);
        }
        data.put(p.getId(), p);
        return p;
    }

    @Override
    public Optional<Product> findById(Long id) {
        return Optional.ofNullable(data.get(id));
    }

    // ... the rest of the interface
}
```

This is exactly chapter 8's `Map`, now fulfilling a contract. Its
advantage over the mock is that it **behaves**: saving and then finding
returns what was saved, without anyone teaching it. The disadvantage is
that `JpaRepository` has dozens of methods to implement.

:::tip
The practical middle ground: declare a smaller interface, with only the
methods the service uses (`ProductGateway`, with four methods), and make
`ProductRepository` extend it. The test implements the small interface;
production uses Spring Data. It is chapter 11's lesson — depend on the
contract — applied to testing.
:::

:::summary
- Constructor injection is what makes the service testable without a
  framework.
- `@Mock` + `@InjectMocks` set up the scenario; `when` teaches; `verify`
  confirms.
- `verify(never())` proves the operation was aborted before the database.
- Too many mocks test the author's prediction, not the behavior.
- A hand-written double behaves; a mock only answers.
:::

:::checkpoint
You isolate the service with Mockito, teach answers, capture arguments,
verify the absence of a call and recognize when too many mocks are a
symptom of a class doing too much.
:::

:::milestone
The project's business rules have fast tests independent of
infrastructure. What's missing is proving that HTTP — path, status and
JSON — is still what was agreed.
:::

:::exercise level=1
Write the test for `delete`, checking that the repository received
`delete` with the right product.

:::answer
```java
when(repository.findById(1L))
        .thenReturn(Optional.of(product));

service.delete(1L);

verify(repository).delete(product);
```
:::

:::exercise level=2
Test `decreaseStock` for the insufficient-stock case. Check the exception
**and** that nothing was saved.

:::answer
The second check is the one that matters: without it, the test would pass
even if the service threw the exception **after** writing the decrease. The
right exception with the wrong side effect is a defect that only shows up
in production.
:::

:::exercise level=3
Take one of your tests with four or more mocks and try to rewrite it by
splitting the class under test. Compare the before and after.

:::answer
In most cases a pure class shows up — calculation, decision,
transformation — that depends on nothing and gets trivial tests. What's
left in the original class is orchestration, and orchestration is tested
with a few `verify`s. The quality of the test is a thermometer for the
design of the code: a hard test is almost never the test's problem.
:::
