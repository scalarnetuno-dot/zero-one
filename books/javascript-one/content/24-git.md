---
title: "Git"
number: 24
slug: git
part: p8
kicker: "Quinta, 17h43. A Bia escreveu ajustes na mensagem do commit. O Rafael leu por cima do ombro e puxou uma cadeira."
goal: >-
  Escrever uma mensagem de commit que responde o que mudou e por quê seis
  meses depois, dizer ao Git o que não entra no repositório, e concluir um
  merge em que os dois lados mexeram na mesma função sem apagar o lado do
  outro.
---

:::story Você escreve no commit
Quinta, 23 de abril, 17h43. A Bia terminou a mudança do relógio e digitou:

```text
$ git commit -m "ajustes"
```

O Rafael, que estava de saída com a mochila no ombro, leu a tela por cima
do ombro dela. Pôs a mochila no chão e puxou uma cadeira.

— O que você mudou?

— O relógio. Ele redesenhava a lista inteira a cada segundo. Separei o
redesenho por região e pus a comparação da lista.

— Por quê?

— Porque o tablet da Lívia travava. Tem o ticket.

— E daqui a seis meses, alguém lê `ajustes` no histórico. O que essa
pessoa sabe?

— Que eu ajustei alguma coisa.

— O ticket pode ter sido apagado quando trocarem o sistema de ticket. Você
pode estar de férias. Eu posso ser a pessoa que precisa saber por que a
lista não redesenha quando o relógio muda, e desfazer isso achando que é
defeito.

— Eu explico na reunião.

— Não tem reunião daqui a seis meses. Você escreve no commit.
:::

## O que o histórico guarda

O capítulo @cap:o-que-vamos-construir leu o histórico do painel e achou
três mensagens: `cliente http`, `ajustes`, `troca axios por fetch`. A
segunda é do Diego, de março de 2024, e é o commit que deixou no fim de
`entrega.js` o comentário que pede para não mexer.

Dois anos depois, ninguém sabe por quê. A mensagem não diz. O Diego
responde WhatsApp devagar. O comentário continua lá, e cada pessoa que
chega ao arquivo o obedece sem saber o que ele protege.

O Git guarda, para sempre, **o que** mudou: o `git diff` de qualquer
commit mostra cada linha. O que ele não consegue guardar sozinho é **por
quê**. Esse é o trabalho da mensagem.

:::term Commit
Um registro no histórico: um conjunto de mudanças, com autor, data e uma
mensagem. O Git guarda o que mudou. A mensagem guarda o motivo, e é a
única parte que alguém escreve.

`git log` mostra as mensagens. `git show <código>` mostra a mensagem e as
linhas que mudaram.
:::

## Uma mensagem que responde

A mensagem tem duas partes: uma primeira linha curta, e, depois de uma
linha em branco, o corpo.

```text
lista: redesenha só a região que mudou

O relógio do canto chamava desenhar() a cada segundo, e desenhar()
refazia os 160 cartões da lista. No tablet do cais, cada redesenho
levava ~40 ms, e o toque em "cancelar" caía no meio.

Agora cada mudança chama só o desenho das regiões que dependem dela:
o relógio redesenha o relógio; a lista só é refeita quando as
entregas mudam, e não é refeita se a atualização do servidor vier
igual à que está na tela.

Medido no tablet, 60 s aberto: de 9.600 cartões criados para 160.

Ticket 1862.
```

**A primeira linha** diz o que mudou, em até uns cinquenta caracteres, no
imperativo ou como fato. É o que aparece em `git log --oneline`, e o que
alguém lê procurando uma mudança entre cem. `lista:` na frente diz em que
parte do painel.

**O corpo** diz por quê: o que estava errado, o que a mudança faz, como
foi conferido. Linhas de até uns setenta caracteres, porque o terminal não
quebra linha em mensagem de commit.

**O ticket** vai no fim, como referência. Não como a explicação: o ticket
pode sumir, a mensagem não.

Com mensagem de várias linhas, o `-m` não serve. `git commit` sem `-m`
abre o editor configurado, e a mensagem se escreve lá, com as linhas em
branco no lugar certo.

