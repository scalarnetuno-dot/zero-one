---
title: "Funções"
number: 8
slug: funcoes
part: p3
kicker: "Cento e oitenta e sete linhas, oito responsabilidades, e um comentário na última pedindo para ninguém mexer. O Rafael deixou tirar uma."
goal: >-
  Declarar uma função, passar argumentos, devolver um valor, e tirar uma
  responsabilidade de processarEntrega com nome e saída visível — sem
  limpar as outras cento e oitenta linhas no mesmo dia.
---

:::story Cento e oitenta e sete
Segunda, 23 de março, 14h. A Bia abriu `entrega.js` e rolou até
`processarEntrega`. Contou as linhas no editor.

— Cento e oitenta e sete.

O Rafael puxou a cadeira.

— Lê em voz alta o que ela faz. Só os verbos.

A Bia foi descendo.

— Valida o código. Calcula o prazo. Muda o status. Formata o endereço.
Grava log. Chama a API do aplicativo. Manda a notificação. Atualiza a
linha na tela. — Parou. — E aqui no meio, na linha 94, calcula o frete.

— Oito.

— E no fim:

```javascript
  // NÃO MEXER. FUNCIONA.
}
```

— Posso reescrever?

— Não. — O Rafael apontou a linha 94. — Pode tirar isso. Uma coisa. Com
nome. E com um jeito de ver que ela dá o mesmo resultado que dava antes.

— E o comentário?

— Fica. Ele não está errado. Está velho.
:::

## O que uma função é

Uma função é um trecho de código com nome, que recebe valores, faz um
trabalho e devolve um resultado:

```javascript title="dobro.js" numbered
function dobro(valor) {
  return valor * 2;
}

console.log(dobro(1890));
console.log(dobro(720));
```

```text
$ node dobro.js
3780
1440
```

`function dobro(valor)` declara a função: o nome é `dobro`, e ela recebe
um **parâmetro**, `valor`. Na chamada, `dobro(1890)`, o `1890` é o
**argumento**: o valor que ocupa o parâmetro nessa chamada. `return`
devolve o resultado e encerra a função.

:::anatomy title="As partes de uma função"
lang: javascript
code: |
  function dobro(valor) {
    return valor * 2;
  }
notes:
  - { line: 1, text: "`function` e o nome. O nome é um verbo ou diz o que volta: `dobro`, `calcularFrete`." }
  - { line: 1, text: "Entre parênteses, os parâmetros: nomes que só existem dentro da função." }
  - { line: 2, text: "`return` devolve o valor e sai. O que vem depois dele não roda." }
  - { line: 3, text: "Sem `return`, a função devolve `undefined`." }
:::

A última nota é a que pega. Uma função que calcula e esquece o `return`
não dá erro:

```javascript
function dobro(valor) {
  valor * 2;
}

console.log(dobro(1890));   // undefined
```

A conta foi feita e jogada fora. Quem chamou recebe `undefined` e segue.

## O frete, na linha 94

O trecho do frete, dentro de `processarEntrega`, era isto — com as
variáveis que ele lia de cima e escrevia para baixo:

```javascript title="entrega.js (trecho, linhas 88–103)"
  var base = 1290;
  if (e.cidade == "Franca") base = 1890;
  if (e.cidade == "São Carlos") base = 2150;
  var extra = 0;
  if (e.peso > 5) extra = Math.round((e.peso - 5) * 90);
  var frete = base + extra;
  if (e.urgente) frete = frete + 1000;
  e.frete = frete;
  ...
```

Tabela por cidade, noventa centavos por quilo acima de cinco, mil
centavos de urgência. Tudo em centavos — o Diego já sabia disso em 2022.

O trecho não precisa de nada que esteja fora dele além de `e`. Ele não
chama a rede, não mexe na tela, não grava log. É o pedaço mais isolado das
cento e oitenta e sete linhas, e por isso é o primeiro.

## Tirar uma responsabilidade

