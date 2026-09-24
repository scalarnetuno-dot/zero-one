---
title: "Condicionais"
number: 6
slug: condicionais
part: p2
kicker: "A entrega E-5012 aparecia como entregue e como cancelada. Dois ifs rodaram, e nenhum deles sabia do outro."
goal: >-
  Escrever decisões com if, else if e else; usar switch só quando o status
  é de fato um conjunto fechado; sair cedo de uma função; e recusar um par
  de estados que não pode existir.
---

:::story Entregue e cancelada
Quinta, 19 de março. O Paulo pôs dois monitores lado a lado na mesa da
Bia. No da esquerda, a lista da manhã: E-5012, **entregue**, 7h48. No da
direita, o detalhe da mesma entrega: **cancelada**, 7h51.

— Qual das duas? — perguntou ele.

A Bia abriu o trecho que monta o texto do status:

```javascript
let rotulo = "a caminho";
if (e.entregue) {
  rotulo = "entregue";
}
if (e.cancelada) {
  rotulo = "cancelada";
}
```

— O motorista marcou entregue às 7h48 — disse ela. — Às 7h51 a loja
ligou para cancelar, e a central marcou cancelada. Os dois campos estão
`true`.

— E a lista?

— A lista usa outro trecho. Testa `entregue` por último.

O Paulo desligou o monitor da direita.

— Então depende de qual tela você abrir.
:::

## `if`, `else if`, `else`

```javascript title="rotulo.js" numbered
const status = "a caminho";

if (status === "entregue") {
  console.log("Entregue");
} else if (status === "cancelada") {
  console.log("Cancelada");
} else {
  console.log("Em rota");
}
```

```text
$ node rotulo.js
Em rota
```

O JavaScript testa as condições de cima para baixo e executa **só o
primeiro bloco** cuja condição é verdadeira. Os outros são pulados, mesmo
que as condições deles também fossem verdadeiras. O `else` pega o que
sobrou.

As chaves delimitam cada bloco. Com uma linha só dentro, dá para omiti-las
— e o painel novo não omite. Uma segunda linha acrescentada depois, sem
chaves, fica fora do `if` e roda sempre, com o recuo mentindo que está
dentro.

## Dois `if` não são uma escolha

O trecho do rótulo tinha dois `if` separados. Cada um é uma decisão
independente. O segundo roda **sempre**, tenha o primeiro rodado ou não:

```javascript title="rotulo.js" numbered
const e = { entregue: true, cancelada: true };

let rotulo = "a caminho";
if (e.entregue) {
  rotulo = "entregue";
}
if (e.cancelada) {
  rotulo = "cancelada";
}
console.log(rotulo);
```

```text
cancelada
```

E a lista, com a ordem invertida, respondia `entregue`. As duas telas
estavam corretas em relação ao próprio código. Cada uma escolheu, sem
dizer, qual `if` vence — pela ordem em que foram escritos.

O problema de fundo não é o `if`. É que a entrega guarda a situação em
**dois campos booleanos**, e dois booleanos têm quatro combinações:

| `entregue` | `cancelada` | Faz sentido? |
|---|---|---|
| `false` | `false` | sim: em rota |
| `true` | `false` | sim: entregue |
| `false` | `true` | sim: cancelada |
| `true` | `true` | **não** |

Tabela: A quarta linha é o estado impossível. O código de 2022 não o
recusa; cada tela o resolve do seu jeito.

## Uma função, um estado

O painel novo decide a situação **num lugar só**, e recusa a combinação
que não existe:

```javascript title="situacao.js" numbered
function situacao(e) {
  if (e.entregue && e.cancelada) {
    throw new Error(`${e.codigo}: entregue e cancelada`);
  }
  if (e.cancelada) {
    return "cancelada";
  }
  if (e.entregue) {
    return "entregue";
  }
  return "a caminho";
}

console.log(situacao({ codigo: "E-5010", entregue: true }));
console.log(situacao({ codigo: "E-5011" }));
const e5012 = { codigo: "E-5012", entregue: true, cancelada: true };
console.log(situacao(e5012));
```

```text
$ node situacao.js
entregue
a caminho
D:\borba\situacao.js:3
    throw new Error(`${e.codigo}: entregue e cancelada`);
    ^

Error: E-5012: entregue e cancelada
```

Três coisas nessa função.

**Cada `if` termina com `return`.** O `return` sai da função. Quando o
primeiro caso aplicável devolve, os de baixo não rodam. Os `if` separados
voltam a ser uma escolha, porque só um deles chega ao fim.

**O caso impossível vem primeiro, e para tudo.** `throw new Error(...)`
interrompe o programa com uma mensagem. É o que se quer: uma entrega nesse
estado não deve ganhar um rótulo qualquer. Deve chegar a alguém que decida
se ela foi entregue ou cancelada.

**`undefined` conta como falso.** A E-5011 não tem nenhum dos dois campos,
e cai no `return` do fim.

:::key
Quando dois `if` atribuem à mesma variável, pergunte: os dois podem ser
verdadeiros ao mesmo tempo? Se podem, e só um deveria valer, a decisão
está sendo tomada pela ordem das linhas — e outra tela, escrita em outra
ordem, vai decidir diferente.
:::

