---
title: "Operadores"
number: 5
slug: operadores
part: p2
kicker: "Frete de 10 mais adicional de 20. A tela da Lívia mostrava R$ 1020."
goal: >-
  Fazer conta sem colar texto sem querer, comparar sem que a ordem
  alfabética decida por você, combinar condições com && e || sabendo o que
  eles devolvem, e ler a precedência no trecho em que ela muda o
  resultado.
---

:::story Mil e vinte
Quarta, 18 de março, 5h52. A Lívia mandou uma foto da tela para a
Cláudia, que encaminhou para o grupo às 8h:

> Frete do Mercado Leste, loja 4: R$ 1020. Era 30.

A Bia abriu o formulário de ajuste de frete. Dois campos: o frete da
tabela e o adicional de rota. A soma estava numa linha de `entrega.js`:

```javascript
const total = form.frete.value + form.adicional.value;
```

— `value` de campo de formulário é sempre texto — disse o Rafael, antes de
ela terminar de ler. — Sempre. Mesmo o campo de número.

— Dez mais vinte, mil e vinte.

— Por isso ninguém reclamava. Quase todo frete tem adicional zero.

— E "10" mais "0"?

— "100". A Lívia achava que era o adicional da serra.
:::

## Aritmética

Os operadores de conta são os de sempre, com dois a mais:

```javascript title="contas.js" numbered
console.log(30 + 12);
console.log(30 - 12);
console.log(30 * 12);
console.log(30 / 12);
console.log(30 % 12);
console.log(2 ** 10);
```

```text
$ node contas.js
42
18
360
2.5
6
1024
```

A divisão devolve fração quando precisa: não existe divisão inteira à
parte, como em outras linguagens. Para cortar a fração, `Math.floor`
(para baixo), `Math.ceil` (para cima) ou `Math.round` (para o mais
próximo).

`%` é o resto da divisão. No painel ele decide, por exemplo, a cor
alternada das linhas da lista: linha par, `i % 2 === 0`. `**` é potência.

## O `+` tem dois empregos

O capítulo @cap:variaveis-e-tipos mostrou que o `+` com um texto de um
lado junta em vez de somar. Com dois textos, também:

```javascript title="frete.js" numbered
const frete = "10";
const adicional = "20";

console.log(frete + adicional);
console.log(Number(frete) + Number(adicional));
console.log(`Total: ${frete + adicional}`);
```

```text
$ node frete.js
1020
30
Total: 1020
```

`Number(...)` converte o texto em número **antes** da conta. É a conversão
na entrada, feita no lugar certo. A terceira linha mostra que a crase não
conserta nada: o que está dentro de `${ }` é calculado primeiro, e o
cálculo já estava errado.

O formulário da Lívia, com a regra dos centavos do capítulo anterior:

```javascript title="frete.js" numbered
function centavos(texto) {
  return Math.round(Number(texto.replace(",", ".")) * 100);
}

const total = centavos("10") + centavos("20");
console.log(total);
console.log(`R$ ${(total / 100).toFixed(2).replace(".", ",")}`);
```

```text
3000
R$ 30,00
```

Três versões, três saídas: `1020`, `30` e `3000` centavos. Só a última
aguenta o frete de R$ 18,90.

:::pitfall
O `+` unário — um `+` na frente de um valor só — também converte:
`+"10"` é `10`. Aparece em código antigo como atalho, `+form.frete.value`.
Funciona, e é fácil de apagar sem perceber numa edição. O painel novo
escreve `Number(...)`.
:::

## Atribuição composta

```javascript
let total = 0;
total += 1890;
total += 720;
total -= 300;
total *= 2;
```

`total += 1890` é `total = total + 1890`. O mesmo vale para `-=`, `*=`,
`/=`. E `+=` herda o duplo emprego do `+`: com texto, junta. Um
acumulador que começa em `""` em vez de `0` monta uma frase de números.

`contador++` soma um e `contador--` subtrai um. Servem em laço. Numa
expressão maior, a posição do `++` muda o valor que a expressão devolve, e
é por isso que o painel novo o deixa sozinho na linha.

## Comparar

```javascript title="comparar.js" numbered
console.log(1890 > 720);
console.log("1890" > "720");
console.log("1890" > 720);
console.log("banana" < "cebola");
```

```text
$ node comparar.js
true
false
true
true
```

A segunda linha é a que engana. Dois **textos** se comparam em ordem
alfabética, caractere por caractere: `"1"` vem antes de `"7"`, e a
comparação para ali. `"1890"` é "menor" que `"720"`, como "abacate" é
menor que "banana".

A terceira converte o texto em número, porque do outro lado há um número,
e dá o resultado esperado. A mesma coerção do `==`, agindo aqui a favor —
por sorte.

:::key
Ordenar ou comparar valores que vieram de formulário, planilha ou URL
exige converter antes. Dois textos com números dentro se comparam como
palavras. A lista de fretes "do maior para o menor" põe R$ 90 acima de
R$ 1.200.
:::

Para igualdade, o capítulo anterior já decidiu: `===` e `!==`, sempre.

## `&&`, `||`, `!` — e o que eles devolvem

