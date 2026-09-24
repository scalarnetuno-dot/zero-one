---
title: "Desestruturação e spread"
number: 11
slug: desestruturacao-e-spread
part: p3
kicker: "A tela de edição mudou o endereço só para mostrar. A lista da manhã, que guardava o mesmo objeto, mudou junto."
goal: >-
  Ler um objeto por desestruturação, receber parâmetros com nome, copiar
  com spread sem achar que copiou o que está aninhado, e reproduzir a
  mutação compartilhada que mudou a lista sem ninguém mandar.
---

:::story Só nesta tela
Quinta, 26 de março, 5h38. A Lívia imprimiu a lista e conferiu com a tela.
A E-5188, do mercado da Vila Tibério, estava na lista impressa com o
endereço "R. Tibiriçá, 440". Na tela, "R. TIBIRIÇÁ, 440 — FUNDOS".

Às 9h, o Paulo reproduziu: bastava abrir o detalhe da entrega e fechar
sem salvar. A linha da lista mudava.

A Bia achou o trecho da tela de detalhe:

```javascript
function abrirDetalhe(entrega) {
  const d = entrega;
  d.endereco = d.endereco.toUpperCase() + " — FUNDOS";
  mostrar(d);
}
```

— Ele só queria mostrar em maiúsculas — disse ela. — Com o complemento.
Não salvou nada.

— Não precisou salvar — disse o Rafael. — O `d` é a entrega.

— É uma cópia.

— É um segundo nome.
:::

## Um objeto, dois nomes

Um objeto não é copiado quando é atribuído a outro nome. O nome novo passa
a apontar para o **mesmo** objeto:

```javascript title="mesmo.js" numbered
const lista = [{ codigo: "E-5188", endereco: "R. Tibiriçá, 440" }];

const d = lista[0];
d.endereco = "R. TIBIRIÇÁ, 440 — FUNDOS";

console.log(lista[0].endereco);
console.log(d === lista[0]);
```

```text
$ node mesmo.js
R. TIBIRIÇÁ, 440 — FUNDOS
true
```

Não existem dois objetos. Existe um, com dois nomes: `lista[0]` e `d`. O
`===` entre objetos compara **se são o mesmo**, não se têm o mesmo
conteúdo — e responde `true`.

Com texto e número isso não acontece: `let a = "x"; let b = a; b = "y";`
não muda `a`. Texto e número não se alteram; só se trocam. Objetos e
arrays se alteram no lugar, e todo nome que aponta para eles vê a
alteração.

:::term Referência
O que um nome guarda quando aponta para um objeto ou array: o caminho até
ele, não uma cópia. Passar um objeto para uma função, pôr num array ou
atribuir a outro nome cria mais uma referência ao mesmo objeto.

Alterar pelo segundo nome é alterar para todos.
:::

A função `abrirDetalhe` recebeu uma referência. O `const d = entrega` criou
outra. E `d.endereco = ...` alterou o único objeto, que era também o que a
lista mostrava.

## Spread: uma cópia de verdade

Os três pontos antes de um objeto, dentro de chaves, espalham as
propriedades dele num objeto **novo**:

```javascript title="copia.js" numbered
const lista = [{ codigo: "E-5188", endereco: "R. Tibiriçá, 440" }];

const d = { ...lista[0] };
d.endereco = "R. TIBIRIÇÁ, 440 — FUNDOS";

console.log(lista[0].endereco);
console.log(d.endereco);
console.log(d === lista[0]);
```

```text
$ node copia.js
R. Tibiriçá, 440
R. TIBIRIÇÁ, 440 — FUNDOS
false
```

`{ ...lista[0] }` criou um objeto novo com as mesmas propriedades. Mudar o
novo não toca o original.

O spread também acrescenta ou substitui na mesma linha — a forma que o
painel novo usa para "a mesma entrega, com uma coisa diferente":

```javascript
const paraTela = {
  ...entrega,
  endereco: entrega.endereco.toUpperCase(),
};
```

As propriedades de `entrega` entram primeiro; o `endereco` escrito depois
substitui o que veio. O original fica como estava.

Para arrays, o mesmo operador, com colchetes:

```javascript
const manhaComNova = [...manha, novaEntrega];
```

## A cópia é rasa

O spread copia **um nível**. Se uma propriedade é outro objeto, a cópia
recebe a referência a ele — o mesmo objeto de dentro:

```javascript title="raso.js" numbered
const original = {
  codigo: "E-5188",
  destino: { rua: "R. Tibiriçá", numero: 440 },
};

const copia = { ...original };
copia.codigo = "E-5188-B";
copia.destino.numero = 442;

console.log(original.codigo);
console.log(original.destino.numero);
```

```text
$ node raso.js
E-5188
442
```

O `codigo` foi copiado: mudar na cópia não mudou o original. O `destino`
não foi: `copia.destino` e `original.destino` são o mesmo objeto, e o 442
apareceu nos dois.

:::pitfall
Spread copia o primeiro nível e compartilha o resto. Uma entrega com
`destino`, `itens` ou `motorista` aninhados, copiada com `{ ...e }`, ainda
divide esses objetos com o original.

Para mudar um aninhado sem tocar no original, a cópia desce até ele:

```javascript
const copia = {
  ...original,
  destino: { ...original.destino, numero: 442 },
};
```

Para uma cópia completa, de todos os níveis, existe `structuredClone(e)`.
Ela custa mais, e é raro precisar: quase sempre, o que se quer é mudar
**uma** coisa, e a cópia que desce só por ela é a mais clara.
:::

## Desestruturação

A operação inversa do objeto literal: tirar propriedades de um objeto e
pôr cada uma num nome.

