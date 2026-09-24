---
title: "Variáveis e tipos"
number: 4
slug: variaveis-e-tipos
part: p2
kicker: "O campo de pendências chegou vazio. O painel comparou vazio com zero, achou igual, e liberou a entrega para sair sem a assinatura."
goal: >-
  Distinguir os tipos que o painel usa todo dia, perguntar o tipo com
  typeof, parar uma conversão automática antes que ela vire regra de
  negócio, e guardar dinheiro em centavos inteiros.
---

:::story Vazio é zero
Terça, 17 de março, 9h10. O Paulo mandou um print para o grupo, sem
texto. Era a entrega E-4907, farmácia, Franca: status "liberada para
rota". Embaixo, a foto do canhoto do motorista, com o campo da assinatura
do farmacêutico em branco.

— Remédio controlado sai com duas assinaturas — escreveu a Cláudia logo
depois. — Essa saiu com nenhuma.

A Bia abriu `entrega.js` e procurou "liberada". Achou:

```javascript
if (e.pendencias == 0) {
  e.status = "liberada para rota";
}
```

O aplicativo do motorista mandava `pendencias` como texto. Quando ninguém
preenchia, mandava texto vazio.

— Vazio não é zero — disse ela.

O Rafael, sem virar a cadeira:

— Para o `==`, é.
:::

## Os tipos do dia a dia

Todo valor em JavaScript tem um tipo. O painel usa cinco o tempo todo, e o
operador `typeof` diz qual é:

```javascript title="tipos.js" numbered
console.log(typeof "E-4907");
console.log(typeof 480);
console.log(typeof true);
console.log(typeof undefined);
console.log(typeof null);
```

```text
$ node tipos.js
string
number
boolean
undefined
object
```

**`string`** é texto. **`number`** é número — e, em JavaScript, é um tipo
só: inteiro e fracionário são o mesmo tipo. **`boolean`** é `true` ou
`false`. **`undefined`** é o valor de um nome que existe e ainda não
recebeu nada. **`null`** é um valor que alguém pôs ali de propósito para
dizer "nada".

A última linha diz `object`, e está errada. `null` não é um objeto. É um
defeito da primeira implementação, de 1995, que ficou no padrão porque
corrigir quebraria páginas que já dependiam dele. Para perguntar se um
valor é `null`, compare direto: `valor === null`.

:::term Tipo
A categoria de um valor: texto, número, booleano, ausência. O tipo mora no
valor, não no nome. Um mesmo `let` pode apontar para um número numa linha
e para um texto na seguinte.

`typeof` pergunta o tipo e devolve o nome dele como texto.
:::

## `undefined` e `null`

Os dois querem dizer ausência, e chegam por caminhos diferentes:

```javascript title="ausencia.js" numbered
let motorista;
console.log(motorista);

const entrega = { codigo: "E-4907", assinatura: null };
console.log(entrega.assinatura);
console.log(entrega.observacao);
```

```text
$ node ausencia.js
undefined
null
undefined
```

`motorista` foi criado sem valor: `undefined`. `assinatura` foi preenchida
com `null` por quem montou a entrega — "não tem, e eu sei que não tem".
`observacao` não existe no objeto, e ler o que não existe devolve
`undefined`, sem erro.

Essa última é a que mais custa. Um nome de campo escrito errado —
`entrega.assinaura` — não quebra. Devolve `undefined`, e o programa segue.

## O `+` que junta e o `-` que converte

Texto e número se misturam o tempo todo no painel, porque metade do que
chega vem de formulário, e formulário manda texto. O JavaScript, quando
recebe tipos diferentes numa conta, converte um deles sozinho:

```javascript title="conversao.js" numbered
console.log("5" + 1);
console.log("5" - 1);
console.log("5" * "2");
console.log("cinco" - 1);
```

```text
$ node conversao.js
51
4
10
NaN
```

