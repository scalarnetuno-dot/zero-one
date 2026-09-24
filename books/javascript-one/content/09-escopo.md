---
title: "Escopo"
number: 9
slug: escopo
part: p3
kicker: "A mensagem 'sua entrega chegou' foi para o cliente errado. O nome da entrega do laço continuava existindo depois do laço, com a última entrega dentro."
goal: >-
  Prever onde um nome existe — no bloco, na função, no arquivo —, entender
  o que var faz de diferente de let e const, e reproduzir o nome que vaza
  do laço e leva a notificação para o cliente errado.
---

:::story Sua entrega chegou
Terça, 24 de março, 10h20. A Cláudia repassou a reclamação de uma
floricultura de São Carlos: tinha recebido pelo WhatsApp "sua entrega
chegou" — de uma entrega que ainda estava no caminhão. Dez minutos depois,
a entrega dela chegou, e ninguém avisou.

O Paulo reproduziu em homologação em meia hora. Toda vez que o motorista
marcava várias entregas de uma parada de uma vez, a notificação ia para a
última da lista.

A Bia achou o trecho em `processarEntrega`:

```javascript
for (var i = 0; i < parada.entregas.length; i++) {
  var e = parada.entregas[i];
  marcarEntregue(e);
}
notificarCliente(e);
```

— A notificação está fora do laço — disse ela.

— Está — disse o Rafael.

— E o `e` existe ali fora?

— Com `var`, existe. É o último que o laço deixou.
:::

## Onde um nome existe

Todo nome criado com `const`, `let` ou `function` existe numa região do
código, e só nela. Essa região é o **escopo** do nome. Fora dele, o nome
não existe — e usá-lo dá o `ReferenceError` do capítulo
@cap:primeiro-programa.

Com `let` e `const`, a região é o **bloco**: o trecho entre um par de
chaves.

```javascript title="bloco.js" numbered
const cidade = "Franca";

if (cidade === "Franca") {
  const base = 1890;
  console.log(`dentro: ${base}`);
}

console.log(`fora: ${base}`);
```

```text
$ node bloco.js
dentro: 1890
D:\borba\bloco.js:8
console.log(`fora: ${base}`);
                     ^

ReferenceError: base is not defined
```

`base` nasceu dentro das chaves do `if` e morreu nelas. `cidade`, criado
fora de qualquer chave, existe no arquivo inteiro, inclusive dentro do
`if`: de dentro, enxerga-se para fora; de fora, não se enxerga para
dentro.

:::term Escopo
A região do código em que um nome existe. Com `let` e `const`, é o bloco
entre chaves em que o nome foi criado. Um bloco enxerga os nomes dos
blocos que o contêm; os de fora não enxergam os de dentro.
:::

## O laço também é um bloco

O `for` tem um bloco, e o `let` do cabeçalho pertence a ele:

```javascript title="laco.js" numbered
const entregas = ["E-5101", "E-5102", "E-5103"];

for (let i = 0; i < entregas.length; i++) {
  const e = entregas[i];
  console.log(`marcando ${e}`);
}

console.log(typeof e, typeof i);
```

```text
$ node laco.js
marcando E-5101
marcando E-5102
marcando E-5103
undefined undefined
```

`typeof` de um nome que não existe devolve `"undefined"`, sem erro — é a
única operação que tolera isso. Depois do laço, nem `e` nem `i` existem.
Cada volta criou o seu `e`, e todos morreram com a volta.

## `var`: o escopo é a função

`entrega.js` é de 2022 e usa `var`. O `var` é a forma de criar nome que o
JavaScript teve sozinho até 2015, e ele segue outra regra: o escopo de um
`var` não é o bloco. É a **função inteira** em que ele está — ou o arquivo,
se estiver fora de função.

O trecho da notificação, reproduzido:

```javascript title="notifica.js" numbered
function notificarCliente(e) {
  console.log(`avisando ${e}: sua entrega chegou`);
}

const parada = ["E-5101", "E-5102", "E-5103"];

for (var i = 0; i < parada.length; i++) {
  var e = parada[i];
  console.log(`marcando ${e}`);
}
notificarCliente(e);
console.log(`i depois do laço: ${i}`);
```

```text
$ node notifica.js
marcando E-5101
marcando E-5102
marcando E-5103
avisando E-5103: sua entrega chegou
i depois do laço: 3
```

O `var e` não morreu no fim do laço. Ele é um nome só, do arquivo inteiro,
reatribuído a cada volta. Quando o laço termina, ele guarda o último valor
— E-5103 —, e a linha de fora o usa sem reclamar.

E o `i` continua valendo `3`, a posição depois da última.

Com `let` e `const`, o mesmo trecho:

```javascript title="notifica.js" numbered
for (let i = 0; i < parada.length; i++) {
  const e = parada[i];
  console.log(`marcando ${e}`);
}
notificarCliente(e);
```

```text
marcando E-5101
marcando E-5102
marcando E-5103
D:\borba\notifica.js:11
notificarCliente(e);
                 ^

ReferenceError: e is not defined
```

O erro é a melhor coisa que podia acontecer. Com `var`, o programa roda e
avisa a floricultura errada. Com `const`, ele para na linha em que alguém
tentou usar uma entrega que não existe mais — e o defeito aparece no
primeiro teste, e não na reclamação de um cliente.

A correção de verdade não é trocar `var` por `let`. É perguntar **para
quem** a notificação deveria ir. Para cada entrega marcada:

```javascript
for (const e of parada) {
  marcarEntregue(e);
  notificarCliente(e);
}
```

A notificação entrou no laço. Cada cliente é avisado da própria entrega.

:::key
`var` não respeita o bloco: o nome existe na função inteira, com o último
valor que recebeu. Um `var` criado dentro de um laço e usado depois dele
quase sempre é o último item da lista, lido por engano. O painel novo não
usa `var`. No antigo, cada `var` num laço é uma pergunta.
:::

## Existe antes de ser criado

O `var` tem outra diferença: o nome existe na função **desde a primeira
linha**, mesmo antes da linha que o cria. Vale `undefined` até lá.

```javascript
console.log(prazo);   // undefined
var prazo = 2;
```

`let` e `const` também são registrados antes, mas recusam ser lidos até a
linha em que nascem:

```javascript
console.log(prazo);
let prazo = 2;
```

```text
ReferenceError: Cannot access 'prazo' before initialization
```

Uma leitura antecipada de `var` devolve `undefined` e segue; de `let`, para
com uma mensagem que diz qual nome e por quê.

## O nome sem declaração

A pior forma de criar um nome é não criar:

```javascript
function marcar(entrega) {
  ultimaMarcada = entrega;
}
```

Sem `const`, `let` ou `var`, a atribuição cria o nome **no escopo global**
— visível no arquivo inteiro e em todo outro arquivo carregado na mesma
página. `entrega.js` tem três desses, e um deles, `ultimaMarcada`, é lido
em `lista.js`.

Os arquivos do painel novo começam com uma linha que desliga isso:

```javascript
"use strict";
```

No modo estrito, atribuir a um nome não declarado é `ReferenceError`. Os
módulos — a forma de separar arquivos que o livro usa adiante — já nascem
em modo estrito, sem a linha.

## Sombra

Um nome de dentro pode ter o mesmo nome de um de fora. O de dentro vence,
dentro:

```javascript title="sombra.js" numbered
const e = "E-5101";

function detalhe(e) {
  return `detalhe de ${e}`;
}

console.log(detalhe("E-5200"));
console.log(e);
```

```text
detalhe de E-5200
E-5101
```

O parâmetro `e` da função **faz sombra** ao `e` de fora: dentro da função,
`e` é o parâmetro. Não é erro, e às vezes é o certo. Em `processarEntrega`
há cinco nomes `e` em níveis diferentes, e qual deles uma linha está
lendo depende de quantas chaves ela tem em volta.

:::summary
- Escopo é onde o nome existe. Com `let` e `const`, é o bloco; de dentro
  se enxerga para fora, não o contrário.
- O `let` do laço morre com o laço. O `var` vive na função inteira, com o
  último valor.
- `var` lido antes de criado é `undefined`; `let` e `const` dão
  `ReferenceError`.
- Atribuir sem declarar cria nome global. `"use strict"` transforma isso em
  erro.
- Nome de dentro faz sombra ao de fora com o mesmo nome.
:::

:::exercise level=1
Diga o que cada `console.log` imprime, ou se dá erro:

```javascript
let total = 0;
if (true) {
  let total = 10;
  console.log(total);
}
console.log(total);
```

:::answer
`10` e depois `0`.

O `let total` de dentro do `if` é outro nome, que faz sombra ao de fora
enquanto o bloco dura. O `total` de fora nunca foi tocado.

Com `var` nas duas linhas, seriam `10` e `10`: o `var` de dentro seria o
mesmo nome do de fora, reatribuído.
:::

:::exercise level=2
Este trecho de `entrega.js` monta a lista de avisos. Diga o que ele
imprime e corrija.

```javascript
var avisos = [];
for (var i = 0; i < 3; i++) {
  var codigo = "E-51" + i;
}
avisos.push(codigo);
console.log(avisos);
```

:::answer
Imprime `[ 'E-512' ]`. O `push` está fora do laço e usa o último valor de
`codigo`.

```javascript
const avisos = [];
for (let i = 0; i < 3; i++) {
  const codigo = "E-51" + i;
  avisos.push(codigo);
}
console.log(avisos);
```

```text
[ 'E-510', 'E-511', 'E-512' ]
```

A correção principal é mover o `push` para dentro. A troca para `const`
garante que, se alguém o tirar de lá de novo, o erro aparece na hora.
:::

:::exercise level=3
A Bia quer trocar todo `var` de `entrega.js` por `let` numa tarde, "porque
é só busca e troca". O Rafael pede que ela liste o que pode quebrar
primeiro. Liste.

:::answer
Todo `var` usado **fora do bloco em que nasceu**. Com `let`, ele deixa de
existir lá fora, e a linha que o usava passa a dar `ReferenceError` — o
que pode ser o conserto de um defeito, como a notificação, ou a quebra de
algo que funcionava por acaso.

Todo `var` lido **antes da linha que o cria**. Com `let`, a leitura
antecipada vira erro em vez de `undefined`.

Todo `var` declarado **duas vezes** no mesmo escopo. `var` aceita; `let`
recusa com `SyntaxError`, e o arquivo inteiro para de carregar.

E o `var` do arquivo, fora de função, que no navegador vira propriedade de
`window` e pode ser lido por `lista.js`. Com `let`, deixa de ser.

A troca é boa, e é para ser feita função por função, com a conferência do
capítulo @cap:funcoes em cada uma. Não numa tarde.
:::