```javascript
const entrega = {
  codigo: "E-5188",
  status: "a caminho",
  cidade: "Ribeirão Preto",
};

const { codigo, status } = entrega;
console.log(codigo, status);   // E-5188 a caminho
```

`const { codigo, status } = entrega` cria dois nomes com os valores das
propriedades de mesmo nome. Propriedade que não existe dá `undefined`, ou o
padrão, se houver:

```javascript
const { urgente = false, cidade: municipio } = entrega;
```

`urgente = false` dá o padrão. `cidade: municipio` lê `cidade` e guarda no
nome `municipio`.

E em arrays, pela posição:

```javascript
const [primeira, segunda] = manha;
```

## Parâmetros com nome

O capítulo @cap:funcoes deixou `calcularFrete(cidade, pesoKg, urgente)`
com três argumentos em fila, e a pergunta "o `true` é o quê?". A
desestruturação no parâmetro responde:

```javascript title="frete.js" numbered
function calcularFrete({ cidade, pesoKg, urgente = false }) {
  let base = 1290;
  if (cidade === "Franca") base = 1890;
  if (cidade === "São Carlos") base = 2150;

  const extra = pesoKg > 5 ? Math.round((pesoKg - 5) * 90) : 0;
  return base + extra + (urgente ? 1000 : 0);
}

console.log(calcularFrete({ cidade: "Franca", pesoKg: 8 }));
console.log(
  calcularFrete({ pesoKg: 3, urgente: true, cidade: "Franca" }),
);
```

```text
$ node frete.js
2160
2890
```

A função recebe **um objeto** e o desestrutura na própria assinatura.
Quem chama escreve os nomes, em qualquer ordem, e omite os que têm padrão.
E dá para chamar com a própria entrega:
`calcularFrete(entrega)` — as propriedades a mais são ignoradas.

## O detalhe da E-5188

A tela de detalhe, reescrita:

```javascript
function abrirDetalhe(entrega) {
  const paraTela = {
    ...entrega,
    endereco: `${entrega.endereco.toUpperCase()} — FUNDOS`,
  };
  mostrar(paraTela);
}
```

A entrega da lista não é tocada. A tela mostra uma versão dela, criada só
para mostrar.

:::key
Função que recebe um objeto e não deveria alterá-lo trabalha numa cópia —
`{ ...e, campo: novo }`. Alterar o parâmetro direto altera o objeto de
quem chamou, e de todo mundo que tem uma referência a ele.
:::

:::milestone
Fim da Parte 3. Na pasta `borba` há funções pequenas e conferidas: o frete
tirado de `processarEntrega`, a situação decidida num lugar só, os dois
formatos de entrega convertidos na porta, e a tela que mostra uma cópia em
vez de alterar a lista. `processarEntrega` continua no ar, com cento e
oitenta linhas e o comentário na última.
:::

:::summary
- Atribuir um objeto a outro nome não copia: cria outra referência ao mesmo
  objeto. `===` entre objetos pergunta se são o mesmo.
- `{ ...e }` cria um objeto novo com as propriedades de `e`;
  `{ ...e, campo: novo }` copia e substitui.
- A cópia do spread é rasa: objetos aninhados continuam compartilhados.
  Desça a cópia até o que vai mudar.
- `const { a, b = padrão, c: nome } = objeto` desestrutura; `[x, y]` em
  arrays, pela posição.
- Parâmetro desestruturado dá nome aos argumentos e aceita a ordem que
  quem chama quiser.
:::

:::exercise level=1
Diga o que cada linha imprime:

```javascript
const a = { status: "a caminho" };
const b = a;
const c = { ...a };
b.status = "entregue";
console.log(a.status, b.status, c.status);
console.log(a === b, a === c);
```

:::answer
`entregue entregue a caminho` e `true false`.

`b` é outro nome para o objeto de `a`; mudar por `b` mudou para os dois.
`c` é um objeto novo, copiado antes da mudança.
:::

:::exercise level=2
Escreva `cancelar(entrega, motivo)` que devolve uma entrega nova, com
`status: "cancelada"` e o `motivo`, sem alterar a que recebeu. Mostre que
a original continua igual.

:::answer
```javascript
function cancelar(entrega, motivo) {
  return { ...entrega, status: "cancelada", motivo };
}

const e = { codigo: "E-5188", status: "a caminho" };
const c = cancelar(e, "loja fechada");

console.log(e.status);
console.log(c.status, c.motivo);
```

```text
a caminho
cancelada loja fechada
```

`motivo` sozinho, sem `: valor`, é a forma curta de `motivo: motivo`: a
propriedade recebe o nome e o valor do nome de mesmo nome.
:::

:::exercise level=3
A entrega tem `itens: [{ produto: "pão", quantidade: 40 }]`. A tela de
ajuste deixa a Lívia mudar a quantidade antes de confirmar. O código é:

```javascript
const rascunho = { ...entrega };
rascunho.itens[0].quantidade = 35;
```

Diga o que acontece se a Lívia desistir do ajuste, e corrija.

:::answer
A lista já mudou. `{ ...entrega }` copiou o primeiro nível; `itens` é o
mesmo array, e o item dentro dele é o mesmo objeto. Desistir do ajuste não
desfaz nada: a entrega da lista já está com 35.

A cópia precisa descer até o item:

```javascript
const rascunho = {
  ...entrega,
  itens: entrega.itens.map((item) => ({ ...item })),
};
rascunho.itens[0].quantidade = 35;
```

O `map` cria um array novo, e cada item é copiado com spread. Os
parênteses em volta de `{ ...item }` dizem à seta que as chaves são um
objeto a devolver, e não o corpo da função.

Com `structuredClone(entrega)` o resultado seria o mesmo, copiando todos
os níveis de uma vez.
:::
