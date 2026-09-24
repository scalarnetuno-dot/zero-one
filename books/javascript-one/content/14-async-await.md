---
title: "async/await"
number: 14
slug: async-await
part: p4
kicker: "A atualização ficou legível. E o frete da E-5302 apareceu na tela como [object Promise]1000."
goal: >-
  Reescrever o fluxo do capítulo anterior com async e await, tratar erro
  com try e catch, apontar a linha em que o programa espera, e reconhecer
  pela saída o await que faltou.
---

:::story [object Promise]
Quarta, 1º de abril. A Bia reescreveu a atualização da linha com `async`
e `await` na terça à noite. De manhã, o Rafael leu sem comentar e aprovou.

Às 10h, o Paulo mandou um print:

```text
E-5302 | a caminho | R$ [object Promise]1000
```

— É 1º de abril — disse a Bia.

— Não é — disse o Paulo. — É a E-5302. Urgente.

A Bia abriu a função. A linha era esta:

```javascript
const frete = buscarFrete(e.codigo) + (e.urgente ? 1000 : 0);
```

— Falta o `await` — disse o Rafael.

— Mas o resto da função tem.

— O resto da função não é esta linha.
:::

## `async` e `await`

O capítulo @cap:promises escreveu passos em sequência com `then`. `async`
e `await` escrevem a mesma coisa com cara de código de cima para baixo:

```javascript title="linha.js" numbered
function buscar(valor, ms) {
  return new Promise((r) => setTimeout(() => r(valor), ms));
}

async function atualizarLinha(codigo) {
  console.log(`pedindo ${codigo}`);
  const status = await buscar("entregue", 120);
  const frete = await buscar(2340, 60);
  console.log(`${codigo} | ${status} | ${frete}`);
  return { status, frete };
}

atualizarLinha("E-5261");
console.log("a chamada devolveu na hora");
```

```text
$ node linha.js
pedindo E-5261
a chamada devolveu na hora
E-5261 | entregue | 2340
```

`async` antes de `function` faz duas coisas: permite usar `await` dentro
dela, e faz a função **sempre devolver uma promessa**. O `return` do fim
cumpre essa promessa.

`await` antes de uma promessa **pausa esta função** até a promessa
terminar, e entrega o valor dela. `status` recebe `"entregue"`, não uma
promessa.

A palavra que importa é *esta*. O `await` não para o programa. A função
`atualizarLinha` fica suspensa na linha do `await`; quem a chamou recebe
uma promessa e segue — e é por isso que "a chamada devolveu na hora" sai
antes da linha da entrega.

:::term await
Pausa a função `async` em que está até a promessa à direita terminar, e
devolve o valor dela. Se a promessa for rejeitada, o `await` lança o erro,
como um `throw` naquela linha.

Fora de uma função `async` — num arquivo comum do Node —, `await` é
`SyntaxError`.
:::

## `try` e `catch`

Com `await`, a promessa rejeitada vira um erro lançado na linha do
`await`. E erro lançado se trata com o `try` que o capítulo
@cap:callbacks disse que não alcançava callbacks — porque agora a espera
acontece **dentro** do bloco:

```javascript title="linha.js" numbered
function falhar(mensagem, ms) {
  return new Promise((_, rejeitar) =>
    setTimeout(() => rejeitar(new Error(mensagem)), ms),
  );
}

async function marcarEntregue(codigo) {
  try {
    await buscar("gravado", 100);
    console.log(`${codigo}: gravado`);
    await falhar("WhatsApp: 503", 100);
    console.log(`${codigo}: notificado`);
  } catch (erro) {
    console.log(`${codigo}: ${erro.message}`);
  }
  console.log(`${codigo}: tela atualizada`);
}

marcarEntregue("E-5230");
```

```text
$ node linha.js
E-5230: gravado
E-5230: WhatsApp: 503
E-5230: tela atualizada
```

A linha depois do `await` que falhou não roda; a execução pula para o
`catch`, e depois segue. A estrutura é a de qualquer código com erro — sem
a convenção do erro primeiro, sem `catch` pendurado no fim de uma cadeia.

## O mesmo fluxo do capítulo anterior

A atualização com rodadas, que o capítulo @cap:promises escreveu com
`Promise.all` e `then`:

```javascript title="tela.js" numbered
const inicio = Date.now();
const t = () => `${String(Date.now() - inicio).padStart(4)} ms`;

function buscar(valor, ms) {
  return new Promise((r) => setTimeout(() => r(valor), ms));
}

let rodadaAtual = 0;

async function atualizar(status, frete, msStatus, msFrete) {
  rodadaAtual++;
  const minha = rodadaAtual;

  const [s, f] = await Promise.all([
    buscar(status, msStatus),
    buscar(frete, msFrete),
  ]);

  if (minha !== rodadaAtual) {
    console.log(`${t()} rodada ${minha} descartada`);
    return;
  }
  console.log(`${t()} rodada ${minha}: ${s} | ${f}`);
}

atualizar("a caminho", 1890, 120, 450);
setTimeout(() => atualizar("entregue", 2340, 120, 60), 200);
```

```text
$ node tela.js
 321 ms rodada 2: entregue | 2340
 451 ms rodada 1 descartada
```

A saída é a mesma do capítulo anterior. O código diz a mesma coisa em
outra ordem de leitura: o `await Promise.all(...)` é a linha em que a
função espera, e tudo abaixo dela acontece depois das duas respostas.

## Esperar em sequência sem precisar

`await` torna fácil escrever uma espera atrás da outra, mesmo quando as
duas não dependem entre si:

