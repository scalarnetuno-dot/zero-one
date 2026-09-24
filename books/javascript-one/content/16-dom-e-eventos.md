---
title: "DOM e eventos"
number: 16
slug: dom-e-eventos
part: p5
kicker: "Um clique em cancelar, dois pedidos de cancelamento. O segundo chegava ao servidor depois que a entrega já tinha mudado."
goal: >-
  Achar um elemento da página, ler e escrever o texto dele, escutar um
  clique, e perceber quando o mesmo botão ganhou dois ouvintes — com a
  página aberta no navegador e o clique contado.
---

:::story Dois pedidos
Segunda, 6 de abril, 14h. O Paulo mandou para o grupo um trecho do log do
servidor, sem comentário:

```text
14:02:11.380 POST /entregas/E-5402/cancelar  200
14:02:11.392 POST /entregas/E-5402/cancelar  409 já cancelada
```

— Um clique — escreveu ele depois. — Eu cliquei uma vez.

A Bia abriu o painel de homologação, abriu a aba de rede do navegador e
clicou em "cancelar" numa entrega. Dois pedidos. Recarregou a página e
clicou de novo, logo em seguida. Um pedido.

— Depende de quanto tempo a página está aberta — disse ela.

O Rafael pediu para ela esperar um minuto e clicar outra vez. Três
pedidos.

— A cada trinta segundos — disse ele — a lista se atualiza. E cada
atualização faz o quê?
:::

## A página como objeto

O navegador lê o HTML e monta, na memória, uma árvore de objetos: um para
cada elemento. O JavaScript da página enxerga essa árvore pelo nome
`document`.

:::term DOM
*Document Object Model*: a árvore de objetos que o navegador monta a partir
do HTML. Cada elemento vira um objeto, com propriedades — o texto, as
classes, os atributos — e métodos.

Mudar um objeto do DOM muda a página na hora. Não há "salvar".
:::

A página mínima do painel novo, na pasta `borba`:

```html title="index.html" numbered
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <title>Painel</title>
  </head>
  <body>
    <h1 id="titulo">Entregas</h1>
    <p>Cliques: <span id="contador">0</span></p>
    <ul id="lista"></ul>
    <script src="painel.js"></script>
  </body>
</html>
```

O `<script>` no fim do `body` carrega o `painel.js` depois de os elementos
existirem. No começo do arquivo, o script rodaria antes de o `<ul>` ter
sido lido, e não o encontraria.

## Achar e mudar

```javascript title="painel.js" numbered
const titulo = document.querySelector("#titulo");
titulo.textContent = "Entregas de Franca";

const lista = document.querySelector("#lista");
const entregas = ["E-5400", "E-5401", "E-5402"];

for (const codigo of entregas) {
  const item = document.createElement("li");
  item.textContent = codigo;
  lista.append(item);
}
```

Abra o `index.html` no navegador — dois cliques no arquivo bastam. O título
mudou e a lista tem três itens.

`document.querySelector("#titulo")` acha o primeiro elemento que bate com
o seletor: `#titulo` é "o elemento com `id` titulo" — a mesma escrita do
CSS. Se nenhum bater, devolve `null`, e a linha seguinte quebra com o
`TypeError` do capítulo @cap:arrays-e-objetos: não se lê propriedade de
`null`.

`textContent` é o texto do elemento. Escrever nele troca o texto.
`createElement("li")` cria um elemento novo, solto; `append` o põe dentro
de outro, no fim.

:::pitfall
Existe também `innerHTML`, que recebe HTML em texto e o monta. Ele é mais
curto, e é um buraco quando o texto vem de fora: um cliente cadastrado com
o nome `<img src=x onerror=...>` vira código rodando na tela da Lívia. O
painel novo escreve texto com `textContent`, que nunca interpreta HTML.
:::

## Escutar um clique

```javascript title="painel.js" numbered
const contador = document.querySelector("#contador");
let cliques = 0;

const botao = document.createElement("button");
botao.textContent = "cancelar E-5402";
document.body.append(botao);

botao.addEventListener("click", () => {
  cliques++;
  contador.textContent = cliques;
});
```

`addEventListener("click", função)` registra um **ouvinte**: uma função
que o navegador chama toda vez que aquele evento acontece naquele
elemento. É um callback, do capítulo @cap:callbacks, com o navegador no
papel de quem chama.

Clique três vezes. O contador marca 3.

## Dois ouvintes

O `lista.js` de produção montava os botões assim, a cada atualização:

```javascript
function atualizarLista() {
  // ... redesenha as linhas ...
  const botao = document.querySelector("#cancelar-" + codigo);
  botao.addEventListener("click", () => cancelar(codigo));
}

setInterval(atualizarLista, 30000);
```

O detalhe: o redesenho **mantinha** os botões que já existiam, só trocava
o texto das linhas. E cada chamada de `atualizarLista` acrescentava mais
um ouvinte ao mesmo botão. `addEventListener` não substitui: soma.

A reprodução, no `painel.js`:

```javascript title="painel.js" numbered
function registrar() {
  botao.addEventListener("click", () => {
    cliques++;
    contador.textContent = cliques;
  });
}

registrar();
registrar();
```