A Bia não reescreveu o `ajustes` com um commit novo por cima. Ele ainda
não tinha saído da máquina dela, e o Git permite corrigir o último:

```text
$ git commit --amend
```

`--amend` abre o editor com a mensagem do último commit, e troca-a pela
nova. Só vale para o que ainda não foi enviado ao repositório
compartilhado: depois do `push`, o commit é de todo mundo, e reescrevê-lo
muda o histórico de quem já o baixou.

:::key
A mensagem de commit responde, seis meses depois, a pergunta que ninguém
vai estar lá para responder: **por que isto está assim?** O que mudou, o
Git já mostra. O porquê só existe se alguém escrever — e o momento de
escrever é agora, com o motivo ainda na cabeça.
:::

## O que não entra

A pasta `borba` tem coisas que não são o projeto: `node_modules/`, que o
capítulo @cap:npm recria a partir do lockfile; arquivos de configuração do
editor; o `.env` com o endereço do servidor de homologação. O arquivo
`.gitignore` diz ao Git para não olhar para eles:

```text title=".gitignore"
node_modules/
.env
.DS_Store
*.log
```

Cada linha é um padrão. Uma pasta termina em `/`; `*.log` é qualquer
arquivo terminado em `.log`. O `package-lock.json` **não** está na lista:
ele vai para o repositório.

O `.env` guarda o endereço e, em produção, a chave de acesso ao servidor.
Uma chave que entra num commit fica no histórico mesmo depois de o arquivo
ser apagado no commit seguinte — o capítulo de deploy volta a isso.

## Ramo e merge

A Bia e o Rafael trabalham ao mesmo tempo. Cada um num **ramo**: uma linha
de commits separada, que depois é juntada à principal.

```text
$ git switch -c rafael
```

O Rafael, no ramo dele, tornou explícita a base de Ribeirão Preto — que
até então era o valor padrão, e fazia uma cidade desconhecida pagar o
frete de Ribeirão, como o exercício do capítulo @cap:funcoes mostrou. A
Bia, no ramo principal, mudou a base de São Carlos, a pedido da Cláudia.
As duas mudanças caíram na mesma função, em linhas vizinhas.

```text
$ git merge rafael
Auto-merging frete.js
CONFLICT (content): Merge conflict in frete.js
Automatic merge failed; fix conflicts and then commit the result.
```

O Git junta sozinho tudo o que não se sobrepõe. Onde os dois lados
mudaram o mesmo trecho, ele para e marca o arquivo:

```javascript title="frete.js (em conflito)"
export function calcularFrete({ cidade, pesoKg, urgente = false }) {
  let base = 1290;
  if (cidade === "Franca") base = 1890;
<<<<<<< HEAD
  if (cidade === "São Carlos") base = 2290;
=======
  if (cidade === "São Carlos") base = 2150;
  if (cidade === "Ribeirão Preto") base = 1290;
>>>>>>> rafael
  const extra = pesoKg > 5 ? Math.round((pesoKg - 5) * 90) : 0;
  return base + extra + (urgente ? 1000 : 0);
}
```

Entre `<<<<<<< HEAD` e `=======`, a versão do ramo em que a Bia está — a
dela. Entre `=======` e `>>>>>>> rafael`, a versão do ramo que chegou. O
arquivo, assim, não roda: as marcas são texto no meio do código.

Resolver é **editar o arquivo** até ele dizer o que os dois quiseram:

```javascript title="frete.js (resolvido)"
export function calcularFrete({ cidade, pesoKg, urgente = false }) {
  let base = 1290;
  if (cidade === "Franca") base = 1890;
  if (cidade === "São Carlos") base = 2290;
  if (cidade === "Ribeirão Preto") base = 1290;
  const extra = pesoKg > 5 ? Math.round((pesoKg - 5) * 90) : 0;
  return base + extra + (urgente ? 1000 : 0);
}
```

A base nova de São Carlos, da Bia, e a linha de Ribeirão, do Rafael. A
linha antiga de São Carlos, `2150`, sai: foi ela que as duas versões
disputavam, e a da Bia a substituía de propósito.

```text
$ npm test
$ git add frete.js
$ git commit
```

