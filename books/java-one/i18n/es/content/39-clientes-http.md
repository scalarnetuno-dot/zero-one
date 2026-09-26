---
source_hash: 4e7a8145ee01
title: "Clientes HTTP"
number: 39
part: p9
kicker: "La herramienta importa menos que el hábito de guardar la petición junto al código que la atiende."
goal: >-
  Ejercitar la API con `curl`, archivos `.http` y colecciones de Postman, y
  organizarlo de una forma que sobreviva a la salida de quien lo escribió.
---

Ya usas `curl` desde el capítulo 17 y la interfaz de Swagger desde el 38.
Este capítulo es corto y trata de una sola cosa: dónde viven esas
peticiones.

## `curl`: el denominador común

```bash title="Lo que necesitas saber de curl" numbered
# GET simple
curl localhost:8080/products/1

# con las cabeceras de la respuesta
curl -i localhost:8080/products/999

# POST con JSON
curl -X POST localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Cable","price":19.90,"quantity":3}'

# con token
curl localhost:8080/orders/mios \
  -H "Authorization: Bearer $TOKEN"

# guardando el token en una variable
TOKEN=$(curl -s -X POST localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aurora.com","password":"admin123"}' \
  | jq -r .token)
```

La última línea usa `jq`, que lee JSON en la línea de comandos. Vale la pena
instalarlo: convierte "copiar el token con el mouse" en un paso
automatizable.

:::tip
`curl` está en todas partes: en tu terminal, en el servidor de producción,
en el contenedor, en el ejemplo que alguien va a pegar en un ticket. Por eso
sigue siendo la forma más universal de describir una petición, incluso para
quien usa una herramienta gráfica en el día a día.
:::

## Archivos `.http`: la petición versionada

```http title="src/test/http/products.http"
@host = http://localhost:8080
@token = {{login.response.body.token}}

### login
# @name login
POST {{host}}/auth/login
Content-Type: application/json

{ "email": "admin@aurora.com", "password": "admin123" }

### listar productos
GET {{host}}/products?page=0&size=5

### crear producto
POST {{host}}/products
Content-Type: application/json
Authorization: Bearer {{token}}

{
  "name": "Teclado mecánico",
  "price": 349.90,
  "quantity": 12
}

### borrar
DELETE {{host}}/products/1
Authorization: Bearer {{token}}
```

IntelliJ y VS Code (con la extensión REST Client) ejecutan ese archivo con
un clic en cada `###`. Y tiene la propiedad que ninguna herramienta gráfica
tiene: **vive en el repositorio**, al lado del controlador que atiende las
rutas.

:::key
Una petición versionada junto al código es documentación ejecutable. Quien
llega al proyecto mañana abre el archivo, lo corre y ve la API funcionando,
sin instalar nada, sin pedirle una colección a nadie, sin adivinar el
formato del cuerpo.
:::

## Postman e Insomnia

Las herramientas gráficas ganan en tres cosas: historial de respuestas,
entornos con un clic (local, pruebas, producción) y pruebas encadenadas que
extraen valores de una respuesta para la petición siguiente.

```javascript title="Postman: guardando el token después del login"
// pestaña Tests de la petición de login
const json = pm.response.json();
pm.environment.set("token", json.token);

pm.test("el login devuelve 200", function () {
    pm.response.to.have.status(200);
});
```

Y pierden en una, que suele salir cara:

:::pitfall
La colección vive en la máquina de quien la creó. Cuando esa persona se va
de vacaciones —o de la empresa—, el equipo descubre que la única descripción
funcional de la API estaba en una cuenta personal de una herramienta de
terceros. Exporta la colección como JSON y **versiónala junto al proyecto**,
o usa el archivo `.http`, que ya nace versionado.
:::

