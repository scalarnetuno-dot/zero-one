---
title: "Debugging"
number: 17
slug: debugging
part: p5
kicker: "Ticket 1847: a entrega some da lista quando a Lívia cancela. Três pessoas tentaram reproduzir e não conseguiram. O Paulo diminuiu a janela."
goal: >-
  Reproduzir um defeito antes de explicá-lo, usar as ferramentas de
  desenvolvedor do navegador — elementos, estilo calculado, console, ponto
  de parada —, e separar a causa do sintoma quando o sintoma aponta para o
  lugar errado.
---

:::story O bug impossível
Quarta, 8 de abril. O ticket 1847 estava aberto havia seis dias.

> **1847.** Ao cancelar uma entrega, ela some da lista. Deveria continuar
> aparecendo, riscada, até o fim do dia. (Lívia, pelo telefone)

A Bia tinha tentado na segunda: cancelou três entregas em homologação. As
três ficaram na lista, riscadas. O Marcos tentou na terça, no computador
dele: riscadas. A Cláudia pediu para a Lívia gravar a tela, e a Lívia
respondeu que estava no cais, com o tablet, e que não sabia gravar.

— Não reproduz — disse o Marcos, na reunião das 10h. — Deve ser cache.

O Paulo, que não tinha falado a reunião inteira, pegou o notebook, abriu o
painel de homologação e arrastou a borda da janela do navegador para a
esquerda, até ela ficar da largura de um tablet. Cancelou a E-5460.

A linha sumiu.

Ele arrastou a borda de volta. A linha reapareceu, riscada.

— Não é o cancelamento — disse ele. — É a janela.
:::

## Reproduzir antes de explicar

O ticket 1847 descrevia um **sintoma** — "ao cancelar, some" — e três
pessoas foram procurar a causa no cancelamento. Todas abriram o código de
`cancelar`, todas o acharam certo, e todas estavam certas. O código de
cancelar não fazia a entrega sumir.

A pergunta que o Paulo fez não foi "por que some?". Foi "o que é diferente
entre a Lívia e nós?". A Lívia usa um tablet, no cais, na horizontal. As
três tentativas foram em monitores de escritório.

:::key
Antes de explicar um defeito, reproduza-o. Se não reproduz, a pergunta
não é "onde está o erro no código", é "o que a pessoa que viu tem de
diferente": o aparelho, o tamanho da tela, o navegador, a conta, a hora,
os dados. Explicação sem reprodução é um palpite com cara de diagnóstico.
:::

Reproduzido, o defeito tem uma receita:

1. janela com menos de 900 pixels de largura;
2. uma entrega na lista;
3. cancelar.

A linha some. Com a janela larga, não some. É a receita que vai no ticket,
antes de qualquer hipótese.

## As ferramentas do navegador

F12, ou botão direito e "Inspecionar", abre as ferramentas de
desenvolvedor. O capítulo @cap:primeiro-programa usou o **Console**. Para
um elemento que some, a aba certa é outra.

**Elementos** mostra o DOM do capítulo @cap:dom-e-eventos, vivo, como está
agora — não o HTML que veio do servidor. Com a janela estreita e a E-5460
cancelada, a Bia procurou a linha:

```html
<li class="entrega cancelada" data-codigo="E-5460">
  E-5460 · Padaria Jardim · cancelada
</li>
```

O elemento **existe**. O cancelamento não o apagou. Ele está na página e
não aparece. Isso muda a pergunta de novo: não é "quem removeu?", é "o que
o esconde?".

## O estilo calculado

Com o `<li>` selecionado, o painel ao lado mostra os estilos. A aba
**Calculado** (*Computed*) mostra o valor **final** de cada propriedade —
depois de todas as regras de CSS que se aplicam ao elemento terem brigado
entre si:

```text
display: none
```

E, ao lado da propriedade, o arquivo e a linha da regra que venceu:

```text
lista.css:212
```

```css title="lista.css (linhas 205–215)"
@media (max-width: 900px) {
  .entrega {
    padding: 4px 8px;
    font-size: 14px;
  }

  .entrega.cancelada {
    display: none;
  }
}
```

`@media (max-width: 900px)` aplica as regras de dentro só quando a janela
tem até 900 pixels. Dentro dela, `.entrega.cancelada` — um elemento com as
duas classes — recebe `display: none`, que o tira da página.

O `git log` de `lista.css` tinha a mensagem do commit: `versão mobile:
esconde canceladas para caber na tela`, de outubro de 2023. Alguém pensou
num celular. Ninguém pensou que o tablet do cais, na horizontal, tinha 890
pixels.

:::term Estilo calculado
O valor final que o navegador aplica a cada propriedade de CSS de um
elemento, depois de resolver todas as regras que o atingem. As ferramentas
de desenvolvedor mostram esse valor e a regra de onde ele veio.

Quando um elemento "some", o estilo calculado responde se ele está lá e
escondido, ou se não está lá.
:::

## Causa e sintoma

| | O que o ticket dizia | O que era |
|---|---|---|
| sintoma | "ao cancelar, some" | a linha some com a janela estreita |
| o que o cancelamento fazia | parecia a causa | só punha a classe `cancelada` |
| causa | — | a regra de 2023 para celular |

