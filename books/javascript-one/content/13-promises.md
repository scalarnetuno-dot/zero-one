---
title: "Promises"
number: 13
slug: promises
part: p4
kicker: "A tela mostrava o frete de antes do ajuste ao lado do status de depois. As duas respostas chegaram, cada uma na sua hora, e cada uma escreveu por cima da outra."
goal: >-
  Criar e consumir uma Promise, encadear then e catch, explicar por que
  três pedidos terminam fora da ordem em que foram feitos, e juntar
  respostas que precisam aparecer juntas com Promise.all.
---

:::story Frete velho, status novo
Terça, 31 de março, 11h. A Cláudia ajustou o frete da E-5261 de R$ 18,90
para R$ 23,40 — a loja tinha pedido entrega em outra doca — e, no mesmo
minuto, o motorista marcou a entrega como "entregue".

Na tela da Lívia, a linha ficou assim por cinco segundos:

```text
E-5261 | entregue | R$ 18,90
```

Depois, na atualização seguinte:

```text
E-5261 | entregue | R$ 23,40
```

— Cinco segundos — disse a Cláudia. — Qual o problema?

— A Mercado Leste confere o frete pela tela — disse a Bia. — Se o print
sai nesses cinco segundos, o frete da entrega entregue está errado.

O Rafael abriu o trecho da atualização:

```javascript
buscarStatus(e.codigo).then((s) => { linha.status = s; mostrar(); });
buscarFrete(e.codigo).then((f) => { linha.frete = f; mostrar(); });
```

— Dois pedidos — disse ele. — Saem juntos. Cada um volta quando volta.

— E o frete voltou da réplica do banco, que estava atrasada.

— Voltou. E escreveu na tela como se fosse o de agora.
:::

## Uma promessa de valor

O capítulo @cap:callbacks passava uma função para ser chamada depois. A
`Promise` inverte o arranjo: a função que vai demorar **devolve um
objeto** que representa o resultado futuro. Quem chamou decide, nesse
objeto, o que fazer quando o valor chegar.

```javascript title="promessa.js" numbered
function buscarFrete(codigo) {
  return new Promise((resolver) => {
    setTimeout(() => {
      resolver(2340);
    }, 300);
  });
}

const promessa = buscarFrete("E-5261");
console.log(promessa);

promessa.then((frete) => {
  console.log(`frete: ${frete}`);
});
```

```text
$ node promessa.js
Promise { <pending> }
frete: 2340
```

`new Promise(...)` recebe uma função que faz o trabalho demorado. Essa
função recebe `resolver`: quando o trabalho termina, chama-se `resolver`
com o valor. A promessa, que estava **pendente**, passa a **cumprida**.

`console.log(promessa)` mostra `Promise { <pending> }`: no momento da
linha, o valor ainda não existe. Não é o frete. É a promessa dele.

`.then(função)` registra o que fazer com o valor quando ele chegar.

:::term Promise
Um objeto que representa um valor que ainda não existe. Ela começa
pendente, e termina cumprida — com um valor — ou rejeitada — com um erro.
`then` recebe o valor; `catch` recebe o erro.

Uma promessa termina uma vez só. Cumprida não volta a ser pendente.
:::

## Rejeitar e `catch`

O trabalho pode falhar. A função da promessa recebe um segundo argumento,
`rejeitar`:

```javascript title="promessa.js" numbered
function buscarFrete(codigo) {
  return new Promise((resolver, rejeitar) => {
    setTimeout(() => {
      if (!codigo.startsWith("E-")) {
        rejeitar(new Error(`código inválido: ${codigo}`));
        return;
      }
      resolver(2340);
    }, 300);
  });
}

buscarFrete("5261")
  .then((frete) => console.log(`frete: ${frete}`))
  .catch((erro) => console.log(`falhou: ${erro.message}`));
```

```text
$ node promessa.js
falhou: código inválido: 5261
```

