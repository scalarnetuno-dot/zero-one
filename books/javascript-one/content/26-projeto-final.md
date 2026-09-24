---
title: "Projeto final"
number: 26
slug: projeto-final
part: p8
kicker: "Quarta, 6 de maio, 5h35. A Lívia imprimiu a lista, pôs o papel ao lado do tablet e foi descendo com o dedo."
goal: >-
  Juntar o que o livro construiu na pasta borba — lista, status, frete, o
  teste do caso do Paulo, o contrato com o servidor, um commit legível e um
  jeito de subir que o Neto aceita numa segunda — e fazer, sozinho, o
  próximo pedido que a operação vai trazer.
---

:::story O papel e a tela
Quarta, 6 de maio, 5h35. A impressora do cais soltou três folhas. A Lívia
as pôs na prancheta, ao lado do tablet, e foi descendo com o dedo.

— E-6311, Franca, a caminho. Bate. E-6312, Franca, a caminho. Bate.
E-6313, padaria do Jardim, sem cidade no sistema, conferir endereço. —
Ela olhou o quadro no fim da folha. — Bate. Está no quadro.

A Bia estava encostada na porta do escritório do cais, com um café que o
Seu Aldo tinha oferecido sem dizer nada. O Rafael, ao lado, não tinha
aceitado o café.

Às 5h44, o motorista da rota de São Carlos marcou a E-6231 como entregue
no celular. A Lívia olhou o relógio do tablet. Às 5h44 e nove segundos, a
linha mudou.

— Nove segundos — disse ela, para ninguém.

O Seu Aldo passou atrás dela, olhou a prancheta, olhou o tablet. Pegou a
folha de São Carlos e dobrou.

— Pode soltar — disse ele.

— O caminhão? — perguntou a Lívia.

— O papel.
:::

## O que a pasta tem

A pasta `borba`, na manhã da renovação:

:::tree title="A pasta borba em 6 de maio"
borba/
  package.json          engines >=22, scripts start e test
  package-lock.json
  .nvmrc                24
  .gitignore            node_modules/, .env
  situacoes.js          as situações e a tradução para o contrato
  frete.js              calcularFrete, formatarReais
  api.js                gravarStatus, buscarCanceladas — só fetch
  estado.js             o estado e as funções que o mudam
  desenho.js            lista, detalhe, rodapé, relógio
  painel.js             liga o estado à página
  servidor.js           o servidor mínimo do contrato
  index.html
  test/
    frete.test.js
    intervalo.test.js   o caso do Paulo
    contrato.test.js    os valores de status do contrato
:::

Nenhum arquivo tem mais de oitenta linhas. Os `import` vão numa direção
só: `situacoes.js` e `frete.js` não importam nada; `painel.js` importa
todos.

O painel de produção, o de 2022, continua no ar para o que o painel novo
ainda não faz — a roteirização, o cadastro de clientes. `entrega.js`
continua com cento e oitenta linhas e o comentário na última. Foi de lá
que saíram, uma por vez e conferidas, as regras que a pasta `borba` tem:
o frete, a situação, a tradução do sistema antigo.

## Subir e testar

Dois comandos, que o Neto roda no servidor e a Bia roda na máquina dela, e
que dão o mesmo resultado nas duas:

```text
$ npm ci
added 0 packages in 0.4s

$ npm test
✔ Franca, 8 kg, sem urgência
✔ Franca, 5 kg, sem extra
✔ Franca, 6 kg, um quilo de extra
✔ iniciar rota muda para a caminho
✔ cancelar enquanto a rota ainda grava
✔ iniciar rota enquanto o cancelamento grava
✔ o painel só manda status do contrato
ℹ tests 7
ℹ pass 7
ℹ fail 0

$ npm start
painel em :8080, servidor de entregas em https://api.borba...
```

`added 0 packages`: o Axios saiu no capítulo @cap:npm, e a pasta não
depende de nada além do Node. Os sete testes são sete frases que alguém
na Borba disse em voz alta nos últimos dois meses — incluindo as duas do
Paulo, que ele jurou que ia achar e achou.

## Três entregas, o papel e a tela

A conferência da manhã, feita na segunda, 4 de maio, com três entregas de
exemplo que cobrem os casos que já tinham dado errado:

