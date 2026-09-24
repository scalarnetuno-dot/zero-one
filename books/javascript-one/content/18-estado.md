---
title: "Estado"
number: 18
slug: estado
part: p5
kicker: "A lista dizia cancelada. O painel de detalhe, ao lado, dizia a caminho. Cada pedaço da tela tinha guardado a sua cópia da entrega."
goal: >-
  Ter um lugar só de onde a tela lê a lista, mudar o dado ali e redesenhar
  a partir dele, e ver a diferença entre a tela que atualiza as duas
  regiões e a que atualiza uma.
---

:::story Duas verdades lado a lado
Sexta, 10 de abril, 5h47. A Lívia mandou uma foto do tablet para a
Cláudia. À esquerda, a lista: E-5512, **cancelada**, riscada — o 1847
consertado. À direita, o painel de detalhe da mesma entrega, aberto desde
as 5h40: **a caminho**, motorista Ademir, previsão 7h10.

— Qual das duas eu passo para a loja? — escreveu a Lívia.

A Bia abriu o `lista.js` às 9h. O detalhe era montado assim:

```javascript
function abrirDetalhe(codigo) {
  const e = { ...buscarNaLista(codigo) };
  painelDetalhe.entrega = e;
  desenharDetalhe(e);
}
```

— Ela copiou a entrega — disse a Bia. — Para não alterar a lista. Como eu
fiz no capítulo do endereço.

— E quando a lista muda? — perguntou o Rafael.

— A lista muda a lista.

— E o detalhe fica com a cópia das 5h40.
:::

## Onde o dado mora

O painel da Borba mostra a mesma entrega em três lugares: a linha da
lista, o detalhe ao lado, e o total do rodapé. Em 2022, cada um desses
lugares guardava o seu dado:

- a lista guardava o array que veio do servidor;
- o detalhe guardava uma cópia da entrega aberta;
- o rodapé guardava um número, somado quando a lista carregava.

Enquanto nada muda, as três cópias concordam. Quando uma entrega é
cancelada, a lista é atualizada — e as outras duas não sabem.

:::term Estado
O dado que a tela mostra num dado momento: a lista de entregas, qual está
aberta no detalhe, qual filtro está ligado. Tudo que, se mudasse, faria a
tela mudar.

Estado duplicado é estado que vai divergir. A pergunta é quando.
:::

A cópia do detalhe foi feita pelo motivo certo — o capítulo
@cap:desestruturacao-e-spread mostrou o que acontece quando a tela altera
o objeto da lista. Mas ela trocou um defeito por outro: o detalhe deixou
de alterar a lista, e passou a não enxergar mais as mudanças dela.

## A reprodução

Sem navegador, com as regiões da tela desenhadas como texto:

```javascript title="duas-copias.js" numbered
const lista = [
  { codigo: "E-5512", status: "a caminho", frete: 1890 },
  { codigo: "E-5513", status: "a caminho", frete: 2160 },
];

const detalhe = { ...lista[0] };
let totalRodape = lista.reduce((s, e) => s + e.frete, 0);

function desenhar() {
  const linhas = lista.map((e) => `${e.codigo} ${e.status}`);
  console.log(`lista:   ${linhas.join(" | ")}`);
  console.log(`detalhe: ${detalhe.codigo} ${detalhe.status}`);
  console.log(`rodapé:  ${totalRodape}`);
}

lista[0].status = "cancelada";
desenhar();
```

```text
$ node duas-copias.js
lista:   E-5512 cancelada | E-5513 a caminho
detalhe: E-5512 a caminho
rodapé:  4050
```

Três regiões, três respostas. A lista sabe do cancelamento. O detalhe não.
O rodapé soma o frete de uma entrega cancelada, que a Borba não cobra.

Não há erro em nenhuma linha. Cada região mostra corretamente o dado que
guardou. O defeito é haver três dados.

## Um lugar só

O painel novo guarda **um** estado, e cada região da tela é **desenhada a
partir dele**, sem guardar nada:

```javascript title="estado.js" numbered
const estado = {
  entregas: [
    { codigo: "E-5512", status: "a caminho", frete: 1890 },
    { codigo: "E-5513", status: "a caminho", frete: 2160 },
  ],
  aberta: "E-5512",
};

function desenharLista(s) {
  return s.entregas.map((e) => `${e.codigo} ${e.status}`).join(" | ");
}

function desenharDetalhe(s) {
  const e = s.entregas.find((x) => x.codigo === s.aberta);
  return e ? `${e.codigo} ${e.status}` : "nenhuma aberta";
}

function desenharRodape(s) {
  return s.entregas
    .filter((e) => e.status !== "cancelada")
    .reduce((soma, e) => soma + e.frete, 0);
}

function desenhar() {
  console.log(`lista:   ${desenharLista(estado)}`);
  console.log(`detalhe: ${desenharDetalhe(estado)}`);
  console.log(`rodapé:  ${desenharRodape(estado)}`);
}
```

Três mudanças de desenho.

**O detalhe guarda o código, não a entrega.** `estado.aberta` diz **qual**
entrega está aberta. O dado dela é lido da lista toda vez que o detalhe é
desenhado.

**O rodapé não guarda o total.** Ele o **calcula** a partir da lista, na
hora de desenhar. Um total guardado precisa ser atualizado por alguém; um
total calculado não pode ficar velho.