| Herramienta | Gana en | Pierde en |
|---|---|---|
| `curl` | universal, automatizable | ilegible cuando crece |
| `.http` | versionado, dentro del IDE | sin historial, sin interfaz |
| Postman | entornos, encadenamiento, equipo | vive fuera del repositorio |
| Swagger UI | siempre al día, cero configuración | solo lo que expone la API |

Tabla: No elijas una. Usa `curl` para el ejemplo del ticket, `.http` para el
día a día, Postman cuando haya equipo y Swagger para quien llega de afuera.

## Un paso más: generar el cliente

```bash title="A partir del /v3/api-docs del capítulo 38"
npx @openapitools/openapi-generator-cli generate \
  -i http://localhost:8080/v3/api-docs \
  -g typescript-axios \
  -o ./client
```

El equipo de front recibe una biblioteca tipada, con un método por endpoint,
generada a partir de la especificación. Cuando un campo cambie de nombre, el
código del front deja de compilar, en vez de mostrar `undefined` en la
pantalla, como en el incidente del capítulo 36.

:::story La colección de Carlos
La integración con el socio llevaba tres días trabada.

El socio decía que `POST /orders` devolvía `400`. Aurora decía que
funcionaba. Los dos tenían razón: el socio enviaba `customerId` como texto,
y la API esperaba un número.

Nadie podía comparar porque nadie tenía la misma petición. Cada persona
tenía la suya, armada de memoria, en una herramienta distinta.

Carlos tenía una colección de Postman con todo funcionando: la que usaba
desde el capítulo 17. Solo que la colección estaba en su cuenta personal,
que solo tenía la sesión abierta en su computadora, que estaba en el taller
con la pantalla rota.

El cuarto día, Marina creó el archivo `products.http` en el repositorio, con
las once peticiones. Le llevó veinte minutos. El socio clonó el proyecto,
abrió el archivo, lo corrió, vio el cuerpo correcto y lo resolvió en cinco
minutos.

El archivo sigue ahí. Ya lo usaron siete personas que nunca hablaron con
Carlos.
:::

:::summary
- `curl` es universal; `jq` convierte la respuesta en algo automatizable.
- El archivo `.http` vive en el repositorio, al lado del código que
  ejercita.
- Postman gana en entornos y encadenamiento, y desaparece con quien lo
  creó: expórtalo y versiónalo.
- La especificación del capítulo 38 genera clientes tipados
  automáticamente.
:::

:::checkpoint
Ejercitas la API por las cuatro vías, guardas las peticiones en el
repositorio y sabes por qué la colección personal es un punto único de
falla.
:::

:::milestone
Cualquier persona puede ejercitar la API en cualquier máquina, sin una
conversación previa. Falta la última pieza de herramientas: la que registra
por qué el código es como es.
:::

:::exercise level=1
Crea `src/test/http/products.http` con las cinco peticiones del CRUD y
córrelas desde el editor.

:::answer
Empieza por el login y usa `{{login.response.body.token}}` en las demás. El
encadenamiento es lo que convierte el archivo en un guion: una ejecución de
arriba abajo ejercita la API entera.
:::

:::exercise level=2
Escribe un script `bash` que haga login, cree un producto, lo busque, lo
borre y confirme el `404`. Haz que falle con un código de salida distinto de
cero si algún paso no devuelve el estado esperado.

:::answer
`curl -f -s -o /dev/null -w "%{http_code}"` devuelve el estado y permite
comparar. Un script así es una prueba de humo: corre contra el entorno de
pruebas después de cada deploy y responde, en diez segundos, si la
aplicación arrancó entera.
:::

:::exercise level=3
Genera un cliente TypeScript a partir de `/v3/api-docs` e inspecciona el
código producido. Después renombra un campo del DTO, genera de nuevo y
compara.

:::answer
El diff muestra exactamente lo que se rompió para quien consume. Es la forma
más concreta de ver el costo de un cambio de contrato, y el argumento más
convincente que existe a favor del versionado de API, un tema que este
libro deja como próximo paso.
:::