```javascript title="conferencia.js" numbered
import { doSistemaAntigo } from "./situacoes.js";
import { calcularFrete, formatarReais } from "./frete.js";

const papel = [
  "E-6201 | Franca | a caminho | R$ 21,60",
  "E-6202 | São Carlos | cancelada | R$ 22,90",
  "E-6203 | (sem cidade) | a caminho | R$ 12,90",
];

const sistemaAntigo = [
  { codigo: "E-6201", situacao: "EM ROTA", municipio: "FRANCA",
    peso: 8 },
  { codigo: "E-6202", situacao: "CANCELADA", municipio: "SÃO CARLOS",
    peso: 3 },
  { codigo: "E-6203", situacao: "EM ROTA", municipio: "", peso: 2 },
];

const tela = sistemaAntigo.map((a) => {
  const e = doSistemaAntigo(a);
  const frete = calcularFrete({ cidade: e.cidade, pesoKg: a.peso });
  const cidade = e.cidade || "(sem cidade)";
  const reais = formatarReais(frete);
  return `${e.codigo} | ${cidade} | ${e.status} | ${reais}`;
});

tela.forEach((linha, i) => {
  const ok = linha === papel[i] ? "bate" : "DIFERENTE";
  console.log(`${ok}: ${linha}`);
});
```

```text
$ node conferencia.js
bate: E-6201 | Franca | a caminho | R$ 21,60
bate: E-6202 | São Carlos | cancelada | R$ 22,90
bate: E-6203 | (sem cidade) | a caminho | R$ 12,90
```

A E-6201 é o frete do capítulo @cap:funcoes. A E-6202 é a tradução do
capítulo @cap:arrays-e-objetos e a base nova de São Carlos do capítulo
@cap:git. A E-6203 é a entrega sem cidade do capítulo @cap:repeticoes, que
em março sumia da lista e agora aparece — com o frete da base padrão, que
a Lívia confere à mão, porque sem cidade o sistema não sabe outra coisa.

As três linhas batem com o papel. Não porque o código foi escrito para
isso: porque cada regra que produz essas linhas foi tirada de um defeito
que a Lívia viu, conferida contra o que havia antes, e coberta por um
teste.

## Os trinta segundos

A cláusula da Mercado Leste: cada status marcado pelo motorista aparece no
painel em até trinta segundos. Em março, a Lívia contava cerca de 2.400
por dia fora da janela.

O painel novo busca a lista a cada dez segundos — o intervalo caiu de
trinta para dez na semana de 27 de abril, depois de o Neto medir que o
servidor aguentava — e redesenha só quando algo mudou. Um status marcado
leva, no pior caso, dez segundos de espera mais o tempo do pedido. Na
contagem da Lívia na primeira semana de maio, a média foi de onze
segundos, e o pior caso do dia, vinte e três.

Às 16h de 6 de maio, o Renato mandou uma mensagem para o grupo com a foto
da renovação assinada e o texto "slide novo?". O Rafael respondeu com um
polegar. Ninguém fez o slide.

:::milestone
Fim do livro. Você escreveu JavaScript do primeiro `console.log` a um
painel que a operação aceita comparar com o papel: tipos que não se
convertem sozinhos, dinheiro em centavos, decisões que não dependem da
ordem das linhas, funções pequenas tiradas de uma grande sem reescrevê-la,
cópias que não alteram o original, promessas que não chegam fora de
ordem, closures que lembram a entrega certa, uma tela que lê de um lugar
só, módulos numa direção, um teste que falhou antes de passar, um
contrato escrito com o servidor, um commit que responde, e um deploy numa
segunda às 14h. O papel foi dobrado às 5h44.
:::

:::summary
- A pasta `borba` tem arquivos pequenos, importações numa direção, e
  nenhuma dependência além do Node.
- `npm ci`, `npm test` e `npm start` dão o mesmo resultado na máquina e no
  servidor.
- As regras vieram de `entrega.js`, uma por vez, conferidas. O painel
  antigo não foi apagado.
- A conferência final é a da Lívia: três entregas que já deram errado, o
  papel e a tela, linha por linha.
:::

:::exercise level=1
Acrescente à `conferencia.js` uma quarta entrega: urgente, Ribeirão Preto,
12 kg, a caminho. Escreva a linha do papel e confira que bate.

