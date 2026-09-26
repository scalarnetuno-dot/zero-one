---
source_hash: a22b8a89d8a7
title: "JPA relationships"
number: 29
part: p6
kicker: "Two tables that know each other become two classes that point at each other — and that is where JPA becomes powerful and dangerous in equal measure."
goal: >-
  Map `@ManyToOne`, `@OneToMany` and `@ManyToMany`, choose the owning side
  of the relationship and avoid the three classic traps of bidirectional
  mapping.
---

So far the project has a single entity. The real world doesn't: a product
belongs to a category, an order belongs to a customer, an order has items.
This chapter connects the boxes of chapter 18's diagram.

## The most common relationship: `@ManyToOne`

```java title="Product.java (excerpt)" numbered
@ManyToOne(fetch = FetchType.LAZY, optional = false)
@JoinColumn(name = "category_id")
private Category category;
```

Five words and the table gains a `category_id` column with a foreign key.
Notice `fetch = LAZY` — it is the most important decision in the line, and
chapter 30 explains why.

:::anatomy title="The annotation that creates the foreign key"
lang: java
code: |
  @ManyToOne(fetch = FetchType.LAZY, optional = false)
  @JoinColumn(name = "category_id")
  private Category category;
notes:
  - { line: 1, text: "`@ManyToOne`: many products to one category. This is the relationship's **owning** side." }
  - { line: 1, text: "`LAZY` only loads the category when someone calls `getCategory()`." }
  - { line: 1, text: "`optional = false` becomes `NOT NULL` on the column: every product needs a category." }
  - { line: 2, text: "`@JoinColumn` names the column; without it, Hibernate makes up `category_id` anyway." }
:::

:::key
The **owning side** is always where the foreign key is — the
`@ManyToOne` side. It is what the database consults to know who points to
whom. Everything else in the mapping is navigation convenience in Java.
:::

## The other side: `@OneToMany`

```java title="Category.java (excerpt)" numbered
@OneToMany(mappedBy = "category")
private List<Product> products = new ArrayList<>();
```

`mappedBy = "category"` says: *"the owner of this relationship is
`Product`'s `category` field; I am just the mirror"*. Without it, Hibernate
creates a **third table** for the relationship — and you find out from the
schema error at startup.

:::pitfall
`@OneToMany` without `mappedBy` generates a join table nobody asked for:
`category_products`. The symptom is `ddl-auto=validate` failing with
"missing table". The cause is always the same: you declared two owning
sides.
:::

## Bidirectional demands discipline

When both sides exist in Java, they can disagree with each other:

:::compare left="Only half" right="Both sides"
product.setCategory(cat);
// cat.getProducts()
// still lacks the product
---
public void add(
    Product p) {
  products.add(p);
  p.setCategory(this);
}
:::

The object in memory stays inconsistent until someone reloads it from the
database — and the difference between what is in memory and what is in the
table is one of JPA's most baffling sources of bugs. A helper method on one
side solves it.

:::tip
Only map the `@OneToMany` side if you **really navigate** through it. A
category with eleven thousand products in a `List` is an invitation to
disaster. If navigating it is rare, forget the field and use
`productRepository.findByCategoryId(id)` — the information is the same, the
risk is not.
:::

## `@OneToMany` with its own owner: the order's items

```java title="Order.java" numbered
@Entity
@Table(name = "orders")
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "customer_id")
    private Customer customer;

    @OneToMany(mappedBy = "order",
               cascade = CascadeType.ALL,
               orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>();

    public void add(OrderItem item) {
        items.add(item);
        item.setOrder(this);
    }
}
```

Here `cascade` and `orphanRemoval` make sense: an order item **doesn't
exist** without the order. Saving the order saves the items; removing an
item from the list deletes it from the database.

:::pitfall
`CascadeType.ALL` between `Product` and `Category` would be a disaster:
deleting a category would delete all its products. Cascade is only
justified when the child is **part** of the parent — an order's items, a
customer's addresses. If the child has a life of its own, no cascade.
:::

:::trivia
The table is called `orders`, in the plural, for a prosaic reason: `ORDER`
is a reserved word in SQL (`ORDER BY`). Mapping an entity called `Order` to
a table `order` produces a syntax error in the `CREATE TABLE` that has
confused many people. Other names on the blacklist: `user`, `group`,
`table`, `select`.
:::

## `@ManyToMany`: when both sides are many

```java title="Product.java (excerpt)" numbered
@ManyToMany
@JoinTable(
    name = "product_tag",
    joinColumns = @JoinColumn(name = "product_id"),
    inverseJoinColumns = @JoinColumn(name = "tag_id"))
private Set<Tag> tags = new HashSet<>();
```