A Cláudia levou a E-5012 à Lívia. A resposta foi que "entregue" vence: a
mercadoria já estava na loja. A regra ficou escrita num comentário acima
da função, com a data da conversa. O `throw` continuou: a próxima entrega
nesse estado precisa ser conferida, não adivinhada.

## `switch`, para conjunto fechado

Quando a mesma variável é comparada com vários valores fixos, o `switch`
diz isso de uma vez:

```javascript title="cor.js" numbered
function cor(situacao) {
  switch (situacao) {
    case "a caminho":
      return "azul";
    case "entregue":
      return "verde";
    case "cancelada":
      return "cinza";
    default:
      throw new Error(`situação desconhecida: ${situacao}`);
  }
}

console.log(cor("entregue"));
```

```text
verde
```

Cada `case` compara com `===`. O `default` pega o que não bateu com
nenhum. O `switch` só vale a pena quando o conjunto é **fechado** — a
lista de situações que a própria função `situacao` produz. Para faixas de
valor ("frete acima de R$ 100"), é `if`.

:::pitfall
Sem `return` ou `break` no fim de um `case`, a execução **continua** no
`case` de baixo:

```javascript
switch (situacao) {
  case "entregue":
    total += 1;
  case "cancelada":
    canceladas += 1;
}
```

Uma entrega entregue soma um em `total` e um em `canceladas`. O
`entrega.js` de 2022 tem dois `switch` assim. Um deles é de propósito, com
comentário. O outro, ninguém sabe.
:::

## A forma curta

Para escolher entre dois **valores**, há o operador condicional:

```javascript
const texto = e.urgente ? "URGENTE" : "normal";
```

Condição, `?`, o valor se verdadeira, `:`, o valor se falsa. Serve para
valor, numa linha. Encadear dois — `a ? x : b ? y : z` — é um `if` com
`else if` escrito de um jeito que ninguém lê às 5h40.

:::summary
- `if` / `else if` / `else` executa só o primeiro bloco verdadeiro. Chaves
  sempre.
- Dois `if` que atribuem à mesma variável decidem pela ordem das linhas.
  Numa função, cada caso termina em `return`.
- Dois booleanos têm quatro combinações. A que não existe é recusada com
  `throw`, não resolvida calada.
- `switch` para conjunto fechado, com `default` que recusa o desconhecido.
  Sem `return` ou `break`, o `case` escorre para o de baixo.
- `? :` escolhe entre dois valores. Não encadeie.
:::

:::exercise level=1
Diga o que `situacao` devolve em cada caso:

```javascript
situacao({ codigo: "A", entregue: false, cancelada: false });
situacao({ codigo: "B", cancelada: true });
situacao({ codigo: "C", entregue: "sim" });
situacao({ codigo: "D", entregue: 0, cancelada: 1 });
```

:::answer
`"a caminho"`, `"cancelada"`, `"entregue"` e `"cancelada"`.

O caso C mostra que a condição aceita qualquer valor verdadeiro, não só
`true`: `"sim"` é verdadeiro. O caso D, que `0` é falso e `1` é
verdadeiro. Se o aplicativo mandar `"false"` como texto, a entrega aparece
entregue — um motivo a mais para converter na entrada.
:::

:::exercise level=2
Reescreva com uma cadeia de `if` e `return`, e diga qual defeito sai
junto:

```javascript
let prioridade = "normal";
if (e.urgente) prioridade = "alta";
if (e.cliente === "Mercado Leste") prioridade = "contrato";
if (e.cancelada) prioridade = "nenhuma";
```

:::answer
```javascript
function prioridade(e) {
  if (e.cancelada) {
    return "nenhuma";
  }
  if (e.cliente === "Mercado Leste") {
    return "contrato";
  }
  if (e.urgente) {
    return "alta";
  }
  return "normal";
}
```

Sai a dependência escondida da ordem. No original, uma entrega urgente da
Mercado Leste virava "contrato" porque a linha dela estava depois; ninguém
decidiu isso. Na função, a ordem dos `return` é a regra, lida de cima para
baixo: cancelada não tem prioridade, contrato vem antes de urgência. Se a
Cláudia quiser outra ordem, é essa lista que ela discute.
:::

:::exercise level=3
O aplicativo novo do motorista vai mandar a situação num campo só,
`status`, com os valores `"rota"`, `"entregue"` e `"cancelada"`. O antigo
continua mandando os dois booleanos por mais três semanas. Escreva uma
função que aceite os dois formatos e devolva uma situação só.

:::answer
```javascript
function situacaoDe(e) {
  if (e.status !== undefined) {
    switch (e.status) {
      case "rota":
        return "a caminho";
      case "entregue":
        return "entregue";
      case "cancelada":
        return "cancelada";
      default:
        throw new Error(`${e.codigo}: status ${e.status}`);
    }
  }
  return situacao(e);
}
```

Se o campo novo existe, ele manda. Se não, a função antiga decide, com a
recusa do estado impossível. O `default` recusa um valor que o aplicativo
novo inventar sem avisar. Daqui a três semanas, a segunda metade sai — e
a função continua sendo o único lugar em que a situação é decidida.
:::
