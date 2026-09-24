---
title: "Antes de começar"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Três jeitos de pedir a mesma entrega, um comentário pedindo para não mexer, e uma lista impressa às 5h35 que ainda manda mais que o painel."
---

Esta é a pasta do painel da Borba, no ar desde março de 2022:

```text
painel/
  package.json
  index.html
  lista.js
  lista.css
  entrega.js
  http/
    client.js
```

O `package.json` anota uma biblioteca, o Axios, na versão 0.21.1. O
`lista.js` pede dados com `fetch`, que já vem com a linguagem. A pasta
`http/` tem um terceiro jeito, escrito à mão. Os três perguntam a outro
computador como está uma entrega.

No fim de `entrega.js` tem um comentário de duas linhas de idade e quatro
anos de obediência:

```javascript
// NÃO MEXER. FUNCIONA.
```

E funciona.

Cento e sessenta motoristas, três cidades, o primeiro caminhão saindo às
5h40. A Lívia imprime a lista às 5h35. Quando o papel e o painel discordam,
o caminhão sai pelo papel. O Seu Aldo, no cais, acredita no papel. Nesses
quatro anos ele acertou o bastante para a sala inteira ter aprendido a não
discutir.

Você vai escrever o programa que merece discordar dele. A pasta de produção
fica onde está. Mexer nela na primeira semana é o jeito mais curto de parar
a manhã.

## A Borba, a Calha e a data

A **Borba Entregas** faz entrega no mesmo dia em Ribeirão Preto, Franca e
São Carlos. A **Estúdio Calha** — dezenove pessoas, o tipo de casa de
software que herda o sistema quando quem escreveu já foi embora — assinou
para o painel aguentar uma cláusula nova.

E existe uma data que ninguém pode empurrar.

A **Mercado Leste**, onze lojas, renova o contrato com a Borba na
quarta-feira, **6 de maio**. O fornecimento vale R$ 2,1 milhões por ano. A
cláusula nova pede que cada status apareça no painel em até trinta segundos
depois da marcação do motorista. Cada atraso custa R$ 3,50. A Lívia contou
o buraco de hoje em cerca de 2.400 por dia: R$ 8.400 por dia, mais de
R$ 180 mil num mês, se nada mudar.

O contrato da Calha é R$ 96 mil, preço fechado. Um terço disso já virou
reunião. Se a cláusula estiver de pé em 6 de maio, começa uma mensalidade
de R$ 14 mil. Se não estiver, a Borba paga a multa e a mensalidade não
começa.

O servidor que serve o painel de manhã roda **Node 20**. Essa linha deixa
de receber correção em **30 de abril**, seis dias antes da renovação.

## Quem aparece

**Bia** entrou na Calha em 2 de março. Recebeu acesso ao repositório na
sexta, dia 13, e passou o fim de semana lendo a pasta. Aprende rápido. A
pergunta que ela faz é, em geral, a que a sala estava evitando.

**Rafael** é sênior. Já viu decisão temporária o bastante para saber quanto
tempo ela dura. Responde curto e, quando pode, aponta para o arquivo em vez
de explicar.

**Marcos** é o tech lead. Gosta de arquitetura e de desenhar coisa que ainda
não existe. A tentativa de trocar um cliente HTTP por outro, pela metade, é
dele.

**Cláudia** é a PO. Traduz a operação para o time. A tradução às vezes perde
a restrição, porque ela não estava no cais às 5h40. O ofício dela é esse:
transformar a frase da Lívia em alguma coisa que vira tarefa.

**Paulo** é o QA. Tem um prazer quase científico pelo caso que o
desenvolvedor jurou que não acontecia.

**Neto** é o DevOps. Aparece quando alguém diz que funciona na própria
máquina.

**Lívia Borba** toca a operação. Imprime a lista, abre o painel, e é a
única pessoa do contrato capaz de descrever o que o sistema faz.

**Seu Aldo** fundou a Borba com uma van, em 1998. Continua no cais às 5h40.
Quase não entra em reunião. Quando o papel e a tela discordam, o caminhão
obedece a ele.

**Diego Pacheco** escreveu o painel em março de 2022 e saiu da Calha em
novembro de 2024. O comentário é dele. Não é vilão. O arquivo despachou
caminhão por quatro anos.

**Renato** fundou a Calha. Nunca escreveu JavaScript e não finge que
escreveu. Volta de palestra com uma caixa nova no slide.

E o **painel**, com o comentário no fim da função, é o sistema em produção.
Cada coisa nova que aparecer aqui vai ser medida contra ele.

## Como o código aparece

Código aparece assim, às vezes com o nome do arquivo:

```javascript title="status.js"
const situacao = "a caminho";
console.log(situacao);
```

`const` cria um nome e o prende a um valor. Aqui o valor é o texto entre
aspas. `console.log` escreve esse valor no terminal. O ponto e vírgula
encerra a instrução.

O que o terminal responde aparece sem nome de arquivo e sem realce:

```text
a caminho
```

Quando o programa quebra, o que interessa vem primeiro: o arquivo, a linha,
um cursor em cima do ponto e o tipo da falha. As linhas de baixo, quando
aparecerem, são o motor atravessando o próprio código até chegar na sua.
A primeira é a sua.

:::key
Comando de terminal aparece com `$` na frente. O `$` representa o prompt e
não faz parte do comando: não digite.
:::

Você não precisa instalar nada para começar a ler. Quando o primeiro
programa precisar rodar, a instalação vem junto, com o teste que confirma
que deu certo.

A data que ninguém pode empurrar é 6 de maio. Até lá, a Lívia imprime às
5h35, e o caminhão sai pelo papel quando o painel discorda.
