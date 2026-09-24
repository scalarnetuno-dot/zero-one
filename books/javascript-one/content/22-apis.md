---
title: "APIs"
number: 22
slug: apis
part: p7
kicker: "A página mandava status cancelado. O servidor aceitava CANCELADA. Os dois tinham teste verde, e a entrega nunca foi cancelada no servidor."
goal: >-
  Fazer um pedido com fetch e ler a resposta inteira, status incluído;
  entender por que fetch não falha num 422; e escrever, numa tabela curta,
  o contrato que a página e o servidor vão obedecer.
---

:::story Os dois verdes
Segunda, 20 de abril, 9h30. O Neto fez o que a Bia tinha pedido no ticket
da sexta: pôs no servidor a regra de que entrega cancelada não volta para
a rota. Mostrou o teste dele, verde.

— Manda um cancelamento do painel novo — disse ele. — Para ver no log.

A Bia cancelou a E-5801 na homologação. A linha ficou riscada.

O Neto olhou o log do servidor.

```text
PUT /entregas/E-5801/status  422
```

— Quatrocentos e vinte e dois — disse ele. — Seu painel mandou o quê?

— `status: "cancelado"`.

— O servidor aceita `CANCELADA`. Maiúsculo, feminino.

— O meu teste está verde.

— O meu também.

O Rafael, da mesa ao lado:

— E a linha ficou riscada. Com o servidor dizendo que não cancelou.
:::

## Um pedido e uma resposta

O capítulo @cap:npm deixou a busca de canceladas com `fetch`. O `fetch`
faz um pedido HTTP e devolve uma promessa da resposta:

```javascript
const resposta = await fetch("http://localhost:3000/entregas/E-5801");
console.log(resposta.status);           // 200
const corpo = await resposta.json();    // o conteúdo, lido como JSON
```

A resposta chega em duas partes. Primeiro o **cabeçalho**: o número de
status, os metadados. `resposta.status` já está disponível. O **corpo**
ainda está chegando; `resposta.json()` devolve outra promessa, que cumpre
quando o corpo terminou de chegar e foi lido como JSON. Por isso os dois
`await`.

Para gravar, o pedido leva um método e um corpo:

```javascript
await fetch(`http://localhost:3000/entregas/${codigo}/status`, {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ status }),
});
```

`method: "PUT"` diz que o pedido substitui um valor. `headers` avisa ao
servidor que o corpo é JSON. `body` é o texto do corpo: `JSON.stringify`
transforma o objeto em texto JSON.

## O número diz o que aconteceu

O status HTTP é um número de três dígitos, e o primeiro dígito diz a
família:

| Faixa | Quer dizer | Exemplos do painel |
|---|---|---|
| 2xx | deu certo | `200` gravado |
| 4xx | o pedido tem um problema | `404` não existe, `409` conflito, `422` dado inválido |
| 5xx | o servidor tem um problema | `500` erro interno, `503` indisponível |

Tabela: O `422` diz: o pedido chegou, o formato é JSON, e o que está
dentro não é aceito. O `409` diz: o pedido está certo, e o estado da
entrega não permite.

## O servidor pequeno

Para ver o contrato sendo cobrado, a pasta `borba` ganha um servidor
mínimo, com o módulo `node:http` do próprio Node, que imita a regra que o
Neto pôs em produção:

```javascript title="servidor.js" numbered
import { createServer } from "node:http";

const STATUS = ["SEPARADA", "EM_ROTA", "ENTREGUE", "CANCELADA"];
const entregas = new Map([["E-5801", "SEPARADA"]]);

function responder(res, codigo, corpo) {
  res.writeHead(codigo, { "Content-Type": "application/json" });
  res.end(JSON.stringify(corpo));
}

const servidor = createServer(async (req, res) => {
  const achou = req.url.match(/^\/entregas\/(E-\d+)\/status$/);
  if (req.method !== "PUT" || !achou) {
    return responder(res, 404, { erro: "rota inexistente" });
  }

  let texto = "";
  for await (const pedaco of req) texto += pedaco;
  const { status } = JSON.parse(texto);

  if (!STATUS.includes(status)) {
    return responder(res, 422, {
      erro: "status inválido",
      campo: "status",
      recebido: status,
      aceitos: STATUS,
    });
  }

  const codigo = achou[1];
  if (entregas.get(codigo) === "CANCELADA") {
    return responder(res, 409, { erro: "entrega já cancelada" });
  }
  entregas.set(codigo, status);
  responder(res, 200, { codigo, status });
});

