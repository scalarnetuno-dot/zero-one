---
title: "O primeiro programa"
number: 3
slug: primeiro-programa
part: p1
kicker: "Dois Nodes na mesma manhã, e só um deles pode atender o cais."
goal: >-
  Escrever, salvar e rodar um programa JavaScript no Node; escrever texto
  com crase; prender um nome com const e reatribuir com let; ler as três
  falhas que aparecem na primeira hora.
---

:::story Qual máquina?
A Bia abriu o terminal na pasta dela.

```text
$ node --version
v24.9.0
```

No servidor, a mesma pergunta respondia 20.

— Aqui está rodando — disse ela.

O Neto apareceu na porta. Ninguém tinha chamado.

— Qual máquina?

— A minha.

— E a do servidor?

O Rafael, sem levantar os olhos:

— Vinte. Até 30 de abril.

O Neto olhou para o número na tela dela.

— Não mexe no vinte. O da manhã depende dele. O seu fica do lado, e antes
de rodar qualquer coisa você descobre qual dos dois o terminal está
chamando.
:::

Rodar JavaScript parece a parte mais simples do trabalho, e é onde se perde
a manhã: o `node` que responde no terminal quase nunca é o único da
máquina. O programa desta página roda no seu, o 24. O painel de produção
continua no 20, e ninguém desta página vai publicá-lo hoje.

O menor programa útil tem uma linha. Salve isto num arquivo chamado
`status.js`, dentro da pasta `borba`:

```javascript title="status.js" numbered
console.log("Entrega E-4821: a caminho");
```

Abra o terminal nessa pasta e rode:

```text
$ node status.js
Entrega E-4821: a caminho
```

`console.log` escreve o valor no terminal e pula para a linha seguinte. O
que está entre aspas é texto, e o texto sai do jeito que foi escrito. O
ponto e vírgula encerra a instrução. Você vai ver arquivo da Borba sem ele:
os dois costumam rodar. Este livro escreve o ponto e vírgula para o fim da
instrução ficar visível.

O Node leu o arquivo, executou a linha e terminou. Não há um segundo
comando para "compilar" antes. A compilação existe, dentro do motor, e você
não a dispara.

:::term V8
O motor, escrito pelo Google, que executa o JavaScript dentro do Chrome e
dentro do Node. `node status.js` entrega o seu arquivo a esse motor, mais
às peças de arquivo e terminal que o Node acrescenta.

A versão do motor no seu Node 24 não é a versão do motor no Node 20 do
servidor. O arquivo desta página cabe nas duas.
:::

:::diagram type="flowchart" caption="Do arquivo à linha no terminal. Você dispara um comando. A compilação fica dentro do motor."
nodes:
  - { id: src, type: io, text: "status.js" }
  - { id: node, type: process, text: "node status.js" }
  - { id: v8, type: process, text: "V8 executa" }
  - { id: out, type: io, text: "Entrega E-4821: a caminho" }
edges:
  - { from: src, to: node }
  - { from: node, to: v8 }
  - { from: v8, to: out }
:::

## O mesmo texto, no navegador

O painel da Lívia não roda com `node status.js`. Roda no navegador, que tem
o próprio motor. O Chrome usa o V8. O Firefox usa outro, o SpiderMonkey. A
linguagem é a mesma; o programa ao redor, não.

Abra o navegador, aperte F12 e escolha o painel **Console**. F12 abre as
ferramentas de desenvolvedor: o lugar em que o navegador mostra o que a
página está fazendo. No console, digite a mesma chamada e confirme com
Enter:

```javascript
console.log("Entrega E-4821: a caminho");
```

A linha aparece de novo. Você não salvou arquivo. O console executa o que
você digita e esquece quando a aba fecha. Serve para perguntar. Não serve
para ser o programa.

:::term Console do navegador
Uma linha de comando dentro das ferramentas de desenvolvedor. Executa
JavaScript na página que está aberta.

Uma página em branco não é o painel da Borba. O que você digitou aqui é
seu. Não consultou entrega nenhuma no servidor.
:::