Tabela: O cancelamento fornecia o estado. A regra de CSS fazia o resto. As
três pessoas que leram o código de `cancelar` estavam lendo o código certo
para a pergunta errada.

A correção é uma linha. A Lívia confirmou que quer ver as canceladas em
qualquer tela, riscadas:

```css title="lista.css (depois)"
@media (max-width: 900px) {
  .entrega {
    padding: 4px 8px;
    font-size: 14px;
  }
}
```

A regra que escondia saiu. A regra geral, fora do `@media`, já riscava a
entrega cancelada, e passou a valer também no tablet.

## O console, e o `debugger`

Nem todo defeito está no CSS. Para o que está no JavaScript, as mesmas
ferramentas têm duas formas de olhar por dentro.

**O console, de propósito.** `console.log` no meio do código, com o nome
do que se imprime:

```javascript
console.log("cancelar", { codigo, statusAntes: e.status });
```

Com um objeto entre chaves, o console mostra os nomes junto com os
valores. `console.log(codigo, status)` imprime dois textos soltos, e às
5h40 ninguém lembra qual era qual.

**O ponto de parada.** A palavra `debugger` numa linha, com as ferramentas
abertas, **para** a execução ali:

```javascript
function cancelar(codigo) {
  const e = estado.entregas.find((x) => x.codigo === codigo);
  debugger;
  e.status = "cancelada";
  desenhar();
}
```

A página congela na linha. A aba **Fontes** (*Sources*) mostra o arquivo,
a linha destacada, e o valor de cada nome visível ali — `codigo`, `e`,
`estado`. Os botões de passo avançam uma linha por vez. É o `console.log`
de todas as variáveis ao mesmo tempo, sem ter de adivinhar qual imprimir.

O mesmo efeito, sem mudar o arquivo: clicar no número da linha na aba
Fontes marca um ponto de parada.

:::pitfall
`debugger` e `console.log` de investigação esquecidos vão para produção. O
`debugger` não faz nada na tela da Lívia — as ferramentas dela estão
fechadas —, e o `console.log` escreve para ninguém. O custo não é o
defeito; é o arquivo que mente sobre o que é código de verdade. Antes do
commit, a busca por `debugger` e por `console.log(` no que mudou.
:::

## O teste da receita

A receita do 1847 virou uma conferência que qualquer um roda antes de
fechar uma mudança na lista: abrir o painel, estreitar a janela até 800
pixels, cancelar uma entrega, e ver a linha riscada. As ferramentas de
desenvolvedor têm um modo de dispositivo — o ícone do celular e do
tablet no canto — que fixa a largura sem arrastar borda.

O ticket foi fechado com a receita, a causa, a linha removida, e o nome do
Paulo no campo "reproduzido por".

:::summary
- Reproduza antes de explicar. Se não reproduz, procure o que a pessoa que
  viu tem de diferente.
- A receita do defeito vai no ticket antes da hipótese.
- A aba Elementos mostra o DOM vivo: se o elemento existe, algo o
  esconde; se não existe, algo o removeu.
- O estilo calculado mostra o valor final e a regra de onde ele veio.
- O sintoma aponta para onde o defeito aparece, não para onde ele está.
- `console.log` com nomes; `debugger` para parar e olhar tudo. Os dois
  saem antes do commit.
:::

:::exercise level=1
Um item da lista não aparece. Na aba Elementos, ele está lá. Diga três
propriedades de CSS que você procuraria no estilo calculado.

:::answer
`display: none`, que o tira da página; `visibility: hidden`, que o deixa
ocupando espaço mas invisível; e `opacity: 0`, que o deixa transparente.

E, fora dessas três, a posição: um elemento com `height: 0` e
`overflow: hidden`, ou posicionado fora da área visível. O estilo
calculado mostra todas, com a regra de origem.
:::

:::exercise level=2
A Cláudia abre o ticket 1851: "o total de fretes do rodapé está errado às
vezes". Escreva as três primeiras perguntas que você faria antes de abrir
o código.

:::answer
Errado quanto, e comparado com o quê? Um print com o total da tela e o
número que ela esperava, e de onde veio esse número.

Quando? Em que horário, depois de qual ação — cancelar, ajustar frete,
atualizar —, e se some sozinho depois.

Onde? Em qual aparelho, com qual tela, com a lista de qual cidade.

As três perguntas buscam a receita. "Às vezes" quase sempre esconde uma
condição que ainda não foi descoberta, como a largura da janela no 1847.
:::

:::exercise level=3
O Marcos propõe, para evitar o próximo 1847, proibir `display: none` em
todo o `lista.css`. Responda.

:::answer
A proibição ataca a ferramenta, e não o defeito. `display: none` é o jeito
certo de esconder o menu fechado, o aviso já lido, o botão que não se
aplica. Proibido, ele volta como `height: 0` ou `opacity: 0`, que escondem
do mesmo jeito e são mais difíceis de achar no estilo calculado.

O defeito do 1847 foi uma regra de **negócio** — o que a operação vê —
escrita no CSS, sem ninguém da operação saber. A proposta que eu levaria:
regra de CSS que esconde **dado** — entrega, frete, status — passa por
quem decide o que a Lívia vê, e a conferência da janela estreita entra na
lista do que se testa antes de subir.
:::