:::diagram type="er" caption="Many-to-many needs a third table — always."
columns: 2
entities:
  - name: "Product"
    fields: ["id (PK)", "name", "price"]
  - name: "Tag"
    fields: ["id (PK)", "name"]
  - name: "product_tag"
    fields: ["product_id (FK)", "tag_id (FK)"]
relations:
  - { from: "Product", to: "product_tag", label: "1:N" }
  - { from: "Tag", to: "product_tag", label: "1:N" }
:::

:::pitfall
`@ManyToMany` works well as long as the relationship is **only** a link.
The moment someone asks "when was this tag applied?" or "who applied it?",
the join table has to become an entity with its own id — and converting it
in the middle of the project is painful. Before using `@ManyToMany`, ask
whether the link might gain attributes in the future. It almost always can.
:::

Use `Set`, not `List`, in `@ManyToMany`: a `List` makes Hibernate delete
and reinsert every row of the join table on every change.

## The project's model, complete

:::diagram type="er" caption="Aurora Comércio's domain at the end of Part 6."
columns: 2
entities:
  - name: "Category"
    fields: ["id (PK)", "name"]
  - name: "Product"
    fields: ["id (PK)", "name", "price", "quantity", "category_id (FK)"]
  - name: "Customer"
    fields: ["id (PK)", "name", "email"]
  - name: "Order"
    fields: ["id (PK)", "customer_id (FK)", "created_at", "total"]
  - name: "OrderItem"
    fields: ["id (PK)", "order_id (FK)", "product_id (FK)", "quantity", "unit_price"]
relations:
  - { from: "Category", to: "Product", label: "1:N" }
  - { from: "Customer", to: "Order", label: "1:N" }
  - { from: "Order", to: "OrderItem", label: "1:N" }
:::

Notice the `unit_price` inside `OrderItem`: it is chapter 18's *snapshot*.
The product's price changes; the order's doesn't.

:::story The category inside the category
"We need subcategories," said Cláudia.

"A category inside another one?"

"Right. 'Peripherals' has 'Keyboards' and 'Mice'."

Carlos mapped it in ten minutes: a `@ManyToOne` from `Category` to
`Category` itself. It was even elegant.

The following week, Cláudia came back:

"And inside 'Keyboards' there are 'Mechanical' and 'Membrane'."

The mapping held up — a tree is a tree, whatever its depth. What didn't
hold up was the screen: listing a category's products started needing all
its descendants, and the query turned into a recursion.

"How many levels do you plan to have?" asked Marina.

"About three, I think."

"'I think' means five."

It was seven, in four months. And, on the seventh, someone created a
subcategory whose parent was itself. The database accepted it: the foreign
key was satisfied. The screen went into an infinite loop.
:::

:::summary
- `@ManyToOne` is the owning side: where the foreign key lives.
- `@OneToMany` needs `mappedBy`, otherwise it becomes a join table.
- In a bidirectional relationship, a helper method keeps both sides
  consistent.
- `cascade` and `orphanRemoval` only when the child is part of the parent.
- `@ManyToMany` with a `Set`; if the link might gain attributes, use an
  entity.
:::

:::checkpoint
You map the three cardinalities, identify the owning side, avoid the
accidental join table and know when cascade is dangerous.
:::

:::milestone
The domain is complete: category, product, customer, order and item. And,
along with it, a kind of problem arrived that didn't exist before — the
next chapter is entirely about it.
:::

:::exercise level=1
Map `Category` in `Product` with `@ManyToOne` and create the *query
method* `findByCategoryId(Long id)`. Check the column in the database.

:::answer
```java
Page<Product> findByCategoryId(Long categoryId, Pageable p);
```
Notice that the method's name navigates the relationship: `Category` +
`Id`. Spring Data understands that and generates
`WHERE category_id = ?` without any join.
:::

:::exercise level=2
Create `Order` and `OrderItem` with cascade and `orphanRemoval`. Then
remove an item from the list, save the order and check the `DELETE` in the
log.

:::answer
The `DELETE` shows up without you asking for it: `orphanRemoval = true`
understands that an item outside the parent's list no longer exists. It is
convenient and dangerous in equal measure — if someone calls
`items.clear()` by mistake, the order loses everything.
:::

:::exercise level=3
Implement the story's subcategory: `Category` with a `@ManyToOne` to
itself. Then write the validation that prevents a category from being its
own parent, directly or indirectly.

:::answer
The direct validation is trivial (`parent.getId().equals(this.getId())`).
The indirect one requires climbing the tree to the root looking for its own
id — and that is why, in large databases, this kind of hierarchy usually
gains a `path` column (something like `/1/7/23/`) that turns the cycle
check into a text comparison. A data structure solving what the algorithm
would do expensively: the same lesson as chapter 8.
:::
