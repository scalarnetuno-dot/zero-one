---
title: "Módulos"
number: 19
slug: modulos
part: p6
kicker: "entrega.js passou a importar lista.js, que já importava entrega.js. O painel parou de carregar com uma mensagem sobre acessar um nome antes de ele existir."
goal: >-
  Separar o painel em arquivos com export e import, entender em que ordem
  o Node carrega módulos que se importam, reproduzir a dependência
  circular, e desfazê-la com um terceiro arquivo que guarda o dado.
---

:::story Antes de existir
Segunda, 13 de abril, 16h10. A Bia estava separando a pasta `borba` em
arquivos. O `painel.js` tinha passado de quatrocentas linhas, e o Rafael
tinha pedido na sexta: "um arquivo por assunto".

Ela criou `entrega.js`, com as regras de situação e o cancelamento, e
`lista.js`, com o desenho da lista. O cancelamento precisava redesenhar a
linha — importou de `lista.js`. A lista precisava da ordem das situações
para ordenar — importou de `entrega.js`.

Rodou.

```text
ReferenceError: Cannot access 'SITUACOES' before initialization
```

— Mas `SITUACOES` está ali — disse ela. — Linha três, exportado.

O Rafael leu o erro, depois os dois `import`.

— Está. Só que ninguém chegou na linha três ainda.
:::

## Um arquivo, um módulo

Até aqui, cada exemplo era um arquivo que rodava sozinho. O painel novo
tem regras de entrega, desenho de tela, frete e comunicação com o
servidor. Num arquivo só, é o `entrega.js` de 2022 de novo.

Um **módulo** é um arquivo que declara o que oferece aos outros com
`export` e o que usa dos outros com `import`:

```javascript title="frete.js" numbered
export function calcularFrete({ cidade, pesoKg, urgente = false }) {
  let base = 1290;
  if (cidade === "Franca") base = 1890;
  if (cidade === "São Carlos") base = 2150;
  const extra = pesoKg > 5 ? Math.round((pesoKg - 5) * 90) : 0;
  return base + extra + (urgente ? 1000 : 0);
}

export function formatarReais(centavos) {
  const texto = (centavos / 100).toFixed(2);
  return `R$ ${texto.replace(".", ",")}`;
}
```

```javascript title="painel.js" numbered
import { calcularFrete, formatarReais } from "./frete.js";

const f = calcularFrete({ cidade: "Franca", pesoKg: 8 });
console.log(formatarReais(f));
```

Para o Node tratar os arquivos da pasta como módulos, o `package.json`
diz isso numa linha:

```json title="package.json"
{
  "name": "borba",
  "type": "module"
}
```

```text
$ node painel.js
R$ 21,60
```

`export` antes de `function` torna a função disponível para quem
importar. O que não tem `export` fica privado ao arquivo — uma função
auxiliar de `frete.js` que ninguém de fora precisa ver.

`import { ... } from "./frete.js"` traz os nomes pedidos. O `./` diz que o
arquivo está na mesma pasta, e a extensão `.js` é obrigatória.

:::term Módulo
Um arquivo com escopo próprio. Os nomes criados nele não vazam para os
outros — o problema do `var` global do capítulo @cap:escopo desaparece.
Só passa de um arquivo para outro o que foi exportado de um lado e
importado do outro.

Todo módulo roda em modo estrito, sem precisar de `"use strict"`.
:::

## O formato de 2022

O painel de produção não usa `import`. Os arquivos são carregados um atrás
do outro por `<script>` no `index.html`, e se enxergam por nomes globais.
No servidor, o Node 20 roda com o formato antigo dele:

```javascript
const axios = require("axios");
module.exports = { processarEntrega };
```

`require` e `module.exports` são o formato CommonJS, que o Node usa desde
2009. `import` e `export` são o formato do próprio padrão da linguagem,
chamado ESM, que o Node aceita desde a linha 12. Os dois convivem; um
arquivo usa um ou outro. A pasta `borba` usa ESM, e o `"type": "module"`
é o que diz isso ao Node.