O `+` com um texto de um lado **junta**: converte o `1` em `"1"` e cola.
O `-` não tem sentido para texto, então converte o `"5"` em número e
subtrai. O `*` faz o mesmo com os dois lados. E `"cinco" - 1` tenta
converter `"cinco"` em número, não consegue, e produz `NaN`.

:::term NaN
*Not a Number*: o valor numérico que resulta de uma conta sem sentido. O
tipo dele é `number` — o que diz muito sobre o nome.

`NaN` não é igual a nada, nem a ele mesmo: `NaN === NaN` é `false`. Para
perguntar, `Number.isNaN(valor)`.
:::

Essa conversão automática tem nome — **coerção** — e é a origem do
defeito da E-4907.

## `==` converte; `===` não

```javascript title="comparacao.js" numbered
console.log("" == 0);
console.log("0" == 0);
console.log("0" == "");
console.log("" === 0);
console.log("0" === 0);
```

```text
$ node comparacao.js
true
true
false
false
false
```

O `==` compara **depois de converter**. Com um número de um lado, ele
converte o texto em número. `""` vira `0`. `"0"` vira `0`. Os dois ficam
iguais a zero — e não são iguais entre si, porque, entre dois textos, não
há conversão nenhuma. A relação não é nem transitiva.

O `===` compara **sem converter**. Se os tipos são diferentes, a resposta é
`false`, e acabou.

Foi o `if` da E-4907. `pendencias` chegou como `""`. O `==` converteu
`""` em `0`, comparou com `0`, e liberou.

```javascript title="pendencias.js" numbered
const pendencias = "";

if (pendencias == 0) {
  console.log("liberada para rota");
}

if (pendencias === 0) {
  console.log("liberada para rota (===)");
} else {
  console.log("pendências não informadas: segura");
}
```

```text
$ node pendencias.js
liberada para rota
pendências não informadas: segura
```

O `===` sozinho não conserta a regra: com ele, a entrega com `"0"` —
zero pendências, informado como texto — também ficaria segura. O conserto
é converter **na entrada**, com uma decisão sobre o vazio:

```javascript title="pendencias.js" numbered
function lerPendencias(texto) {
  if (texto === "" || texto === null || texto === undefined) {
    return null;
  }
  return Number(texto);
}

const pendencias = lerPendencias("");
console.log(pendencias === 0 ? "liberada" : "segura");
```

```text
segura
```

`function lerPendencias(texto)` dá nome a um trecho que recebe um valor e
devolve outro com `return`. `||` é o "ou". A última linha usa a forma curta
de decisão: condição, `?`, o valor se verdadeira, `:`, o valor se falsa.

`Number("")` também devolveria `0` — a mesma conversão do `==`. Por isso o
vazio é tratado antes, e vira `null`: "não informado". Não é zero.

:::key
O painel usa `===` sempre. E converte o que chega **uma vez, na entrada**,
decidindo o que o vazio significa. Uma conversão que acontece sozinha, no
meio de uma comparação, é uma regra de negócio que ninguém escreveu.
:::

## Dinheiro não mora em `number`

Todo número, em JavaScript, é guardado num único formato binário de ponto
flutuante. Para contar entregas, sobra precisão. Para somar dinheiro, não:

```javascript title="frete.js" numbered
console.log(0.1 + 0.2);
console.log(0.1 + 0.2 === 0.3);
console.log(18.9 + 7.2);
```

```text
$ node frete.js
0.30000000000000004
false
26.099999999999998
```

R$ 18,90 de frete mais R$ 7,20 de taxa de retorno não é, para o
computador, R$ 26,10. A diferença não aparece na tela quando alguém
arredonda — e aparece no fechamento do mês, na soma de quarenta mil
entregas, e numa comparação que dá falso.

O painel novo guarda dinheiro em **centavos, inteiros**:

```javascript title="frete.js" numbered
const frete = 1890;
const retorno = 720;
const total = frete + retorno;

console.log(total);
console.log(total === 2610);
console.log(`R$ ${(total / 100).toFixed(2).replace(".", ",")}`);
```

```text
2610
true
R$ 26,10
```

Enquanto os valores forem inteiros — e centavos são —, as contas são
exatas. A divisão por cem só acontece na hora de mostrar. `toFixed(2)`
escreve o número com duas casas; `replace` troca o ponto pela vírgula.

:::pitfall
Inteiro em `number` é exato até `9007199254740991`
(`Number.MAX_SAFE_INTEGER`). Em centavos, são noventa trilhões de reais.
O faturamento da Borba cabe com folga. Um identificador de banco de dados
com dezenove dígitos, não: ele chega como número, perde os últimos dígitos
calado, e aponta para outra entrega. Identificador longo vem como texto.
:::

:::summary
- `typeof` diz o tipo: `string`, `number`, `boolean`, `undefined`. Para
  `null`, diz `object`, por um defeito de 1995.
- `undefined` é o que ninguém preencheu; `null` é o nada posto de
  propósito. Ler campo inexistente devolve `undefined`, sem erro.
- `+` com texto junta; `-`, `*` e `/` convertem para número. Conta sem
  sentido dá `NaN`.
- `==` converte antes de comparar; `===` não. O painel usa `===` e converte
  na entrada.
- Dinheiro em centavos, inteiros. A vírgula só aparece na tela.
:::

:::exercise level=1
Diga o que cada linha imprime, sem rodar. Depois confira.

```javascript
console.log(typeof "480");
console.log("480" + 20);
console.log("480" - 20);
console.log("480" === 480);
```

:::answer
`string`, `48020`, `460` e `false`.

A segunda junta, porque o `+` tem um texto de um lado. A terceira subtrai,
porque o `-` converte o texto em número. A quarta compara sem converter:
texto e número são tipos diferentes.
:::

:::exercise level=2
Escreva `lerCentavos(texto)`, que recebe o frete como a planilha da Lívia
escreve — `"18,90"` — e devolve `1890`. Texto vazio devolve `null`. Texto
que não for número devolve `null` também.

:::answer
```javascript
function lerCentavos(texto) {
  if (texto === "" || texto === null || texto === undefined) {
    return null;
  }
  const numero = Number(texto.replace(",", "."));
  if (Number.isNaN(numero)) {
    return null;
  }
  return Math.round(numero * 100);
}

console.log(lerCentavos("18,90"));
console.log(lerCentavos(""));
console.log(lerCentavos("doze"));
```

```text
1890
null
null
```

O `Math.round` corrige a sobra do ponto flutuante na multiplicação: `18.9
* 100` dá `1889.9999999999998`. Essa é a única conta com fração que o
frete faz — na entrada —, e o arredondamento a fecha.
:::

:::exercise level=3
No `entrega.js` há esta linha:

```javascript
if (e.tentativas == "0") {
  enviarPrimeiraTentativa(e);
}
```

O aplicativo novo manda `tentativas` como número, e o antigo como texto.
Diga para quais valores a linha dispara, se ela está certa por sorte, e
como você a escreveria.

:::answer
Dispara para `0`, `"0"`, `""` e `" "`. Os dois primeiros estão certos. O
vazio e o espaço convertem para `0` e disparam também — uma entrega sem a
informação é tratada como se nunca tivesse sido tentada, e o motorista vai
de novo.

Ela está certa por sorte nos dois casos que os aplicativos mandam hoje.
Reescrita, a conversão vai para a entrada e a comparação fica estrita:

```javascript
const tentativas = lerInteiro(e.tentativas); // null se vazio
if (tentativas === 0) {
  enviarPrimeiraTentativa(e);
}
```

`lerInteiro` segue o molde do `lerPendencias`: vazio vira `null`, e `null`
não é `0`.
:::