```javascript
const status = await buscar("entregue", 120);
const frete = await buscar(2340, 450);
```

Isso leva 570 ms: o pedido do frete só **sai** depois que o status voltou.
Com `Promise.all`, os dois saem juntos e o tempo é o do mais lento, 450
ms. Na tela da manhã, com 160 entregas, a diferença entre esperar uma de
cada vez e esperar todas juntas é a diferença entre um minuto e meio e um
segundo.

A regra: `await` em sequência quando o segundo pedido **precisa** do
resultado do primeiro. Quando não precisa, `Promise.all`.

## O `await` que faltou

A linha da E-5302:

```javascript title="urgente.js" numbered
async function buscarFrete(codigo) {
  return 2340;
}

async function freteDaLinha(e) {
  const frete = buscarFrete(e.codigo) + (e.urgente ? 1000 : 0);
  return frete;
}

freteDaLinha({ codigo: "E-5302", urgente: true })
  .then((f) => console.log(`R$ ${f}`));
```

```text
$ node urgente.js
R$ [object Promise]1000
```

`buscarFrete` é `async`, e por isso devolve uma promessa — mesmo com um
`return 2340` direto. Sem `await`, `frete` recebe a promessa. O `+` com
um objeto de um lado transforma o objeto em texto — `"[object Promise]"` —
e junta o `1000`. É o `+` que junta, do capítulo @cap:operadores, com uma
promessa no lugar do formulário.

Com o `await`:

```javascript
const frete = (await buscarFrete(e.codigo)) + (e.urgente ? 1000 : 0);
```

```text
R$ 3340
```

Os parênteses em volta do `await` deixam claro o que é esperado antes da
soma.

:::pitfall
O `await` que falta não dá erro. Dá um valor errado com cara de valor: um
`[object Promise]` num texto, um `NaN` numa conta, um `if (promessa)` que é
sempre verdadeiro — porque uma promessa é um objeto, e objeto é verdadeiro.

Quando uma saída mostra `[object Promise]`, ou uma condição com uma
chamada `async` sempre dá o mesmo resultado, procure o `await` que falta
na linha em que o valor nasceu.
:::

:::key
`async` faz a função devolver uma promessa, sempre. `await` pausa **só a
função em que está**. Todo valor que vem de uma função `async` precisa de
um `await` — ou de um `then` — antes de ser usado como valor.
:::

:::summary
- `async` permite `await` e faz a função devolver uma promessa.
- `await` pausa a função até a promessa terminar e entrega o valor. O
  programa, fora dela, segue.
- Promessa rejeitada lança o erro na linha do `await`; `try` e `catch`
  tratam como qualquer erro.
- `await` em sequência só quando o segundo precisa do primeiro. Senão,
  `await Promise.all`.
- `await` esquecido não quebra: produz `[object Promise]`, `NaN` ou uma
  condição sempre verdadeira.
:::

:::exercise level=1
Diga o que cada `console.log` imprime:

```javascript
async function frete() {
  return 1890;
}

console.log(frete());
frete().then((v) => console.log(v));
```

:::answer
Primeiro `Promise { 1890 }`, depois `1890`.

A função `async` devolve uma promessa, mesmo retornando um número direto.
O Node mostra a promessa já cumprida com o valor entre chaves. O `then`
recebe o número.
:::

:::exercise level=2
Reescreva com `async` e `await`, mantendo o comportamento:

```javascript
gravarStatus("E-5230")
  .then(() => atualizarLinha("E-5230"))
  .then(() =>
    notificarCliente("E-5230").catch((erro) => {
      console.log(`aviso pendente: ${erro.message}`);
    }),
  )
  .catch((erro) => console.log(`gravação falhou: ${erro.message}`));
```

:::answer
```javascript
async function marcar(codigo) {
  try {
    await gravarStatus(codigo);
    await atualizarLinha(codigo);
  } catch (erro) {
    console.log(`gravação falhou: ${erro.message}`);
    return;
  }

  try {
    await notificarCliente(codigo);
  } catch (erro) {
    console.log(`aviso pendente: ${erro.message}`);
  }
}
```

Dois `try`: um para o que é essencial, que interrompe; outro para a
notificação, que só registra. O `return` no primeiro `catch` impede de
notificar uma entrega que não foi gravada — o que a cadeia original
também impedia, por o `catch` estar no fim.
:::

:::exercise level=3
A tela da manhã faz isto para 160 entregas:

```javascript
for (const e of entregas) {
  e.status = await buscarStatus(e.codigo);
}
```

Cada pedido leva cerca de 300 ms. Diga quanto a lista demora, reescreva, e
diga o que a versão nova precisa tratar que a antiga não precisava.

:::answer
Demora 160 × 300 ms, uns 48 segundos: cada pedido só sai quando o
anterior voltou. A Lívia imprime às 5h35 e a lista ainda está carregando.

```javascript
const resultados = await Promise.allSettled(
  entregas.map((e) => buscarStatus(e.codigo)),
);

resultados.forEach((r, i) => {
  entregas[i].status =
    r.status === "fulfilled" ? r.value : "sem resposta";
});
```

Os 160 pedidos saem juntos, e a lista demora o tempo do mais lento.

O que a versão nova precisa tratar: 160 pedidos ao mesmo tempo contra um
servidor que antes recebia um por vez. Se o servidor da Borba não
aguentar, alguns vão falhar — por isso `allSettled`, e não `all` — e vale
limitar quantos saem de uma vez. E a ordem de chegada deixa de ser a da
lista; o índice `i` é o que devolve cada resposta à sua entrega.
:::
