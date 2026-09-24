---
title: "Closures"
number: 15
slug: closures
part: p4
kicker: "Cada botão de cancelar da lista cancelava a última entrega. Quem lia o código não via o número errado escrito em lugar nenhum."
goal: >-
  Dizer qual variável uma função criada dentro de outra enxerga, usar isso
  de propósito para guardar estado, e reproduzir o laço que prende o
  último valor em todos os botões da lista.
---

:::story O último da lista
Quinta, 2 de abril, véspera do feriado. A Lívia ligou para a Cláudia às
6h02.

— Cancelei a E-5340, da padaria. Sumiu a E-5347, do mercado.

— A E-5347 era a última da lista?

— Era.

Às 9h o Paulo tinha a reprodução: qualquer botão "cancelar" da lista de
Franca cancelava a última entrega de Franca. A Bia abriu o trecho que
monta os botões, em `lista.js`:

```javascript
for (var i = 0; i < entregas.length; i++) {
  var botao = criarBotao("cancelar");
  botao.onclick = function () {
    cancelar(entregas[i].codigo);
  };
}
```

— O `i` é o da volta — disse ela. — Cada botão tem o seu.

— Tem? — perguntou o Rafael.

— Cada função foi criada numa volta diferente.

— Foi. E todas olham para o mesmo `i`.
:::

## Uma função lembra onde nasceu

Uma função criada dentro de outra enxerga os nomes de quem a criou — e
continua enxergando **depois** que a de fora terminou.

```javascript title="contador.js" numbered
function criarContador(nome) {
  let total = 0;
  return function () {
    total++;
    console.log(`${nome}: ${total}`);
  };
}

const canceladas = criarContador("canceladas");
const entregues = criarContador("entregues");

canceladas();
canceladas();
entregues();
canceladas();
```

```text
$ node contador.js
canceladas: 1
canceladas: 2
entregues: 1
canceladas: 3
```

`criarContador` terminou nas duas linhas do `const`. Mesmo assim, a função
que ela devolveu continua lendo e mudando `total` e `nome`. E cada chamada
de `criarContador` criou um `total` diferente: o de `canceladas` e o de
`entregues` não se misturam.

:::term Closure
Uma função junto com os nomes que ela enxergava onde foi criada. A função
leva esses nomes consigo — não uma cópia dos valores, os **próprios
nomes** —, e lê o valor que eles tiverem na hora em que ela rodar.

Todo callback do capítulo @cap:callbacks que usava uma variável de fora
era uma closure.
:::

A frase entre travessões é a que explica o defeito. A closure não guarda o
valor da variável no momento em que foi criada. Guarda a variável. Se a
variável mudar depois, a função vê a mudança.

## O laço com `var`

Os botões da lista de Franca, reproduzidos sem navegador — cada "botão" é
uma função guardada num array, e clicar é chamá-la:

```javascript title="botoes.js" numbered
const entregas = ["E-5340", "E-5341", "E-5347"];
const botoes = [];

for (var i = 0; i < entregas.length; i++) {
  botoes.push(function () {
    console.log(`cancelando ${entregas[i]}`);
  });
}

botoes[0]();
botoes[1]();
botoes[2]();
```

```text
$ node botoes.js
cancelando undefined
cancelando undefined
cancelando undefined
```

Pior que o painel: nem a última. O capítulo @cap:escopo mostrou que o
`var` é **um nome só**, da função ou do arquivo inteiro. As três funções
foram criadas enxergando esse mesmo `i`. Quando o laço termina, ele vale
`3` — a posição depois da última. Os botões só são clicados depois, e os
três leem `i`, que é `3`, e `entregas[3]` não existe.

No painel, o laço usava `entregas.length - 1` num ponto e `i` noutro, e o
que sobrava era a última entrega — a E-5347 —, que existia. Por isso a
reclamação da Lívia era "cancela a última", e não "não cancela nada". O
mecanismo é o mesmo.

## O laço com `let`

```javascript title="botoes.js" numbered
for (let i = 0; i < entregas.length; i++) {
  botoes.push(function () {
    console.log(`cancelando ${entregas[i]}`);
  });
}
```

```text
$ node botoes.js
cancelando E-5340
cancelando E-5341
cancelando E-5347
```

Uma palavra de diferença. Com `let`, **cada volta do laço tem o seu
próprio `i`** — o JavaScript cria um nome novo por volta, com o valor
daquela volta. Cada função enxerga o `i` da volta em que nasceu, e esse
`i` nunca muda depois.

:::key
Uma closure enxerga a **variável**, não o valor que ela tinha. Função
criada dentro de um laço com `var` enxerga o mesmo nome em todas as voltas,
e na hora de rodar lê o último valor. Com `let` ou `const`, cada volta tem
o seu.
:::

## Melhor ainda: não depender da posição

O `let` resolve o defeito. A forma que o painel novo usa evita a pergunta:

```javascript title="botoes.js" numbered
for (const codigo of entregas) {
  botoes.push(() => console.log(`cancelando ${codigo}`));
}
```

Cada função fecha sobre o `codigo` da volta — um `const` que nasce e não
muda. Não há posição para ser lida depois, nem array que possa ter mudado
entre a criação do botão e o clique.