O teste antes do `add`: um conflito resolvido à mão é código novo, escrito
por quem resolveu, e que nenhum dos dois autores viu. O `commit` sem `-m`
abre o editor com uma mensagem pronta, `Merge branch 'rafael'`, e espaço
para dizer como o conflito foi resolvido.

:::pitfall
O jeito mais rápido de "resolver" um conflito é apagar um dos dois lados
inteiro — geralmente o do outro. O arquivo volta a rodar, os testes do
seu lado passam, e a mudança do Rafael some sem ninguém ter decidido
isso. Antes de apagar um lado, leia o que ele fazia. Se não souber, a
pessoa que o escreveu está a uma mensagem de distância.
:::

:::summary
- O Git guarda o que mudou. A mensagem guarda o porquê — a única parte que
  alguém escreve.
- Primeira linha curta, com o que mudou; linha em branco; corpo com o
  motivo, o efeito e a conferência. O ticket no fim, como referência.
- `git commit --amend` corrige o último commit, só antes do `push`.
- `.gitignore` tira do repositório o que não é projeto: `node_modules/`,
  `.env`. O lockfile fica.
- Conflito é o Git parando onde os dois lados mudaram o mesmo trecho.
  Resolve-se editando até o arquivo dizer o que os dois quiseram, com o
  teste antes do commit.
:::

:::exercise level=1
Reescreva estas mensagens do histórico do painel como uma primeira linha
que diz o que mudou. Invente o mínimo necessário e diga o que você teria
de perguntar para escrever o corpo.

1. `ajustes`
2. `fix`
3. `troca axios por fetch`

:::answer
1. Sem ler o diff, não dá. Com o diff do commit de março de 2024 —
   Axios entrando em `entrega.js` e o comentário no fim —: `entrega:
   busca de status passa a usar Axios`. A pergunta para o corpo é a que
   ninguém fez ao Diego: o que quebrava antes, para ele pôr o comentário.
2. Com o diff do 1847: `lista: canceladas visíveis em tela estreita`. O
   corpo diz que a regra de 2023 as escondia abaixo de 900 px, e que o
   tablet do cais tinha 890.
3. `entrega, lista: busca de entregas passa a usar fetch`. O corpo, se
   fosse honesto, diria o que a mensagem de 2025 não disse: que o Axios e
   a pasta `http/` continuavam em uso em outros lugares.

A terceira mostra que uma mensagem pode ser verdadeira e ainda enganar: a
intenção — trocar — não foi o que aconteceu.
:::

:::exercise level=2
A Bia commitou o `.env` sem querer e fez `push`. No commit seguinte, apagou
o arquivo e o pôs no `.gitignore`. Diga o que ainda está exposto e o que
precisa ser feito.

:::answer
O `.env` continua no histórico, no commit em que entrou. Qualquer pessoa
com acesso ao repositório vê o conteúdo com `git show` daquele commit. O
`.gitignore` só impede que ele entre de novo.

Se o arquivo tinha uma chave de acesso, a chave está vazada: precisa ser
trocada — gerar outra, no servidor, e invalidar a antiga. Apagar o
arquivo do histórico é possível, com ferramentas próprias, e não desfaz o
vazamento: quem baixou o repositório antes já tem a cópia.

A ordem é: trocar a chave primeiro. Limpar o histórico, se for o caso,
depois.
:::

:::exercise level=3
O Marcos propõe que, para evitar conflitos, cada pessoa trabalhe num
arquivo diferente e ninguém mexa no arquivo do outro. Responda.

:::answer
Evita o conflito do Git e não evita o conflito de verdade. A Bia e o
Rafael mexeram na mesma função porque as duas mudanças eram sobre a mesma
regra: o frete por cidade. Em arquivos separados, cada um teria escrito a
sua versão da regra, e o painel teria duas tabelas de frete que não se
conhecem — o defeito dos três clientes HTTP, com outro assunto.

O conflito do Git é o momento em que duas pessoas descobrem que mexeram na
mesma coisa. É barato: aparece na máquina de quem juntou, com as duas
versões lado a lado. O que o reduz não é separar arquivos; é ramos curtos,
que duram um ou dois dias, e juntados com frequência, para que as duas
versões nunca se afastem muito.
:::
