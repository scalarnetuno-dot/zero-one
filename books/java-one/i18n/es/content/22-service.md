---
source_hash: 696ff888e952
title: "Service"
number: 22
part: p4
kicker: "La capa donde viven las reglas. Si está vacía, las reglas están desparramadas en otro lugar, y las vas a encontrar por las malas."
goal: >-
  Mover las reglas de negocio del controlador a un servicio, inyectar el
  repositorio por constructor y usar `@Transactional` sabiendo lo que hace.
---

El controlador del capítulo 17 sabía HTTP **y** sabía reglas. Mientras la
regla es "guárdalo en el mapa", pasa. Cuando se vuelve "no dejes registrar
dos productos con el mismo nombre, y al descontar stock márcalo como agotado
si llega a cero", el controlador deja de ser un traductor y pasa a ser el
sistema entero.

## Las tres responsabilidades, separadas

:::diagram type="blocks" caption="Cada capa solo conoce la de abajo, y solo hace una cosa."
rows:
  - [{ text: "Controller", note: "HTTP: ruta, estado, JSON" }]
  - [{ text: "Service", note: "reglas de negocio y transacción" }]
  - [{ text: "Repository", note: "consultas y grabación" }]
:::

| Capa | Sabe | No sabe |
|---|---|---|
| Controller | verbo, ruta, estado | reglas, base de datos |
| Service | reglas, orden de las operaciones | HTTP, JSON |
| Repository | SQL, entidad | reglas, HTTP |

Tabla: La prueba del olfato: si el `Service` importa algo de `http`, la
separación se rompió.

:::key
El `Service` no debe tener ningún `import` de `org.springframework.http` ni
de `jakarta.servlet`. Si lo tiene, las reglas de negocio pasaron a depender
del protocolo, y probarlas va a exigir levantar un servidor.
:::

## El servicio

```java title="ProductService.java" numbered
package com.tienda.catalog.product;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ProductService {

    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }

    @Transactional(readOnly = true)
    public List<Product> listar() {
        return repository.findAll();
    }

    @Transactional(readOnly = true)
    public Product buscar(Long id) {
        return repository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException(id));
    }

    @Transactional
    public Product crear(Product nuevo) {
        if (repository.existsByNameIgnoreCase(nuevo.getName())) {
            throw new DuplicateProductException(nuevo.getName());
        }
        return repository.save(nuevo);
    }

    @Transactional
    public Product actualizar(Long id, Product datos) {
        Product actual = buscar(id);
        actual.setName(datos.getName());
        actual.setDescription(datos.getDescription());
        actual.setPrice(datos.getPrice());
        actual.setQuantity(datos.getQuantity());
        return actual;         // sin save: entidad gestionada
    }

    @Transactional
    public void borrar(Long id) {
        Product actual = buscar(id);
        repository.delete(actual);
    }
}
```

Cinco métodos y cuatro decisiones que merecen explicación.

:::anatomy title="Las decisiones escondidas en cinco métodos"
lang: java
code: |
  @Transactional(readOnly = true)
  public Product buscar(Long id) {
      return repository.findById(id)
              .orElseThrow(() ->
                  new ProductNotFoundException(id));
  }

  @Transactional
  public Product actualizar(Long id, Product datos) {
      Product actual = buscar(id);
      actual.setPrice(datos.getPrice());
      return actual;
  }
notes:
  - { line: 1, text: "`readOnly = true` le avisa a la base que no habrá escritura: permite optimizar." }
  - { line: 4, text: "`orElseThrow` convierte la ausencia en una excepción con nombre; el capítulo 26 la convierte en `404`." }
  - { line: 10, text: "Reutiliza `buscar`: la regla del \"no existe\" vive en un solo lugar." }
  - { line: 12, text: "Sin `save`: la entidad está gestionada y el `UPDATE` sale al final de la transacción." }
:::

## `@Transactional`: lo que realmente hace esta anotación

Envuelve el método en una transacción de base de datos: la abre antes, la
confirma (`commit`) si termina bien, la deshace (`rollback`) si se escapa
una excepción.