## A ordem em que os módulos rodam

Quando o `painel.js` importa `frete.js`, o Node:

1. lê `painel.js` e acha os `import`;
2. carrega `frete.js` e **executa** o arquivo inteiro, de cima para baixo;
3. só então executa `painel.js`.

Cada módulo roda uma vez só, na primeira vez em que alguém o importa. Os
outros que o importarem recebem o mesmo, já executado.

A regra é simples até dois módulos se importarem mutuamente.

## A dependência circular

Os dois arquivos da Bia:

```javascript title="entrega.js" numbered
import { desenharLinha } from "./lista.js";

export const SITUACOES = ["a caminho", "entregue", "cancelada"];

export function cancelar(e) {
  return desenharLinha({ ...e, status: "cancelada" });
}
```

```javascript title="lista.js" numbered
import { SITUACOES } from "./entrega.js";

const ORDEM = SITUACOES.map((s, i) => [s, i]);

export function desenharLinha(e) {
  return `${e.codigo} ${e.status}`;
}
```

```javascript title="painel.js" numbered
import { cancelar } from "./entrega.js";

console.log(cancelar({ codigo: "E-5601", status: "a caminho" }));
```

```text
$ node painel.js
file:///D:/borba/lista.js:3
const ORDEM = SITUACOES.map((s, i) => [s, i]);
              ^

ReferenceError: Cannot access 'SITUACOES' before initialization
```

A ordem do que aconteceu:

1. `painel.js` importa `entrega.js`. O Node começa a carregar `entrega.js`.
2. `entrega.js` importa `lista.js`. Antes de executar `entrega.js`, o Node
   carrega `lista.js`.
3. `lista.js` importa `entrega.js` — que **já está sendo carregado**. O
   Node não começa de novo: entrega a `lista.js` o que `entrega.js` tem
   até agora. E até agora `entrega.js` não executou nenhuma linha.
4. `lista.js` executa, e a linha 3 lê `SITUACOES` — um nome que existe no
   módulo, mas cuja linha de criação ainda não rodou.

É o `let` lido antes de nascer, do capítulo @cap:escopo, entre dois
arquivos. O nome está lá. A linha que o preenche vem depois.

:::key
Dois módulos que se importam mutuamente formam um ciclo, e um deles roda
primeiro **sem o outro estar pronto**. Se o que roda primeiro usar algo do
outro já no carregamento — numa linha solta, fora de função —, esse algo
ainda não existe.
:::

A versão sem a linha do `ORDEM` roda — `desenharLinha` só é chamada
depois, quando os dois já carregaram. Por isso ciclos ficam escondidos:
funcionam até alguém acrescentar, num dos arquivos, uma linha que usa o
outro no carregamento.

## O terceiro arquivo

O ciclo se desfaz perguntando **o que** cada arquivo precisa do outro. A
lista precisa das situações. O cancelamento precisa do desenho. As
situações não são nem do cancelamento nem da lista: são o **dado** que os
dois usam.

```javascript title="situacoes.js" numbered
export const SITUACOES = ["a caminho", "entregue", "cancelada"];
```

```javascript title="lista.js" numbered
import { SITUACOES } from "./situacoes.js";

const ORDEM = SITUACOES.map((s, i) => [s, i]);

export function desenharLinha(e) {
  return `${e.codigo} ${e.status}`;
}
```

```javascript title="entrega.js" numbered
import { SITUACOES } from "./situacoes.js";
import { desenharLinha } from "./lista.js";

export function cancelar(e) {
  if (!SITUACOES.includes(e.status)) {
    throw new Error(`${e.codigo}: situação ${e.status}`);
  }
  return desenharLinha({ ...e, status: "cancelada" });
}
```

```text
$ node painel.js
E-5601 cancelada
```

`situacoes.js` não importa nada. `lista.js` importa só ele.
`entrega.js` importa os dois. As setas vão todas numa direção:

:::diagram type="flowchart" caption="Depois da divisão: as dependências vão numa direção só, e o dado fica num arquivo que não depende de ninguém."
nodes:
  - { id: p, type: process, text: "painel.js" }
  - { id: e, type: process, text: "entrega.js" }
  - { id: l, type: process, text: "lista.js" }
  - { id: s, type: io, text: "situacoes.js" }
edges:
  - { from: p, to: e }
  - { from: e, to: l }
  - { from: e, to: s }
  - { from: l, to: s }
:::

:::pitfall
A tentação, diante do erro, é mover a linha do `ORDEM` para dentro de uma
função, onde ela só roda depois. O erro some, e o ciclo continua. A
próxima pessoa a acrescentar uma linha solta num dos dois arquivos
encontra o mesmo erro, sem a história. Ciclo se desfaz; não se contorna.
:::

## Exportação padrão

Um módulo pode ter uma exportação sem nome:

```javascript
export default function desenhar(estado) { /* ... */ }
```

```javascript
import desenhar from "./desenho.js";
```

Quem importa escolhe o nome. É conveniente, e é por isso que o painel
novo não usa: o mesmo módulo importado como `desenhar` num arquivo e
`render` noutro não se acha por busca. Exportação com nome obriga todo
mundo a chamar a coisa pelo mesmo nome.

:::summary
- Módulo é um arquivo com escopo próprio. `export` oferece; `import`
  traz. O caminho relativo leva `./` e a extensão.
- `"type": "module"` no `package.json` põe o Node em ESM. O painel de 2022
  usa `<script>` global no navegador e `require` no servidor.
- Cada módulo executa uma vez, inteiro, na primeira importação.
- Num ciclo, um módulo roda sem o outro pronto. Usar o outro numa linha
  solta dá `Cannot access ... before initialization`.
- O ciclo se desfaz tirando o dado comum para um terceiro arquivo, que não
  depende de ninguém.
:::

:::exercise level=1
Diga o que acontece em cada caso:

1. `import { calcularfrete } from "./frete.js";`
2. `import { calcularFrete } from "./frete";`
3. Uma função sem `export` em `frete.js`, importada pelo nome no painel.

:::answer
1. `SyntaxError`: o módulo não exporta `calcularfrete`, com `f` minúsculo.
   A mensagem diz o nome que não foi encontrado. Os nomes diferenciam
   maiúscula de minúscula.
2. Erro de módulo não encontrado: em ESM no Node, a extensão é
   obrigatória.
3. O mesmo `SyntaxError` do item 1. O que não é exportado não existe para
   fora do arquivo.
:::

:::exercise level=2
A Bia quer que `lista.js` mostre o frete formatado. Diga de qual arquivo
ela importa, e se isso cria algum ciclo com os arquivos do capítulo.

:::answer
De `frete.js`:

```javascript
import { formatarReais } from "./frete.js";
```

Não cria ciclo. `frete.js` não importa nada — ele é, como
`situacoes.js`, um arquivo de regras que só dá. As setas continuam numa
direção: `lista.js` depende de `frete.js`, e nada em `frete.js` depende da
lista.

O teste rápido de ciclo: seguir os `import` a partir de um arquivo e ver
se se volta a ele.
:::

:::exercise level=3
O Marcos propõe uma pasta `utils/` com um `index.js` que reexporta tudo —
frete, situações, desenho, cancelamento —, "para cada arquivo importar de
um lugar só". Diga o que isso faz com os ciclos, e o que você proporia.

:::answer
Um `index.js` que reexporta tudo depende de todos os arquivos. Se
`lista.js` importar de `utils/index.js`, passa a depender, indiretamente,
de `entrega.js` — que depende de `lista.js`. O ciclo desfeito volta, agora
atravessando um arquivo que ninguém lê, e o erro aparece com o nome de um
módulo que parece não ter nada a ver.

A proposta que eu faria: cada arquivo importa do arquivo que tem o que ele
precisa, pelo nome. São duas ou três linhas de `import` a mais, e cada
uma diz a verdade sobre de quem aquele arquivo depende. A comodidade de
um lugar só custa enxergar as dependências — que é o que evita o ciclo.
:::