servidor.listen(3000, () => console.log("servidor em :3000"));
```

`createServer` recebe a função que atende cada pedido: `req` é o pedido,
`res` é a resposta a montar. `req.url.match(...)` confere o caminho com uma
expressão regular e captura o código da entrega. O corpo chega em pedaços,
e o `for await` os junta. O resto é o que o capítulo @cap:condicionais
ensinou: recusar o que não vale, cedo, com o motivo.

Num terminal, `node servidor.js`. Noutro, o cliente:

```javascript title="cliente.js" numbered
async function gravarStatus(codigo, status) {
  const resposta = await fetch(
    `http://localhost:3000/entregas/${codigo}/status`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    },
  );
  const corpo = await resposta.json();
  console.log(resposta.status, corpo);
}

await gravarStatus("E-5801", "cancelado");
await gravarStatus("E-5801", "CANCELADA");
await gravarStatus("E-5801", "EM_ROTA");
```

```text
$ node cliente.js
422 {
  erro: 'status inválido',
  campo: 'status',
  recebido: 'cancelado',
  aceitos: [ 'SEPARADA', 'EM_ROTA', 'ENTREGUE', 'CANCELADA' ]
}
200 { codigo: 'E-5801', status: 'CANCELADA' }
409 { erro: 'entrega já cancelada' }
```

O `await` no nível do arquivo, sem função `async` em volta, funciona
porque a pasta é ESM: módulos aceitam `await` solto.

Três pedidos, três respostas que dizem coisas diferentes. O primeiro é o
painel da Bia: recusado, com o campo, o valor recebido e a lista do que
vale. O segundo, o valor certo: gravado. O terceiro é o caso do Paulo, do
capítulo @cap:testes, agora no servidor: a rota não volta depois do
cancelamento.

## `fetch` não falha num 422

O painel da Bia fazia isto:

```javascript
try {
  await fetch(url, { method: "PUT", body: ... });
  marcarComoCancelada(codigo);
} catch (erro) {
  mostrarFalha(codigo);
}
```

O `fetch` só rejeita a promessa quando **não há resposta** — a rede caiu,
o servidor não existe. Um `422`, um `409`, um `500` são respostas. A
promessa cumpre, o `try` segue, e a tela risca a entrega que o servidor
recusou.

:::key
Para o `fetch`, qualquer resposta é sucesso. Quem decide se deu certo é
quem lê o status. `resposta.ok` é `true` para 2xx e `false` para o resto;
conferir `resposta.ok` antes de acreditar é obrigatório.
:::

```javascript title="api.js" numbered
export async function gravarStatus(codigo, status) {
  const resposta = await fetch(`/entregas/${codigo}/status`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });

  const corpo = await resposta.json();
  if (!resposta.ok) {
    const erro = new Error(corpo.erro);
    erro.status = resposta.status;
    erro.corpo = corpo;
    throw erro;
  }
  return corpo;
}
```

A resposta que não é 2xx vira um erro lançado, com o status e o corpo
presos a ele. Quem chama volta a poder usar `try` e `catch` como o
capítulo @cap:async-await ensinou — e a tela só risca a entrega depois que
o servidor disse `200`.

## Os dois verdes

O teste do painel conferia que `cancelar` mandava `{ status: "cancelado" }`.
O teste do servidor conferia que `CANCELADA` era aceito e o resto
recusado. Os dois estavam certos a respeito do que cada um tinha decidido
sozinho. Ninguém tinha escrito o que os **dois** tinham combinado — porque
não tinham combinado nada.

O contrato, escrito na página do repositório, em tabela curta, com a
Cláudia e o Neto na mesma conversa:

| Pedido | Corpo | Respostas |
|---|---|---|
| `PUT /entregas/:codigo/status` | `{ "status": S }` | `200` com a entrega; `404` sem entrega; `409` se cancelada; `422` se `S` inválido |
| valores de `S` | `SEPARADA`, `EM_ROTA`, `ENTREGUE`, `CANCELADA` | maiúsculas, sem acento |
| erro | `{ "erro": texto, "campo"?, "recebido"?, "aceitos"? }` | sempre JSON |

Tabela: O contrato é a regra dos dois lados. O painel pode mostrar
"cancelada" na tela; o que ele manda é `CANCELADA`.

O painel ganhou uma tradução na porta, como a do capítulo
@cap:arrays-e-objetos:

```javascript
const PARA_O_SERVIDOR = {
  separada: "SEPARADA",
  "a caminho": "EM_ROTA",
  entregue: "ENTREGUE",
  cancelada: "CANCELADA",
};
```

E cada lado ganhou um teste a mais, o mesmo: a lista de valores da
tabela. O do painel confere que tudo que ele manda está na lista. O do
servidor confere que tudo na lista é aceito. Quando um dos dois mudar a
lista, o teste do outro não fica verde por acaso.

:::summary
- `fetch(url, opções)` devolve a resposta; `resposta.status` vem
  primeiro, `resposta.json()` é outra promessa.
- 2xx deu certo; 4xx o pedido tem problema; 5xx o servidor tem. `422` é
  dado inválido; `409`, estado que não permite.
- `fetch` só rejeita sem resposta. `422` cumpre a promessa: confira
  `resposta.ok`.
- Dois lados com testes verdes podem discordar. O contrato escrito — rota,
  corpo, valores, respostas — é o que os dois obedecem.
- A tela fala a língua dela; na porta, traduz para a do contrato.
:::

:::exercise level=1
Diga o que o painel deve fazer ao receber cada resposta a um
cancelamento:

1. `200`
2. `409 { erro: "entrega já cancelada" }`
3. `422 { campo: "status", recebido: "cancelado" }`
4. a rede caiu, sem resposta.

:::answer
1. Riscar a entrega.
2. Riscar também: ela **já** está cancelada, e é o estado que a Lívia
   queria. Vale avisar que outra pessoa cancelou antes.
3. Não riscar, e registrar como defeito do painel: um `422` para um valor
   que o painel monta sozinho é o painel fora do contrato.
4. Não riscar, e mostrar que o cancelamento não foi enviado, com um jeito
   de tentar de novo.

Só o 4 chega ao `catch` do `fetch` sem o `resposta.ok`. Os outros três
cumprem a promessa.
:::

:::exercise level=2
Escreva o teste do painel que confere que todo valor de `PARA_O_SERVIDOR`
está na lista do contrato.

:::answer
```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { PARA_O_SERVIDOR } from "../api.js";