:::diagram type="sequence" caption="Spring intercepta la llamada y se ocupa del principio y del final."
actors:
  - { id: c, name: "Controller" }
  - { id: p, name: "Proxy" }
  - { id: s, name: "Service" }
  - { id: d, name: "Base" }
messages:
  - { from: c, to: p, text: "crear(producto)" }
  - { from: p, to: d, text: "BEGIN" }
  - { from: p, to: s, text: "crear(producto)" }
  - { from: s, to: d, text: "INSERT" }
  - { from: s, to: p, text: "retorna", dashed: true }
  - { from: p, to: d, text: "COMMIT" }
  - { from: p, to: c, text: "producto guardado", dashed: true }
:::

Fíjate en el **proxy**. Spring no modifica tu método: crea un objeto que
envuelve tu servicio e intercepta la llamada. Eso explica las dos trampas
más comunes de la anotación.

:::pitfall
**Una llamada interna no pasa por el proxy.** Si `crear()` llama a
`this.validar()` y solo `validar()` tiene `@Transactional`, la anotación se
ignora: la llamada no salió del objeto, así que el proxy no vio nada. La
solución es poner la transacción en el método público que inicia la
operación.
:::

:::pitfall
**Solo una excepción *unchecked* deshace la transacción, por defecto.** Una
`IOException` (checked) que se escapa de un método `@Transactional` hace
que Spring confirme la transacción de todos modos. Para cambiarlo:
`@Transactional(rollbackFor = Exception.class)`.
:::

:::story La transacción que no existía
El descuento de stock funcionaba. Menos cuando no funcionaba.

Una vez cada doscientas, el producto salía del stock y el pedido no se
grababa. El cliente pagaba, el ítem desaparecía del estante y el pedido no
existía en ninguna parte.

Carlos había puesto `@Transactional` en el método. Estaba ahí, escrito,
visible, con el import correcto.

Marina abrió el archivo y señaló la línea 61: el método público llamaba a
`this.descontarYProcesar()`, un método privado de la misma clase, que era
donde estaba la anotación.

—La anotación no es una promesa que hace el método —dijo—. Es una promesa
que alguien hace *alrededor* de él. Si la llamada no sale del objeto, no hay
nadie alrededor.

Carlos pasó el resto del día entendiendo qué es un proxy. Fue la tarde más
útil de ese mes.
:::

## Las excepciones de negocio

```java title="ProductNotFoundException.java" numbered
package com.tienda.catalog.product;

public class ProductNotFoundException extends RuntimeException {
    public ProductNotFoundException(Long id) {
        super("producto no encontrado: " + id);
    }
}
```

```java title="DuplicateProductException.java" numbered
public class DuplicateProductException extends RuntimeException {
    public DuplicateProductException(String name) {
        super("ya existe un producto con el nombre: " + name);
    }
}
```

Dos clases de cinco líneas. No saben nada de HTTP, y justamente por eso el
servicio puede lanzarlas. En el capítulo 26, un traductor central convierte
la primera en `404` y la segunda en `409`.

## La regla de negocio de verdad

Hasta aquí el servicio solo orquesta. La regla aparece cuando el negocio
tiene una decisión:

```java title="Una operación con regla" numbered
@Transactional
public Product descontarStock(Long id, int cantidad) {
    Product producto = buscar(id);

    if (cantidad <= 0) {
        throw new IllegalArgumentException("cantidad inválida");
    }
    if (producto.getQuantity() < cantidad) {
        throw new InsufficientStockException(
                producto.getQuantity(), cantidad);
    }

    producto.setQuantity(producto.getQuantity() - cantidad);
    if (producto.getQuantity() == 0) {
        producto.setStatus(Status.AGOTADO);
    }
    return producto;
}
```

Esta es la capa que justifica la arquitectura. Fíjate en que la regla "stock
cero pasa a agotado" existe en **un** solo lugar. Si viviera en el
controlador, cada endpoint nuevo que descontara stock tendría que repetirla,
y uno de ellos se olvidaría.

