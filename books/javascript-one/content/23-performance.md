---
title: "Performance"
number: 23
slug: performance
part: p7
kicker: "O relógio do canto da tela mudava a cada segundo. A cada segundo, cento e sessenta cartões eram jogados fora e feitos de novo. O tablet do cais esquentava."
goal: >-
  Medir antes de reescrever, contar quantas vezes a tela é refeita e por
  quê, e parar de reconstruir a lista inteira a cada evento que não muda
  a lista — com números antes e depois.
---

:::story O tablet quente
Quarta, 22 de abril, 6h05. A Lívia mandou uma mensagem de voz para a
Cláudia, que a transcreveu no ticket:

> O tablet trava quando eu rolo a lista. Às vezes eu toco em cancelar e
> ele demora para responder. E ele está quente. Nunca tinha esquentado.

A Bia abriu o painel novo no notebook. Rolou: normal. Abriu no tablet de
testes, o mesmo modelo do cais. Rolou: aos trancos.

— Mudou alguma coisa ontem? — perguntou o Rafael.

— O relógio. A Lívia pediu para saber a hora da última atualização. Pus
um "atualizado às 6h05:12" no canto.

— Que atualiza...

— A cada segundo.

— E como ele atualiza?

A Bia abriu o arquivo.

```javascript
setInterval(() => {
  estado.agora = new Date();
  desenhar();
}, 1000);
```

— Pelo `desenhar` — disse ela.

— Que desenha o quê?

— Tudo.
:::

## Medir primeiro

"Está lento" é uma sensação. Para mudar código por causa dela, primeiro
ela vira um número. Três formas, da mais simples para a mais completa.

**Contar.** Quantas vezes a coisa cara acontece? Um contador no ponto
suspeito:

```javascript
let redesenhos = 0;

function desenhar() {
  redesenhos++;
  // ...
}

setInterval(() => console.log(`redesenhos: ${redesenhos}`), 10000);
```

**Cronometrar.** Quanto tempo ela leva?

```javascript
const inicio = performance.now();
desenhar();
const ms = performance.now() - inicio;
console.log(`desenhar: ${ms.toFixed(1)} ms`);
```

`performance.now()` devolve o tempo em milissegundos, com fração, desde que
a página abriu. A diferença entre duas leituras é o tempo do que rodou no
meio.

**O painel de desempenho.** As ferramentas de desenvolvedor do capítulo
@cap:debugging têm a aba **Desempenho** (*Performance*): grava alguns
segundos da página e mostra, numa linha do tempo, onde o tempo foi —
script, cálculo de estilo, desenho na tela. É a ferramenta para quando o
contador e o cronômetro não explicam.

A Bia fez as duas primeiras no tablet, com o painel aberto por dez
segundos:

```text
redesenhos: 10
desenhar: 38.4 ms
desenhar: 41.2 ms
desenhar: 37.9 ms
```

Dez redesenhos em dez segundos: um por segundo, o relógio. Cada um,
quarenta milissegundos no tablet. É o que a Lívia sentia: durante esses
quarenta milissegundos, a página não responde ao dedo dela. Uma vez por
segundo, a lista travava um vigésimo de segundo — o bastante para o
toque em "cancelar" cair no meio.

:::key
Otimização sem medição é um palpite reescrito. Antes de mudar, conte ou
cronometre o que parece lento, e anote o número. Depois de mudar, meça de
novo, do mesmo jeito. A diferença entre os dois números é o que a mudança
fez — e às vezes ela não fez nada.
:::

## O que o redesenho fazia

O capítulo @cap:estado decidiu: a tela é desenhada a partir do estado, e
toda mudança redesenha. O relógio mudava o estado — `estado.agora` — e
chamava `desenhar`. E `desenhar` refazia as três regiões: a lista inteira,
o detalhe, o rodapé.

O relógio muda uma coisa: o texto do canto. A lista não mudou. Mas o
`desenhar` não sabe o que mudou; ele só sabe refazer tudo. O pitfall
daquele capítulo avisou: redesenhar tudo tem um custo, e a resposta, quando
ele aparecesse, era medir.

A reprodução, com a contagem de cartões criados em sessenta segundos:

```javascript title="relogio.js" numbered
const entregas = Array.from({ length: 160 }, (_, i) => ({
  codigo: `E-${5900 + i}`,
  status: "a caminho",
}));

let cartoesCriados = 0;

function desenharLista() {
  for (const e of entregas) {
    cartoesCriados++;
    // no navegador: criar o <li>, o botão, pôr na página
  }
}

function desenharRelogio(segundo) {
  return `atualizado às 6h05:${String(segundo).padStart(2, "0")}`;
}

// como estava: cada segundo do relógio redesenha tudo
for (let s = 0; s < 60; s++) {
  desenharLista();
  desenharRelogio(s);
}
console.log(`antes: ${cartoesCriados} cartões em 60 s`);

// como fica: a lista uma vez, o relógio sozinho
cartoesCriados = 0;
desenharLista();
for (let s = 0; s < 60; s++) {
  desenharRelogio(s);
}
console.log(`depois: ${cartoesCriados} cartões em 60 s`);
```

```text
$ node relogio.js
antes: 9600 cartões em 60 s
depois: 160 cartões em 60 s
```

`Array.from({ length: 160 }, função)` cria uma lista de 160 itens, cada um
feito pela função. No Node, criar um texto é quase grátis, e a contagem é
o que importa: nove mil e seiscentos cartões por minuto, sem nenhuma
entrega ter mudado. No tablet, cada cartão é um elemento de página, com
estilo calculado e desenho na tela.

## Redesenhar só o que mudou

O painel novo separa o que muda por motivos diferentes:

```javascript title="painel.js" numbered
function mudarEntregas(novas) {
  estado.entregas = novas;
  desenharLista(estado);
  desenharRodape(estado);
}

function mudarAberta(codigo) {
  estado.aberta = codigo;
  desenharDetalhe(estado);
}

setInterval(() => {
  estado.agora = new Date();
  desenharRelogio(estado);
}, 1000);
```

Cada mudança redesenha as regiões que dependem **do que mudou**. O relógio
redesenha o relógio. A lista só é refeita quando as entregas mudam — na
atualização de trinta segundos, num cancelamento, num ajuste de frete.

Não voltou nenhuma cópia de dado: as funções de desenho continuam lendo
do estado, e continuam puras. O que mudou é **quando** cada uma é chamada.

E a atualização de trinta segundos ganhou uma conferência: se a lista que
veio do servidor é igual à que já está na tela, não há o que redesenhar.

```javascript
function mudarEntregas(novas) {
  const antes = JSON.stringify(estado.entregas);
  const iguais = JSON.stringify(novas) === antes;
  if (iguais) {
    return;
  }
  estado.entregas = novas;
  desenharLista(estado);
  desenharRodape(estado);
}
```

`JSON.stringify` transforma as duas listas em texto, e texto se compara com
`===`. Para cento e sessenta entregas, é uma comparação barata comparada
com o redesenho que ela evita.

A medição de novo, no tablet, com o painel aberto por um minuto:

```text
redesenhos da lista: 1
redesenhos do relógio: 60
desenharRelogio: 0.1 ms
```

Um redesenho da lista — no carregamento; as duas atualizações do servidor
nesse minuto vieram iguais. Sessenta do relógio, de um décimo de
milissegundo cada. O tablet parou de esquentar, e a Lívia não mencionou
mais o toque que demorava.

:::pitfall
A comparação por `JSON.stringify` depende da ordem das propriedades: o
mesmo objeto com `status` antes de `codigo` vira outro texto. Para a lista
que o servidor manda sempre no mesmo formato, funciona. Para objetos
montados em lugares diferentes, pode dizer "diferente" para dois iguais —
e o custo é só um redesenho a mais. O erro contrário — "igual" para dois
diferentes — não acontece: textos iguais vêm de dados iguais.
:::

## Eventos que disparam demais

O relógio dispara uma vez por segundo. Há eventos que disparam muito mais:
`mousemove`, a cada pixel que o ponteiro anda; `scroll`, a cada passo da
rolagem; `input`, a cada tecla. Um ouvinte desses que redesenha a lista
faz, numa rolagem de um segundo, dezenas de redesenhos.