:::answer
O frete: base de Ribeirão, 1.290, mais sete quilos a 90 centavos, 630,
mais 1.000 de urgência: 2.920. No papel:

```text
E-6204 | Ribeirão Preto | a caminho | R$ 29,20
```

No sistema antigo, a entrega precisa do campo de urgência, e a chamada ao
frete passa a repassá-lo:

```javascript
{ codigo: "E-6204", situacao: "EM ROTA",
  municipio: "RIBEIRÃO PRETO", peso: 12, urgente: true },
```

```javascript
const frete = calcularFrete({
  cidade: e.cidade, pesoKg: a.peso, urgente: a.urgente,
});
```

A cidade sai certa porque o `doSistemaAntigo` da pasta já usa a
`nomeDeCidade` do exercício do capítulo @cap:arrays-e-objetos. Com a regra
da primeira versão — só a primeira letra maiúscula —, a linha diria
"Ribeirão preto", e a conferência mostraria `DIFERENTE` antes de o papel
mostrar.
:::

:::exercise level=2
A Lívia pede que o painel mostre, ao lado de cada entrega, há quanto tempo
o status foi marcado — "há 3 min". Diga em que arquivo cada parte mora, e
qual cuidado do capítulo @cap:performance essa mudança exige.

:::answer
O horário da marcação vem do servidor, e entra no estado com a entrega:
`estado.js` e a tradução na porta, em `situacoes.js`, se o sistema antigo
mandar o campo com outro nome.

O texto "há 3 min" é desenho: uma função pura em `desenho.js`, que recebe o
horário da marcação e o horário de agora e devolve o texto.

O cuidado: o texto muda com o tempo, sem a entrega mudar. Se ele for
atualizado redesenhando a lista a cada segundo, volta o tablet quente. A
lista é redesenhada quando as entregas mudam; o "há quanto tempo" é
atualizado junto com o relógio, uma vez por minuto — que é a precisão que
"há 3 min" tem —, mexendo só nesse texto de cada linha.
:::

:::exercise level=3
O próximo pedido é seu. A Mercado Leste quer receber, por e-mail, às 18h,
a lista das entregas do dia com o status final de cada uma. A Cláudia
escreveu o ticket numa linha: "mandar o relatório às 18h".

Faça o pedido inteiro, sozinho, na pasta `borba`. Antes de escrever
código, responda por escrito, no primeiro commit:

1. Quais regras do painel o relatório reaproveita, e de qual arquivo?
2. O que acontece com uma entrega cancelada às 17h59? E com uma marcada às
   18h01?
3. O que o relatório faz se o servidor de e-mail falhar às 18h?
4. Qual teste falha primeiro, e o que ele afirma?
5. Em que dia e horário isso sobe?

:::answer
Não há uma resposta única. Uma solução que acerta costuma ter isto:

**Reaproveita** a situação de `situacoes.js`, o frete e a formatação de
`frete.js`, e a lista do estado. Nada é reescrito: se o relatório calcular
o frete de outro jeito, a Mercado Leste recebe às 18h um número diferente
do que viu na tela às 17h.

**O corte das 18h** é uma regra que ninguém escreveu, e é a primeira
pergunta à Lívia: o relatório é "o estado às 18h00" ou "as entregas do dia,
com o status final"? A resposta muda o código, e vai no comentário acima
da função, com a data.

**A falha do e-mail** não pode ser o `catch` que some do capítulo
@cap:callbacks: o envio é tentado de novo, um número limitado de vezes — a
closure do limitador do capítulo @cap:closures —, e, se não sair, alguém
na Borba fica sabendo antes de a Mercado Leste perguntar.

**O primeiro teste** é o da borda: uma entrega cancelada às 17h59 aparece
cancelada; uma marcada às 18h01, com o status de antes. Visto falhando.

**Sobe** numa segunda ou terça, às 14h, com `npm test` verde no servidor e
a Lívia avisada — e o primeiro relatório conferido por ela, contra o
papel, antes de ir para a Mercado Leste.

Se a sua solução não perguntou nada à Lívia, vale voltar ao item 2. As
regras que mais custaram neste livro foram as que ninguém tinha escrito
porque ninguém tinha perguntado.
:::