:::tip
Un servicio bien escrito se lee como la descripción del negocio: buscar,
validar, cambiar, decidir. Si al leerlo en voz alta oyes "toma la petición,
extrae el parámetro, arma el JSON", el código está en la capa equivocada.
:::

## El controlador, ahora delgado

```java title="ProductController.java (solo lo que le toca)" numbered
@RestController
@RequestMapping("/products")
public class ProductController {

    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping("/{id}")
    public Product buscar(@PathVariable Long id) {
        return service.buscar(id);
    }
}
```

Cuatro líneas útiles por endpoint. El controlador se volvió lo que debería
ser: un traductor entre HTTP y una llamada a un método.

:::compare left="Antes (cap. 17)" right="Después"
@GetMapping("/{id}")
Product buscar(
    @PathVariable Long id) {
  Product p =
      base.get(id);
  if (p == null) {
    return null;
  }
  return p;
}
---
@GetMapping("/{id}")
Product buscar(
    @PathVariable Long id) {
  return service.buscar(id);
}
:::

:::summary
- El controller traduce HTTP; el service decide; el repository persiste.
- El servicio no importa nada de HTTP: eso es lo que lo mantiene
  comprobable.
- `@Transactional` abre y cierra la transacción mediante un proxy: una
  llamada interna no cuenta.
- Una excepción *checked* que se escapa no deshace la transacción por
  defecto.
- Dentro de la transacción, cambiar una entidad gestionada hace innecesario
  el `save`.
:::

:::checkpoint
Mueves las reglas al servicio, inyectas el repositorio por constructor,
usas `@Transactional` sabiendo lo que hace y lanzas excepciones de negocio
sin mencionar HTTP.
:::

:::milestone
El defecto número dos del capítulo 17 está resuelto: las reglas salieron del
controlador. La API tiene tres capas y una regla de stock que vive en un
solo lugar.
:::

:::exercise level=1
Escribe `CategoryService` con `listar`, `buscar` y `crear`, rechazando un
nombre duplicado.

:::answer
```java
@Service
public class CategoryService {
    private final CategoryRepository repository;

    public CategoryService(CategoryRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public Category crear(Category nueva) {
        repository.findByNameIgnoreCase(nueva.getName())
                .ifPresent(c -> {
                    throw new DuplicateCategoryException(c.getName());
                });
        return repository.save(nueva);
    }
}
```
:::

:::exercise level=2
Agrega `reajustar(Long id, BigDecimal porcentaje)` al `ProductService`,
rechazando un reajuste que lleve el precio a cero o menos.

:::answer
```java
@Transactional
public Product reajustar(Long id, BigDecimal porcentaje) {
    Product p = buscar(id);
    BigDecimal factor = BigDecimal.ONE
            .add(porcentaje.divide(new BigDecimal("100")));
    BigDecimal nuevo = p.getPrice().multiply(factor);
    if (nuevo.signum() <= 0) {
        throw new IllegalArgumentException("reajuste inválido");
    }
    p.setPrice(nuevo.setScale(2, RoundingMode.HALF_UP));
    return p;
}
```
Ese `setScale` con `HALF_UP` al final no es un detalle: sin él, el resultado
de la multiplicación arrastra decimales que la base va a truncar a su
manera. El redondeo es una decisión de negocio, no del driver.
:::

:::exercise level=3
Imagina que crear un producto también debe registrar un evento en una tabla
de auditoría. Escribe el método y explica qué pasa si falla la grabación de
la auditoría.

:::answer
```java
@Transactional
public Product crear(Product nuevo) {
    Product guardado = repository.save(nuevo);
    auditoria.registrar("CREATE", guardado.getId());
    return guardado;
}
```
Si la auditoría lanza una excepción *unchecked*, la transacción deshace
**las dos** operaciones: el producto no se crea. Eso puede ser el
comportamiento deseado o un desastre (perder la venta porque falló el log).
Es una decisión de negocio, y la forma de separarlas es publicar un evento y
tratarlo en otra transacción, tema que este libro deja como próximo paso.
:::