`.catch` recebe o erro de qualquer ponto anterior da cadeia. Não existe o
risco do capítulo anterior, de chamar o callback duas vezes: uma promessa
termina uma vez, e o segundo `resolver` ou `rejeitar` é ignorado.

## Encadear

`then` devolve **outra promessa**, com o valor que a função dele devolver.
Isso permite escrever passos em sequência, sem a pirâmide:

```javascript
gravarStatus("E-5230")
  .then(() => atualizarLinha("E-5230"))
  .then(() => notificarCliente("E-5230"))
  .catch((erro) => console.log(`falhou: ${erro.message}`));
```

Se `gravarStatus` devolve uma promessa, o primeiro `then` espera por ela.
Se a função dentro de um `then` devolve uma promessa — `notificarCliente`,
por exemplo —, o `then` seguinte espera por essa. A cadeia lê de cima
para baixo, na ordem em que as coisas acontecem.

E um `catch` no fim pega a falha de qualquer um dos três.

:::pitfall
Dentro de um `then`, **devolver** a promessa é o que faz a cadeia esperar:

```javascript
.then(() => { notificarCliente("E-5230"); })
```

Com chaves e sem `return`, a função devolve `undefined`. O `then` seguinte
não espera a notificação, e uma falha dela não chega ao `catch`: vira um
aviso de "promessa rejeitada sem tratamento" no console, longe da cadeia.
A forma sem chaves — `() => notificarCliente(...)` — devolve sozinha.
:::

## Fora de ordem

O trecho da tela fazia dois pedidos **independentes**. Com tempos
reproduzidos da homologação — o status em 120 ms, o frete da réplica em
450 —, e a atualização automática a cada 5 segundos:

```javascript title="tela.js" numbered
const inicio = Date.now();
const t = () => `${String(Date.now() - inicio).padStart(4)} ms`;
const linha = {};

function mostrar(origem) {
  console.log(`${t()} ${origem}: ${linha.status} | ${linha.frete}`);
}

function buscar(valor, ms) {
  return new Promise((r) => setTimeout(() => r(valor), ms));
}

function status(s) {
  linha.status = s;
  mostrar("status");
}

function frete(f) {
  linha.frete = f;
  mostrar("frete");
}

// 11h00: "a caminho", frete 1890 (a réplica lenta)
buscar("a caminho", 120).then(status);
buscar(1890, 450).then(frete);

// 200 ms depois: entregue, frete já ajustado para 2340
setTimeout(() => {
  buscar("entregue", 120).then(status);
  buscar(2340, 60).then(frete);
}, 200);
```

```text
$ node tela.js
 120 ms status: a caminho | undefined
 262 ms frete: a caminho | 2340
 323 ms status: entregue | 2340
 450 ms frete: entregue | 1890
```

A última linha é a tela da Lívia. O frete de **antes** do ajuste — pedido
primeiro, à réplica lenta — chegou **por último**, e escreveu por cima do
frete de depois. A tela termina com status novo e frete velho, e fica assim
até a próxima rodada.

Nenhum pedido falhou. Cada um fez o que devia. O defeito é que a tela
aceita qualquer resposta, na ordem em que chega, sem saber de que rodada
ela é.

## `Promise.all`: o que precisa chegar junto

Status e frete de uma entrega são mostrados juntos. Então são esperados
juntos:

```javascript
Promise.all([buscarStatus(codigo), buscarFrete(codigo)])
  .then(([status, frete]) => {
    linha.status = status;
    linha.frete = frete;
    mostrar("rodada");
  });
```

`Promise.all` recebe uma lista de promessas e devolve **uma** promessa,
que cumpre quando **todas** cumprirem, com a lista dos valores na mesma
ordem. A desestruturação do capítulo @cap:desestruturacao-e-spread separa
os dois. Se qualquer uma rejeitar, a do `all` rejeita, e nenhuma metade é
escrita.

E, para a rodada antiga não escrever por cima da nova, cada rodada leva um
número, e a tela só aceita a mais recente:

```javascript title="tela.js" numbered
let rodadaAtual = 0;

function atualizar(status, frete, msStatus, msFrete) {
  rodadaAtual++;
  const minha = rodadaAtual;

  Promise.all([buscar(status, msStatus), buscar(frete, msFrete)])
    .then(([s, f]) => {
      if (minha !== rodadaAtual) {
        console.log(`${t()} rodada ${minha} descartada`);
        return;
      }
      linha.status = s;
      linha.frete = f;
      mostrar(`rodada ${minha}`);
    });
}

atualizar("a caminho", 1890, 120, 450);
setTimeout(() => atualizar("entregue", 2340, 120, 60), 200);
```

```text
$ node tela.js
 321 ms rodada 2: entregue | 2340
 451 ms rodada 1 descartada
```

A rodada 2 chega primeiro e é mostrada inteira. A rodada 1 chega depois,
percebe que já não é a atual, e se descarta. A tela nunca mostra uma
metade de cada.

:::key
Pedidos que saem juntos não voltam na ordem em que saíram. O que precisa
aparecer junto é esperado junto, com `Promise.all`. E uma resposta que
chega depois de outra mais nova precisa saber que é velha — ninguém mais
vai avisar.
:::

:::summary
- Uma `Promise` representa um valor futuro: pendente, depois cumprida ou
  rejeitada, uma vez só.
- `then` recebe o valor e devolve outra promessa; `catch` recebe o erro de
  qualquer ponto da cadeia.
- Dentro de um `then`, devolver a promessa faz a cadeia esperar. Sem
  `return`, ela segue e o erro escapa.
- Pedidos independentes terminam em qualquer ordem. A resposta velha
  escreve por cima da nova se ninguém a impedir.
- `Promise.all` espera todas e rejeita se uma falhar. Um número de rodada
  descarta a resposta que chegou tarde.
:::

:::exercise level=1
Diga a ordem das linhas:

```javascript
const p = new Promise((r) => r("pronto"));
p.then((v) => console.log(v));
console.log("depois do then");
```

:::answer
`depois do then`, e só então `pronto`.

A promessa já nasce cumprida, mas o `then` nunca chama a função na hora:
ele a agenda para depois do código que está rodando. É a mesma regra do
`setTimeout` com zero, com uma prioridade um pouco maior.
:::

:::exercise level=2
Escreva a cadeia que grava o status, depois atualiza a linha, e depois
notifica — com a falha da notificação **não** impedindo nada e apenas
registrando um aviso, e a falha da gravação indo para o `catch` do fim.

:::answer
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

O `catch` colado à notificação trata só a falha dela, e devolve uma
promessa cumprida: a cadeia de fora segue como se a notificação tivesse
dado certo. O `catch` do fim fica para a gravação e a atualização. É a
decisão da Cláudia do capítulo @cap:callbacks, sem pirâmide.
:::

:::exercise level=3
A tela da manhã pede o status das 160 entregas com `Promise.all`. Uma delas
dá erro no servidor. Diga o que a Lívia vê, e proponha outra forma.

:::answer
Vê nada. `Promise.all` rejeita quando uma das 160 falha, e o `then` não
roda: a lista inteira fica sem atualizar por causa de uma entrega.

A alternativa é `Promise.allSettled`, que espera todas e devolve, para
cada uma, se cumpriu ou falhou:

```javascript
Promise.allSettled(codigos.map(buscarStatus)).then((resultados) => {
  resultados.forEach((r, i) => {
    if (r.status === "fulfilled") {
      mostrarStatus(codigos[i], r.value);
    } else {
      mostrarFalha(codigos[i]);
    }
  });
});
```

159 linhas atualizam; uma mostra que falhou. `Promise.all` é para o que
precisa chegar inteiro — o status e o frete **da mesma entrega**. Para uma
lista de entregas independentes, cada uma vale sozinha.
:::