Recarregue a página e clique uma vez. O contador marca **2**. Clique de
novo: **4**. Dois ouvintes no mesmo botão, e um clique dispara os dois.

Na tela da Lívia, depois de uma hora aberta, o botão de cancelar tinha
cento e vinte ouvintes. O primeiro cancelava a entrega. Os outros cento e
dezenove chegavam ao servidor, que respondia `409 já cancelada` — até o
dia em que um deles chegou antes da resposta do primeiro, e o servidor
registrou dois cancelamentos com dois motivos diferentes.

:::key
`addEventListener` acrescenta; nunca substitui. Código que registra
ouvinte dentro de uma função que roda mais de uma vez — atualização,
redesenho, relógio — registra mais uma vez a cada rodada. Registre o
ouvinte **uma vez**, onde o elemento nasce.
:::

## Um ouvinte para a lista inteira

A forma que o painel novo usa não põe ouvinte em cada botão. Põe **um** na
lista, uma vez, e descobre qual botão foi clicado:

```javascript title="painel.js" numbered
lista.addEventListener("click", (evento) => {
  const botao = evento.target.closest("button[data-codigo]");
  if (!botao) {
    return;
  }
  cancelar(botao.dataset.codigo);
});

function desenhar(entregas) {
  lista.replaceChildren();
  for (const codigo of entregas) {
    const item = document.createElement("li");
    const botao = document.createElement("button");
    botao.textContent = "cancelar";
    botao.dataset.codigo = codigo;
    item.append(codigo, " ", botao);
    lista.append(item);
  }
}
```

O ouvinte recebe o **evento**: um objeto que descreve o clique.
`evento.target` é o elemento em que o clique aconteceu. `closest` sobe da
origem até achar um `button` com o atributo `data-codigo` — ou devolve
`null`, se o clique foi fora de um botão.

`botao.dataset.codigo` escreve e lê o atributo `data-codigo` do HTML. É o
jeito de pendurar um dado num elemento: o botão carrega o código da
própria entrega, e não depende de posição — a lição do capítulo
@cap:closures, agora no HTML.

`replaceChildren()` esvazia a lista antes de redesenhar. `desenhar` pode
rodar a cada trinta segundos sem acumular nada: os botões são recriados,
e o único ouvinte, o da lista, foi registrado uma vez, fora dela.

Com o `painel.js` novo, clique uma vez: um pedido. Espere dez
atualizações e clique de novo: um pedido.

:::summary
- O DOM é a árvore de objetos do HTML. `document.querySelector` acha;
  `textContent` lê e escreve texto; `createElement` e `append` criam.
- `innerHTML` com dado de fora é um buraco; `textContent` não interpreta.
- `addEventListener` registra um ouvinte — e soma, nunca substitui.
- Ouvinte registrado numa função que roda várias vezes se multiplica. Um
  clique vira vários pedidos.
- Um ouvinte na lista, registrado uma vez, com `evento.target.closest` e
  `dataset`, aguenta o redesenho.
:::

:::exercise level=1
Na página do capítulo, escreva o código que muda o texto do título para
"Entregas de hoje: 3", usando o tamanho da lista.

:::answer
```javascript
const titulo = document.querySelector("#titulo");
titulo.textContent = `Entregas de hoje: ${entregas.length}`;
```

Se o seletor estiver errado — `#Titulo`, com maiúscula —, `titulo` é
`null`, e a segunda linha dá `TypeError: Cannot set properties of null`. O
seletor diferencia maiúscula de minúscula, como o `id` no HTML.
:::

:::exercise level=2
O botão "atualizar agora" do painel chama `atualizarLista()`, e dentro
dela há um `addEventListener` para o botão "imprimir". Depois de a Lívia
clicar em "atualizar agora" cinco vezes, quantas vezes a impressão sai
quando ela clica em "imprimir"? Corrija.

:::answer
Seis — o ouvinte registrado no carregamento, mais um a cada atualização.
A impressora recebe seis cópias da lista.

A correção tira o registro de dentro de `atualizarLista`:

```javascript
const imprimir = document.querySelector("#imprimir");
imprimir.addEventListener("click", () => window.print());

function atualizarLista() {
  // ... só redesenha ...
}
```

O botão "imprimir" existe desde o carregamento e não é recriado. O ouvinte
dele é registrado uma vez, junto com o resto da página.
:::

:::exercise level=3
O servidor responde `409` ao segundo cancelamento. O Marcos propõe
resolver o defeito do capítulo só no servidor: "já responde 409, basta a
tela ignorar". Responda.

:::answer
O `409` protege o dado, e é bom que exista. Ele não resolve o defeito da
tela, por três motivos.

Os pedidos a mais continuam saindo: cento e vinte por clique depois de uma
hora, multiplicados por todas as telas abertas da operação. É carga que o
servidor não precisava ter.

A proteção depende da ordem: o `409` só vem se o primeiro pedido já foi
gravado quando o segundo chega. Dois pedidos quase simultâneos podem ser
atendidos ao mesmo tempo — foi o que registrou dois motivos.

E ignorar o erro na tela é ensinar a tela a ignorar erro: o próximo `409`
de verdade — outra pessoa cancelou antes — some junto.

O servidor recusa; a tela não manda o que não devia. As duas coisas.
:::