Quando o programa precisa ficar, o caminho é arquivo salvo e `node`. O
console volta quando a pergunta for sobre uma página.

## Um nome para a situação

O código da entrega e a situação estão cravados no texto. No dia em que a
situação mudar, você edita a frase inteira e reza para não errar o trecho
que era fixo. Um nome separa as duas coisas.

```javascript title="status.js" numbered
const codigo = "E-4821";
const situacao = "a caminho";

console.log(`Entrega ${codigo}: ${situacao}`);
```

```text
$ node status.js
Entrega E-4821: a caminho
```

A saída é a mesma. O arquivo, não. `codigo` e `situacao` são nomes presos
a textos. A linha do `console.log` usa crase, não aspas. Entre crases, o
que está em `${ }` é lido como código, e o resultado entra no texto.

:::anatomy title="As partes de um texto com crase"
lang: javascript
code: |
  console.log(`Entrega ${codigo}: ${situacao}`);
notes:
  - { line: 1, text: "A crase liga a interpolação. Com aspas, `${codigo}` sairia escrito assim, com o cifrão." }
  - { line: 1, text: "`${codigo}` troca o nome pelo valor. Dentro das chaves vale uma expressão." }
  - { line: 1, text: "O que está fora das chaves é texto fixo, inclusive os dois-pontos e o espaço." }
:::

:::term const
Cria um nome e o prende a um valor. Prender quer dizer que o nome não
aceita outra atribuição em seguida.

`situacao = "entregue"` na linha de baixo falha. O valor `"a caminho"`
continua sendo o valor daquele nome até o programa terminar.
:::

A falha, gravada no Node v24.9.0, começa assim. O número das linhas
internas muda de uma versão para outra; o tipo da falha, não.

```text
troca.js:2
situacao = "entregue";
         ^

TypeError: Assignment to constant variable.
```

`TypeError` é o tipo. `Assignment to constant variable` é o motivo:
atribuição a variável constante. O cursor `^` está no `=`, que é o ponto
em que o nome recusou o valor novo. A linha `troca.js:2` diz arquivo e
número da linha.

Quando o nome precisa mudar de valor, o jeito é `let`.

```javascript title="anda.js" numbered
let situacao = "a caminho";
situacao = "entregue";
console.log(situacao);
```

```text
$ node anda.js
entregue
```

:::term let
Cria um nome que aceita outra atribuição. A segunda linha aponta `situacao`
para outro texto. A primeira ligação deixa de valer.

Use `let` quando o valor muda. No resto, `const`. Um nome que não muda é
mais fácil de ler às 5h40 do que um nome que talvez mude.
:::

## Três falhas da primeira hora

As mensagens abaixo foram gravadas no Node v24.9.0. Está só o começo de
cada uma: arquivo, cursor e tipo. Debaixo disso o Node imprime o caminho
interno até a sua linha. Esse caminho repete de uma falha para outra. A
parte que muda, e a que se lê primeiro, é a de cima.

**O arquivo não está onde você chamou.**

```text
Error: Cannot find module 'D:\borba\status.js'
  code: 'MODULE_NOT_FOUND'
```

`MODULE_NOT_FOUND` quer dizer que o Node procurou um arquivo e não achou.
O caminho é o lugar em que ele procurou. Quase sempre o terminal está em
outra pasta, ou o arquivo se chama `status.js.txt` porque o editor
acrescentou a extensão por conta própria. Confira com o nome que está na
pasta, não com o nome que você lembra de ter digitado.

A palavra `module`, na mensagem, é o nome interno: o Node procura o seu
arquivo como se procura um módulo. O caminho ao lado é o lugar em que ele
procurou. A linha de cima basta para achar o problema.

**Faltou fechar.**

```javascript title="quebra.js" numbered
console.log("Entrega E-4821: a caminho"
```

```text
quebra.js:1
console.log("Entrega E-4821: a caminho"
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^

SyntaxError: missing ) after argument list
```

`SyntaxError` é texto que nem chegou a rodar: a gramática não fecha.
`missing ) after argument list` aponta o parêntese que falta. O cursor
cobre o argumento porque foi ali que o Node desistiu de esperar o `)`.
Falta também o ponto e vírgula, e o erro não fala nele. Ele para no
primeiro furo.