const CONTRATO = ["SEPARADA", "EM_ROTA", "ENTREGUE", "CANCELADA"];

test("o painel só manda status do contrato", () => {
  for (const valor of Object.values(PARA_O_SERVIDOR)) {
    assert.ok(CONTRATO.includes(valor), `${valor} fora do contrato`);
  }
});
```

`Object.values` devolve os valores do objeto. `assert.ok` confere que a
expressão é verdadeira, e a mensagem diz qual valor falhou.

A lista `CONTRATO` está copiada no teste. O ideal é os dois lados lerem a
lista de um arquivo só; enquanto o servidor e o painel estiverem em
repositórios diferentes, a cópia com teste dos dois lados é o que avisa
quando uma delas mudar.
:::

:::exercise level=3
O Marcos propõe que o servidor "seja tolerante": aceite `cancelado`,
`cancelada`, `CANCELADO` e `CANCELADA`, e converta. Responda, com o que
isso resolve e o que custa.

:::answer
Resolve o `422` desta semana: o painel da Bia passaria a funcionar sem
mudar.

Custa o contrato. Cada variação aceita é uma que algum cliente vai passar a
mandar, e que o servidor vai precisar aceitar para sempre — o aplicativo
do motorista, o sistema antigo, o próximo que integrar. A tabela de quatro
valores vira uma lista de dezesseis, e a pergunta "o que o painel manda?"
deixa de ter resposta.

E esconde o defeito: o painel que mandava `cancelado` continua mandando.
O `422` com `recebido` e `aceitos` é o servidor fazendo o trabalho dele —
dizer exatamente o que está errado. A tradução fica em quem conhece a
própria língua: a porta do painel.
:::