**As funções de desenho recebem o estado e devolvem o que mostrar.** Não
leem variável solta, não escrevem em nada. São funções puras, do capítulo
@cap:funcoes — e por isso dá para conferi-las com `console.log`.

## Mudar e redesenhar

Toda mudança passa por uma função que altera o estado e manda redesenhar:

```javascript title="estado.js" numbered
function cancelar(codigo) {
  estado.entregas = estado.entregas.map((e) =>
    e.codigo === codigo ? { ...e, status: "cancelada" } : e,
  );
  desenhar();
}

cancelar("E-5512");
```

```text
$ node estado.js
lista:   E-5512 cancelada | E-5513 a caminho
detalhe: E-5512 cancelada
rodapé:  2160
```

As três regiões concordam, porque não há três dados para concordar. Há um.

`cancelar` cria uma lista nova, com a entrega cancelada copiada e as
outras iguais — o spread do capítulo @cap:desestruturacao-e-spread, usado
para mudar sem alterar o objeto que alguém ainda possa estar segurando. E
chama `desenhar`, que refaz tudo a partir do estado novo.

:::key
A tela é desenhada a partir do estado; ela não guarda estado. Toda
mudança passa por uma função que altera o estado e manda redesenhar.
Região da tela que guarda a sua própria cópia do dado vai mostrar, um dia,
uma coisa diferente da região ao lado.
:::

## No navegador

No `painel.js`, as funções de desenho escrevem no DOM em vez de devolver
texto, e o resto é igual:

```javascript title="painel.js" numbered
function desenhar() {
  desenharListaNoDom(estado);
  document.querySelector("#detalhe").textContent =
    desenharDetalhe(estado);
  document.querySelector("#rodape").textContent =
    formatarReais(desenharRodape(estado));
}
```

A atualização de trinta segundos passa a ser: buscar a lista no servidor,
pôr em `estado.entregas`, chamar `desenhar`. O detalhe aberto das 5h40
mostra o status das 5h47, porque lê o mesmo lugar que a lista.

:::pitfall
Redesenhar tudo a cada mudança é o jeito mais simples de a tela nunca
divergir do estado, e tem um custo: com cento e sessenta entregas, cada
redesenho recria cento e sessenta linhas. Para a lista da Borba, a conta
ainda cabe. Quando deixar de caber, a resposta não é voltar a guardar
cópias — é medir onde o tempo vai, antes de mudar qualquer coisa.
:::

:::milestone
Fim da Parte 5. A tela do painel novo lê de um lugar só: a lista, o
detalhe e o rodapé concordam depois de um cancelamento. Cada botão tem um
ouvinte. E a entrega cancelada aparece riscada no tablet do cais, com a
janela de qualquer largura.
:::

:::summary
- Estado é o dado que a tela mostra. Estado duplicado diverge.
- Copiar para não alterar resolve um defeito e cria outro: a cópia não vê
  as mudanças.
- Guarde o código da entrega aberta, não a entrega. Calcule o total, não o
  guarde.
- Funções de desenho recebem o estado e devolvem o que mostrar, sem
  guardar nada.
- Toda mudança altera o estado e manda redesenhar.
:::

:::exercise level=1
No `duas-copias.js`, diga o que o rodapé mostra depois de
`lista.push({ codigo: "E-5514", status: "a caminho", frete: 1550 })`
seguido de `desenhar()`, e por quê.

:::answer
Continua `4050`. `totalRodape` foi calculado uma vez, na linha em que foi
criado, e é um número guardado. A entrega nova entrou na lista e não
entrou no número.

Na versão com estado, o rodapé é calculado no `desenhar`, e mostraria a
soma com a E-5514.
:::

:::exercise level=2
Escreva `ajustarFrete(codigo, novoFrete)` no molde de `cancelar`, e mostre
o rodapé antes e depois de ajustar o frete da E-5513 para 2340.

:::answer
```javascript
function ajustarFrete(codigo, novoFrete) {
  estado.entregas = estado.entregas.map((e) =>
    e.codigo === codigo ? { ...e, frete: novoFrete } : e,
  );
  desenhar();
}

console.log(desenharRodape(estado));
ajustarFrete("E-5513", 2340);
```

```text
2160
lista:   E-5512 cancelada | E-5513 a caminho
detalhe: E-5512 cancelada
rodapé:  2340
```

O primeiro número é o rodapé depois do cancelamento: só a E-5513 conta. O
ajuste muda o estado e o redesenho recalcula.
:::

:::exercise level=3
O Marcos propõe um "sistema de eventos": cada região se inscreve para
ouvir "entrega mudou" e atualiza a própria cópia quando o evento chega.
Compare com a solução do capítulo, e diga quando a proposta dele passa a
valer a pena.

:::answer
A proposta mantém as cópias e acrescenta um jeito de avisá-las. Funciona
enquanto todo código que muda uma entrega lembrar de disparar o evento, e
toda região que guarda cópia lembrar de ouvir. Uma mudança que esquecer o
evento é o detalhe das 5h47 de novo — agora com mais código em volta.

A solução do capítulo não precisa de aviso: não há cópia para avisar. O
custo dela é redesenhar tudo a cada mudança.

A proposta passa a valer quando redesenhar tudo ficar caro de verdade —
medido, com número — e quando as regiões forem muitas e independentes o
bastante para não caberem num `desenhar` só. Com três regiões e cento e
sessenta entregas, é uma arquitetura para um problema que a Borba ainda
não tem.
:::