O painel de 2022 tinha um: o destaque da linha sob o ponteiro era feito
redesenhando a lista no `mousemove`. No painel novo, o destaque é uma
regra de CSS — `li:hover` —, que o navegador aplica sem JavaScript
nenhum. A decisão mais barata, quando dá, é não rodar código.

Para a busca por código, que filtra a lista a cada tecla, a espera: só
filtrar quando a pessoa parar de digitar por um instante.

```javascript
let espera;
busca.addEventListener("input", () => {
  clearTimeout(espera);
  espera = setTimeout(() => filtrar(busca.value), 200);
});
```

Cada tecla cancela a espera anterior e agenda outra. O filtro só roda 200
ms depois da última tecla. "E-59" digitado em quatro teclas rápidas vira
um filtro, não quatro.

:::milestone
Fim da Parte 7. O painel e o servidor têm um contrato escrito, que os
testes dos dois lados cobram; o painel confere o status da resposta antes
de riscar uma entrega; e a lista só é refeita quando uma entrega muda —
com o número de antes e o de depois anotados no ticket.
:::

:::summary
- Meça antes de mudar: contador, `performance.now()`, a aba Desempenho.
  Anote o número.
- Redesenhar tudo a cada mudança é simples e cobra caro quando algo muda
  com frequência sem mudar a lista.
- Cada mudança redesenha só as regiões que dependem dela. As funções de
  desenho continuam puras.
- Uma lista igual à que já está na tela não precisa ser redesenhada.
- Eventos frequentes — ponteiro, rolagem, tecla — resolvem-se com CSS
  quando dá, e com espera quando não dá.
- Meça de novo, do mesmo jeito. A diferença é o que a mudança fez.
:::

:::exercise level=1
O painel antigo tem este ouvinte:

```javascript
window.addEventListener("scroll", () => desenhar());
```

Diga como você mediria o custo dele, e o número que você procuraria.

:::answer
Um contador em `desenhar`, e uma rolagem de um segundo na lista de
Franca. O número é quantos redesenhos um segundo de rolagem produz —
provavelmente dezenas —, multiplicado pelo tempo de um redesenho medido
com `performance.now()`.

Se trinta redesenhos de quarenta milissegundos cabem num segundo de
rolagem, a rolagem passa um segundo inteiro redesenhando e nenhum tempo
rolando. O número torna óbvio o que "está travando" não tornava.
:::

:::exercise level=2
Escreva `criarEspera(funcao, ms)`, que devolve uma função: cada chamada
cancela a anterior e agenda `funcao` para `ms` depois. Use-a na busca.

:::answer
```javascript
function criarEspera(funcao, ms) {
  let agendado;
  return (...args) => {
    clearTimeout(agendado);
    agendado = setTimeout(() => funcao(...args), ms);
  };
}

const filtrarDepois = criarEspera(filtrar, 200);
busca.addEventListener("input", () => filtrarDepois(busca.value));
```

A closure do capítulo @cap:closures guarda o `agendado` de cada espera.
`...args` junta os argumentos recebidos numa lista e os repassa. É o mesmo
spread do capítulo @cap:desestruturacao-e-spread, usado em parâmetros.
:::

:::exercise level=3
O Marcos propõe trocar o `desenhar` por uma biblioteca de interface que
"só atualiza o que mudou, sozinha". Responda com o que os números deste
capítulo dizem.

:::answer
Os números dizem que o problema era de **quando** redesenhar, e que ele
foi resolvido com três funções chamadas nos momentos certos e uma
comparação de lista. A lista passou de 9.600 cartões por minuto para
160, e o relógio custa um décimo de milissegundo.

Uma biblioteca de interface resolve isso de forma geral, para telas com
dezenas de regiões que mudam por motivos cruzados. É uma dependência
nova — o capítulo @cap:npm contou o que custa uma —, com o próprio jeito
de pensar a tela, a duas semanas de 6 de maio.

Se, depois da renovação, a tela crescer a ponto de ninguém mais saber
quais regiões dependem de quê, a conversa volta, com a medição daquele
dia na mesa. Hoje, o número que motivaria a troca não existe.
:::