```javascript
const temMotorista = true;
const temVeiculo = false;

console.log(temMotorista && temVeiculo);  // false
console.log(temMotorista || temVeiculo);  // true
console.log(!temVeiculo);                 // true
```

`&&` é "e", `||` é "ou", `!` é "não". Até aqui, nada novo. O detalhe é que
`&&` e `||` não devolvem `true` ou `false`: devolvem **um dos dois
valores**.

```javascript title="ou.js" numbered
console.log("" || "sem observação");
console.log(0 || 50);
console.log("E-4907" && "tem código");
console.log(null && "nunca chega aqui");
```

```text
$ node ou.js
sem observação
50
tem código
null
```

`a || b` devolve `a` se `a` for "verdadeiro o bastante"; senão, `b`. E o
JavaScript considera falsos seis valores: `false`, `0`, `""`, `null`,
`undefined` e `NaN`. Todo o resto é verdadeiro.

A segunda linha é o defeito: um desconto de `0` escrito como
`desconto || 50` vira desconto de 50, porque `0` é falso. O zero que
alguém digitou de propósito é trocado pelo padrão.

Para "use o padrão só quando **não houver** valor", existe o `??`:

```javascript
console.log(0 ?? 50);          // 0
console.log("" ?? "padrão");   // ""
console.log(null ?? 50);       // 50
console.log(undefined ?? 50);  // 50
```

`??` só troca `null` e `undefined`. Zero e texto vazio são valores, e
ficam.

:::term Falso numa condição
Os seis valores que uma condição trata como falsos: `false`, `0`, `""`,
`null`, `undefined`, `NaN`. `||` troca qualquer um deles pelo valor da
direita. `??` troca só `null` e `undefined`.
:::

## Precedência

Uma expressão com vários operadores é calculada numa ordem fixa: `*` e `/`
antes de `+` e `-`; comparações depois das contas; `&&` antes de `||`.

```javascript title="precedencia.js" numbered
const frete = 1890;
const adicional = 720;

console.log("Total: " + frete + adicional);
console.log("Total: " + (frete + adicional));
console.log(frete + adicional * 2);
console.log((frete + adicional) * 2);
```

```text
$ node precedencia.js
Total: 1890720
Total: 2610
3330
5220
```

A primeira linha é o `+` da esquerda para a direita: `"Total: " + 1890`
vira texto, e o `+ 720` seguinte junta ao texto. O parêntese força a soma
antes. As duas últimas mostram `*` antes de `+`.

Não é preciso decorar a tabela inteira. A regra do painel novo é mais
curta: **quando a ordem muda o resultado, parêntese**. Custa dois
caracteres e poupa a pessoa que lê de consultar a tabela.

:::summary
- `+ - * / % **`. A divisão devolve fração; `Math.floor`, `ceil` e `round`
  cortam.
- `+` com texto junta. Converta com `Number` antes da conta. Crase não
  corrige conta errada.
- `+=` herda o duplo emprego do `+`. `++` fica sozinho na linha.
- Dois textos se comparam em ordem alfabética. Converta antes de ordenar.
- `&&` e `||` devolvem um dos valores. `||` troca zero e vazio pelo padrão;
  `??` só troca `null` e `undefined`.
- Quando a ordem muda o resultado, parêntese.
:::

:::exercise level=1
Diga o que cada linha imprime:

```javascript
console.log("30" + 12);
console.log("30" - 12);
console.log("30" > "4");
console.log(0 || "nenhum");
console.log(0 ?? "nenhum");
```

:::answer
`3012`, `18`, `false`, `nenhum` e `0`.

A terceira compara textos em ordem alfabética: `"3"` vem antes de `"4"`.
A quarta troca o zero porque `||` o considera falso. A quinta mantém o
zero: `??` só troca `null` e `undefined`.
:::

:::exercise level=2
O painel antigo mostrava o desconto do cliente assim:

```javascript
const desconto = cliente.desconto || 10;
```

A Mercado Leste negociou desconto zero. Diga o que o painel mostra para
ela e reescreva a linha.

:::answer
Mostra 10. O desconto zero é falso para o `||`, e o padrão entra no lugar
do valor negociado.

```javascript
const desconto = cliente.desconto ?? 10;
```

Com `??`, o padrão só entra quando o campo não existe ou é `null`. O zero
da Mercado Leste fica.
:::

:::exercise level=3
A Cláudia pede a lista de fretes do dia do maior para o menor. Os valores
chegam da planilha como texto: `["90", "1200", "350"]`. Escreva a
comparação que decide se um frete vem antes do outro, e mostre por que a
versão com os textos direto erra.

:::answer
```javascript
const a = "90";
const b = "1200";

console.log(a > b);                   // true
console.log(Number(a) > Number(b));   // false
```

Comparados como texto, `"90"` é maior que `"1200"`: o `"9"` vem depois do
`"1"`, e a comparação para no primeiro caractere. A lista "do maior para o
menor" começaria pelo frete de R$ 90.

Convertidos, `90 > 1200` é falso, como deve ser. A conversão entra uma vez,
quando a planilha é lida, e a ordenação trabalha com números.
:::