```javascript title="frete.js" numbered
function calcularFrete(cidade, pesoKg, urgente) {
  let base = 1290;
  if (cidade === "Franca") {
    base = 1890;
  }
  if (cidade === "São Carlos") {
    base = 2150;
  }

  let extra = 0;
  if (pesoKg > 5) {
    extra = Math.round((pesoKg - 5) * 90);
  }

  let frete = base + extra;
  if (urgente) {
    frete += 1000;
  }
  return frete;
}

console.log(calcularFrete("Franca", 8, false));
console.log(calcularFrete("São Carlos", 3, true));
console.log(calcularFrete("Ribeirão Preto", 12.5, false));
```

```text
$ node frete.js
2160
3150
1965
```

Franca, 8 kg: 1.890 mais três quilos a 90 centavos, 2.160. São Carlos,
3 kg, urgente: 2.150 mais 1.000, 3.150. Ribeirão, 12,5 kg: 1.290 mais
7,5 quilos, 1.965.

A função recebe **tudo** de que precisa pelos parâmetros, e entrega o
resultado pelo `return`. Não lê variável de fora. Não escreve em `e`.
Chamada duas vezes com os mesmos argumentos, devolve o mesmo número — e é
isso que deixa conferir.

:::term Função pura
Uma função cujo resultado depende só dos argumentos, e que não muda nada
fora dela. `calcularFrete` é pura. `processarEntrega` não é: lê a tela,
chama a rede, grava log.

Função pura se confere com três linhas de `console.log`. A outra, só
subindo o painel.
:::

## Conferir contra o antigo

A regra do Rafael era "um jeito de ver que ela dá o mesmo resultado". A
Bia copiou o trecho antigo para uma função de conferência e comparou as
duas com as entregas da semana, exportadas da produção:

```javascript title="confere.js" numbered
function freteAntigo(e) {
  var base = 1290;
  if (e.cidade == "Franca") base = 1890;
  if (e.cidade == "São Carlos") base = 2150;
  var extra = 0;
  if (e.peso > 5) extra = Math.round((e.peso - 5) * 90);
  var frete = base + extra;
  if (e.urgente) frete = frete + 1000;
  return frete;
}

// semana: as entregas exportadas da produção
let diferentes = 0;
for (const e of semana) {
  const novo = calcularFrete(e.cidade, e.peso, e.urgente);
  if (novo !== freteAntigo(e)) {
    diferentes++;
    console.log(e.codigo, novo, freteAntigo(e));
  }
}
console.log(`${semana.length} entregas, ${diferentes} diferentes`);
```

```text
$ node confere.js
3812 entregas, 0 diferentes
```

Zero. Três mil oitocentas e doze entregas da semana, e a função nova
devolveu, em todas, o mesmo frete que o trecho antigo. É o número que
autoriza a troca — não a leitura do código, nem a opinião de quem
escreveu.

A conferência mostrou uma coisa a mais: 214 dessas entregas tinham o peso
como texto, `"12.50"`, vindo do aplicativo antigo. As duas versões deram o
mesmo resultado porque o `>` e o `-` convertem texto em número — a coerção
do capítulo @cap:variaveis-e-tipos, trabalhando a favor. A Bia anotou no
ticket: o peso precisa ser convertido na entrada, antes de chegar a
qualquer conta.

:::key
Tirar uma responsabilidade de uma função grande tem três passos, nesta
ordem: escrever a função nova com parâmetros e `return`; conferir que ela
dá o mesmo resultado que o trecho antigo, com dados reais; e só então
trocar a chamada. O resto da função grande não é tocado no mesmo dia.
:::

A troca, dentro de `processarEntrega`, foi de oito linhas para uma:

```javascript title="entrega.js (trecho)"
  e.frete = calcularFrete(e.cidade, e.peso, e.urgente);
```

`processarEntrega` passou a ter cento e oitenta linhas. O
comentário continuou na última.

## Valor padrão e argumento que falta

Chamar com menos argumentos não dá erro. O que falta chega como
`undefined`:

```javascript
calcularFrete("Franca", 8);   // urgente é undefined
```

`undefined` é falso, e a conta sai certa por sorte. Para deixar a
intenção escrita, o parâmetro recebe um valor padrão:

```javascript
function calcularFrete(cidade, pesoKg, urgente = false) {
  // ...
}
```

O padrão entra quando o argumento não vem — ou vem `undefined`.

Três parâmetros em fila começam a pedir memória a quem chama:
`calcularFrete("Franca", 8, true)` — o `true` é o quê? Quando a lista
cresce, a função passa a receber um objeto com nomes, e o capítulo
@cap:desestruturacao-e-spread mostra como lê-lo.

## A outra forma: arrow function

```javascript
const calcularTaxa = (valor) => Math.round(valor * 0.03);

console.log(calcularTaxa(2160));   // 65
```

`(valor) => ...` é uma *arrow function*: uma função sem nome próprio,
guardada num `const`. Com uma expressão só depois da seta, o valor dela é
devolvido sem `return`. Com chaves, volta a precisar de `return`.

As duas formas fazem quase o mesmo. O painel novo usa `function` para as
funções com nome que o arquivo oferece, e a seta para funções curtas
passadas a outras — que é onde ela aparece mais, a partir dos próximos
capítulos.

:::summary
- Função tem nome, parâmetros e `return`. Sem `return`, devolve
  `undefined`, sem erro.
- Parâmetro é o nome dentro da função; argumento é o valor na chamada.
  Argumento que falta chega `undefined`; valor padrão escreve a intenção.
- Função pura depende só dos argumentos e não muda nada fora. Confere-se
  com `console.log`.
- Tirar uma responsabilidade: escrever, conferir contra o antigo com dados
  reais, trocar a chamada. Uma por dia.
- `(x) => expressão` devolve a expressão sem `return`.
:::

:::exercise level=1
Diga o que cada chamada devolve, com a `calcularFrete` do capítulo:

```javascript
calcularFrete("Franca", 5, false);
calcularFrete("Franca", 6, false);
calcularFrete("Campinas", 2, true);
```

:::answer
`1890`, `1980` e `2290`.

Com 5 kg não há extra: a condição é `pesoKg > 5`. Com 6, um quilo a 90
centavos. Campinas não está na tabela e cai na base de 1.290 — o que é um
defeito de regra, não de código: a Borba não entrega em Campinas, e a
função deveria recusar.
:::

:::exercise level=2
Escreva `formatarReais(centavos)`, que devolve `"R$ 21,60"` para `2160`.
Use-a para imprimir o frete de Franca, 8 kg.

:::answer
```javascript
function formatarReais(centavos) {
  const texto = (centavos / 100).toFixed(2);
  return `R$ ${texto.replace(".", ",")}`;
}

console.log(formatarReais(calcularFrete("Franca", 8, false)));
```

```text
R$ 21,60
```

A chamada de dentro roda primeiro e entrega o número à de fora. Duas
funções puras encadeadas: cada uma faz uma coisa, e a linha inteira se
confere lendo.
:::

:::exercise level=3
A Cláudia pede que o frete de urgência passe a ser 50% da base, e não mais
mil centavos fixos, "a partir de abril". Diga onde você mudaria, como
conferiria, e o que faria com as entregas de março que ainda vão ser
reprocessadas.

:::answer
Muda em `calcularFrete`, e em nenhum outro lugar — é para isso que ela
existe. A regra nova: `frete += Math.round(base * 0.5)`.

A conferência é a mesma do capítulo, ao contrário: rodar a semana e
**esperar** diferença em toda entrega urgente, e em nenhuma outra. Se uma
entrega não urgente mudar, a mudança escapou.

As entregas de março reprocessadas em abril não podem receber a regra
nova. A função passa a receber a data da entrega, e decide pela data:

```javascript
function calcularFrete(cidade, pesoKg, urgente, data) {
  // ...
  if (urgente) {
    frete += data < "2026-04-01" ? 1000 : Math.round(base * 0.5);
  }
  return frete;
}
```

A data vem como texto no formato `AAAA-MM-DD`, que se compara em ordem
certa como texto. A regra de março continua escrita, com a data em que
deixou de valer.
:::