Esse segundo ponto importa. Com `entregas[i]`, mesmo com `let`, a função
lê o array **na hora do clique**. Se a lista tiver sido reordenada ou
filtrada nesse meio tempo, a posição `i` pode ser de outra entrega.
Fechar sobre o código, e não sobre a posição, fecha sobre o que o botão
quer dizer.

## Closure de propósito

O mesmo mecanismo que causou o defeito serve para guardar estado sem
variável global. O capítulo @cap:promises controlava as rodadas com um
`let rodadaAtual` solto no arquivo. Com uma closure, cada linha da tela
tem o seu:

```javascript title="rodada.js" numbered
function criarAtualizador(codigo) {
  let rodadaAtual = 0;

  return async function atualizar(buscar) {
    rodadaAtual++;
    const minha = rodadaAtual;
    const dados = await buscar(codigo);
    if (minha !== rodadaAtual) {
      return;
    }
    console.log(`${codigo}: ${dados}`);
  };
}

const atualizarE5261 = criarAtualizador("E-5261");
```

`rodadaAtual` não existe fora de `criarAtualizador`. Nenhum outro código
do painel consegue ler ou mudar esse número por engano. E cada entrega da
lista tem o seu atualizador, com a sua contagem.

:::pitfall
Uma closure mantém vivos os nomes que ela enxerga enquanto ela existir. Um
botão removido da tela, mas ainda guardado num array de ouvintes, mantém
na memória a entrega e tudo que a função enxergava. No painel que fica
aberto das 5h40 às 18h, isso se acumula. Quem remove o botão remove
também o ouvinte.
:::

:::milestone
Fim da Parte 4. O painel da Bia não confunde mais a ordem do código com a
ordem dos acontecimentos: a falha da notificação não segura a tela, a
resposta velha não escreve por cima da nova, o `await` esquecido tem cara
conhecida, e cada botão cancela a própria entrega.
:::

:::summary
- Uma função criada dentro de outra enxerga os nomes de quem a criou,
  mesmo depois que a de fora terminou. Isso é uma closure.
- A closure guarda a variável, não o valor. Lê o valor da hora em que
  roda.
- Funções criadas num laço com `var` compartilham o mesmo nome; com `let`
  ou `const`, cada volta tem o seu.
- Feche sobre o que o valor significa — o código da entrega —, não sobre a
  posição num array que pode mudar.
- Closure de propósito guarda estado privado, sem variável global.
:::

:::exercise level=1
Diga o que o trecho imprime, e o que imprimiria com `let`:

```javascript
const avisos = [];
for (var h = 6; h <= 8; h++) {
  avisos.push(() => console.log(`aviso das ${h}h`));
}
avisos.forEach((f) => f());
```

:::answer
Com `var`: três vezes `aviso das 9h`. O laço termina quando `h` vale `9`,
e as três funções leem o mesmo `h`.

Com `let`: `aviso das 6h`, `aviso das 7h`, `aviso das 8h`. Cada volta tem
o seu `h`.

O `9h` é o sintoma mais revelador: um horário que nem está na lista.
:::

:::exercise level=2
Escreva `criarLimitador(maximo)`, que devolve uma função. Cada chamada da
função devolve `true` enquanto não passou de `maximo` chamadas, e `false`
depois. Use-a para permitir três tentativas de reenvio de aviso.

:::answer
```javascript
function criarLimitador(maximo) {
  let chamadas = 0;
  return function () {
    chamadas++;
    return chamadas <= maximo;
  };
}

const podeReenviar = criarLimitador(3);
console.log(podeReenviar(), podeReenviar(), podeReenviar());
console.log(podeReenviar());
```

```text
true true true
false
```

`chamadas` só existe dentro da closure. Cada `criarLimitador(3)` cria um
contador novo: a E-5230 e a E-5231 têm três tentativas cada, sem dividir.
:::

:::exercise level=3
O painel tem um relógio que, a cada 30 segundos, confere se alguma entrega
passou do prazo:

```javascript
let entregas = carregarManha();
setInterval(() => conferirPrazos(entregas), 30000);

function recarregar() {
  entregas = carregarManha();
}
```

A Bia troca o `let` por `const` e cria a lista nova com
`const novas = carregarManha()` dentro de `recarregar`. O relógio passa a
conferir a lista das 5h40 o dia inteiro. Explique e corrija.

:::answer
A função do `setInterval` fecha sobre o nome `entregas`. No original, com
`let`, `recarregar` reatribuía esse nome, e a closure lia a lista nova na
volta seguinte.

Na versão da Bia, `entregas` é `const` e nunca muda. A lista nova vai
para `novas`, um nome que a closure do relógio não enxerga. O relógio
continua lendo o que `entregas` apontava às 5h40.

Uma correção mantém um único lugar de onde todos leem, e faz `recarregar`
mudar esse lugar:

```javascript
const estado = { entregas: carregarManha() };
setInterval(() => conferirPrazos(estado.entregas), 30000);

function recarregar() {
  estado.entregas = carregarManha();
}
```

A closure fecha sobre `estado`, que nunca muda de objeto; a propriedade
`entregas`, lida na hora, é a mais recente.
:::