**O nome não existe.**

```javascript title="nome.js" numbered
console.log(situacao);
```

```text
nome.js:1
console.log(situacao)
            ^

ReferenceError: situacao is not defined
```

`ReferenceError` é um nome usado sem ter sido criado. `situacao` não foi
escrito com `const` nem com `let` neste arquivo. O console do navegador
às vezes ainda tem um nome deixado por uma digitação anterior. O `node
nome.js` começa do zero toda vez. Se o nome não está no arquivo, ele não
existe.

:::pitfall
Aspas e crase não são intercambiáveis. `"Entrega ${codigo}"` imprime o
cifrão e as chaves. A interpolação só liga com crase.

E o nome dentro de `${ }` precisa existir. `${situacao}` com `situacao`
nunca criado é o mesmo `ReferenceError`, só que no meio da frase.
:::

## Comentário

Tem linha que o programa não deve executar, e que uma pessoa precisa ler.

```javascript title="status.js" numbered
// situação como o motorista marcou, não como a tela gostaria
const situacao = "a caminho";
console.log(situacao);
```

Tudo depois de `//`, na mesma linha, é comentário. O Node ignora. O
comentário não explica o que a linha já diz. Explica o que a linha não
consegue carregar: de onde vem o valor, ou por que ele não é outro.

O comentário no fim de `entrega.js`, `// NÃO MEXER. FUNCIONA.`, é desse
gênero. Não descreve a função. Descreve uma decisão de março de 2024: não
mexer. O medo que justificava a decisão não está na linha.

:::summary
- `node status.js` lê o arquivo, executa e termina. A compilação fica
  dentro do V8.
- Texto entre crases interpola o que estiver em `${ }`. Aspas não
  interpolam.
- `const` prende o nome. `let` deixa reatribuir. Reatribuir `const` é
  `TypeError`.
- Arquivo ausente, parêntese faltando e nome inexistente são três falhas
  diferentes: `MODULE_NOT_FOUND`, `SyntaxError`, `ReferenceError`.
:::

:::exercise level=1
Na pasta `borba`, altere `status.js` para a saída sair exatamente assim:

```text
Entrega E-4821: a caminho (Ribeirão Preto)
```

A cidade deve ser um `const`, não um pedaço cravado na frase.

:::answer
```javascript title="status.js"
const codigo = "E-4821";
const situacao = "a caminho";
const cidade = "Ribeirão Preto";

console.log(`Entrega ${codigo}: ${situacao} (${cidade})`);
```

```text
$ node status.js
Entrega E-4821: a caminho (Ribeirão Preto)
```

Os parênteses em volta de `${cidade}` estão fora das chaves. Por isso
saem na impressão como texto, em volta do nome da cidade.
:::

:::exercise level=2
O arquivo abaixo vai falhar. Diga o tipo da falha e a linha, sem rodar.
Depois rode e confira.

```javascript title="status.js"
const codigo = "E-4821"
console.log(`Entrega ${codigo}: ${situacao}`);
```

:::answer
`ReferenceError` na linha 2. `codigo` existe. `situacao` não foi criado.

A falta do ponto e vírgula na linha 1 não é o que quebra. O Node aceita a
instrução mesmo assim e segue. O nome ausente é o primeiro furo de verdade.
:::

:::exercise level=3
A Bia precisa que `situacao` comece em `"a caminho"` e passe a `"entregue"`
antes do `console.log`. Ela escreveu as duas atribuições com `const` e
recebeu `TypeError`. Mostre o arquivo que imprime `entregue`, e diga por
que a primeira linha não pode continuar sendo `const`.

:::answer
```javascript title="anda.js"
let situacao = "a caminho";
situacao = "entregue";
console.log(situacao);
```

`const` recusa a segunda atribuição. O nome precisa nascer com `let` para
a linha seguinte poder apontá-lo a outro texto. Se a situação não mudasse
dentro do arquivo, `const` seria o certo — e o `TypeError` estaria
protegendo essa decisão.
:::
