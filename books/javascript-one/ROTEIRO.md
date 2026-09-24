# JavaScript One — roteiro editorial

**Volume 4 da coleção Zero One.** 26 capítulos numerados em 8 partes, mais
a abertura. O miolo segue o mesmo contrato dos outros volumes: Markdown com
front matter, blocos `:::`, referência cruzada só por `@cap:<slug>`, e
capítulo listado em `book.yaml` mesmo quando o arquivo ainda não existe.

A logística é o **cenário**. O enredo é decisão de desenvolvimento: código,
bug, arquitetura, Git, deploy, teste, e a linguagem no meio disso. A entrega
existe para o software ter onde errar. Ninguém abre um capítulo para aprender
roteirização, frete ou pátio de caminhão.

## O que já está escrito

| Arquivo | Estado |
|---|---|
| `00-antes-de-comecar.md` | escrito |
| `01-o-javascript-que-voce-ouviu-falar.md` | escrito. Título: "Do Mocha ao Node". História documentada, em ordem. Sem o molde fama / defeito / o que melhorou |
| `02-o-que-vamos-construir.md` | escrito. A cena das três bibliotecas mora aqui |
| `03-primeiro-programa.md` | escrito |
| `04` a `26` | escritos, seguindo a régua abaixo |

Os quatro primeiros foram conferidos com `python -m pipeline check javascript-one`.
Os exemplos de Node do capítulo 3 foram rodados no Node v24.9.0. Os dos
capítulos 4 a 26 também: saídas, erros, os tempos do capítulo 13, o teste
vermelho e verde do 21, o `422` do servidor mínimo do 22 e o conflito de
merge do 24. O `Object.groupBy` do 25 foi rodado no Node 20 (falha) e no
24. A diferença de serialização do Axios (0.21.1 × 1.x) do 20 foi medida
com os dois instalados.

Decisões tomadas na escrita:

- Calendário: 04 é terça, 17/03; 17 (o 1847) é quarta, 08/04; 24 (o
  `ajustes`) é quinta, 23/04, 17h43; 25 é sexta, 24/04, 16h52; o servidor
  sobe para o Node 24 na segunda, 27/04; 26 é quarta, 06/05.
- Frete: base 1290 (Ribeirão), 1890 (Franca), 2150 → 2290 (São Carlos, a
  partir do merge do 24); 90 centavos por kg acima de 5; urgência 1000.
- Contrato de status com o servidor: `SEPARADA`, `EM_ROTA`, `ENTREGUE`,
  `CANCELADA`; `422` para valor inválido, `409` para entrega cancelada.
- O painel novo atualiza a cada 10 s a partir da semana de 27/04.

## O mundo

**Estúdio Calha**, Ribeirão Preto, dezenove pessoas. Casa de software que
herda sistema quando quem escreveu foi embora.

**Borba Entregas**, mesma cidade, operação também em Franca e São Carlos.
Cento e sessenta motoristas. Entrega no mesmo dia. Fundada pelo **Seu Aldo**,
que ainda fica no cais às 5h40. Quem toca a operação é a filha, **Lívia
Borba**.

O software em produção é o **painel**: uma página que a Lívia abre de manhã
e um servidor em **Node 20**. No ar desde março de 2022. Escrito pelo
**Diego Pacheco**, então na Calha, num fim de semana que virou quatro anos.
Diego saiu em novembro de 2024. Responde WhatsApp devagar. Não é vilão: o
painel despachou caminhão esse tempo todo.

Às **5h35** a Lívia imprime a lista do dia. Se o papel e o painel discordam,
o caminhão sai pelo papel. O Seu Aldo acredita no papel. O livro inteiro é a
tentativa de fazer o painel merecer o contrário, sem anunciar isso.

### O contrato que põe data nas decisões

A **Mercado Leste**, onze lojas, renova o contrato com a Borba na
**quarta-feira, 6 de maio de 2026**. O fornecimento vale **R$ 2,1 milhões**
por ano. A cláusula nova: cada status de entrega precisa aparecer no painel
em até **30 segundos** depois da marcação do motorista. Atraso custa
**R$ 3,50** por status. A Lívia contou o buraco atual em cerca de **2.400
por dia**, o que dá **R$ 8.400 por dia** e passa de **R$ 180 mil** num mês.

A Calha assinou **R$ 96 mil** fechados para o painel aguentar essa cláusula.
Cerca de um terço já virou hora de reunião antes da segunda-feira em que a
Bia abre o repositório. Se a cláusula estiver de pé em 6 de maio, começa a
mensalidade de **R$ 14 mil**. Se não estiver, a Borba paga a multa e a
mensalidade não começa.

| O livro precisa de | O arranjo entrega |
|---|---|
| prazo com data real | 6 de maio de 2026, uma quarta-feira |
| dinheiro | a multa da Borba e os R$ 14 mil por mês da Calha |
| alguém que cobra | a Lívia toda manhã; a Cláudia todo dia; o Renato quando lembra do slide |
| algo em produção | o painel, no ar desde 2022, e o Node 20 do servidor |

O Node 20 deixa de receber correção em **30 de abril de 2026**, seis dias
antes da renovação. A máquina de quem lê o livro instala **Node 24**, linha
LTS com suporte até 30 de abril de 2028. O 22 também roda os exemplos
(suporte até 30 de abril de 2027). O 26, em setembro de 2026, ainda é
Current: não é a linha deste livro.

A história abre na **segunda-feira, 16 de março de 2026, 8h17**. A Bia
recebeu acesso na sexta, 13 de março.

### O repositório

Nome interno: `painel`. Não é um produto com marca. É a pasta.

```text
painel/
  package.json          axios 0.21.1, anotado e parado
  index.html
  lista.js              fetch, no commit do Marcos de agosto de 2025
  lista.css             o bug da janela estreita mora aqui
  entrega.js            processarEntrega, 187 linhas; Axios e também fetch
  http/
    client.js           o cliente escrito à mão em março de 2022
```

Três jeitos de fazer a mesma pergunta HTTP:

1. a pasta `http/`, commit do Diego em 14 de março de 2022, mensagem
   `cliente http`;
2. o Axios dentro de `entrega.js`, no commit de 18 de março de 2024,
   mensagem `ajustes`, o mesmo commit do comentário
   `// NÃO MEXER. FUNCIONA.`;
3. `fetch` em `lista.js` e em `entrega.js`, commit do Marcos em 12 de
   agosto de 2025, mensagem `troca axios por fetch`. A troca não removeu
   os outros dois.

O leitor **não clona esse repositório**. Ele cria, no capítulo 3, uma pasta
`borba/` na própria máquina e faz crescer ali o painel novo. O de produção
aparece em trechos, quando um defeito precisa ser visto. Estado verificável
ao fim de cada capítulo escrito: arquivos, comando, saída.

### Convenção do código novo

Aspas duplas, ponto e vírgula, `const` por padrão, `let` quando o nome
precisa ser reatribuído, recuo de dois espaços. `var` só aparece quando o
arquivo antigo está na página, e na hora em que aparece é explicado. Nada de
framework. Nada de TypeScript: o buraco que o TypeScript foi inventado para
fechar é ensinado em JavaScript. Biblioteca só entra quando a falta dela
doer, e a primeira candidata é sobrar uma, não ganhar mais uma.

## O elenco

Competentes na direção que a função deles empurra. Ninguém é o bode.

- **Bia** — júnior. Entrou na Calha no kickoff de 2 de março e recebeu o
  repositório na sexta, dia 13. Lê rápido e faz a pergunta que a sala
  estava evitando. É por onde o leitor entra. Não é ingênua: no fim de
  semana ela leu a pasta. Falta vocabulário, não atenção.
- **Rafael** — sênior pragmático. Sabe que decisão temporária dura três
  anos, e diz isso uma vez, cedo. Explica curto. Aponta para o arquivo em
  vez de fazer discurso.
- **Marcos** — tech lead. Gosta de arquitetura e de desenhar o que ainda
  não existe. A migração pela metade, de Axios para `fetch`, é dele. A
  competência é real e está um andar acima do bug.
- **Cláudia** — PO. Traduz a operação para o time. A tradução perde a
  restrição, porque ela não estava no cais às 5h40. Não é distração: é o
  ofício de transformar a frase da Lívia em ticket.
- **Paulo** — QA. Prazer quase científico pelo caso que o desenvolvedor
  jurou que não acontecia. O bug da janela é dele.
- **Neto** — DevOps. Aparece quando alguém diz que funciona na própria
  máquina. A sexta às 16h52 é a porta dele.
- **Lívia Borba** — operação. Abre o painel às 5h40, imprime às 5h35, e é
  a única pessoa que sabe descrever o que o sistema faz sem usar o verbo
  "processar".
- **Seu Aldo** — cais, papel, uma van em 1998. Quase não fala. Quando o
  papel e a tela discordam, o caminhão obedece a ele.
- **Diego Pacheco** — ausente. Escreveu o painel. O comentário é dele.
- **Renato** — fundador da Calha. Nunca escreveu JavaScript e não finge.
  Volta de palestra com uma caixa nova no slide. Aparece pouco.

## O arco

1. **Capítulos 1–3 — chegar.** A linguagem, o contrato, o primeiro arquivo
   que roda fora do servidor.
2. **Capítulos 4–11 — ler o que já está escrito.** Tipos, conta, decisão,
   repetição, a função de 187 linhas, escopo, os objetos que chegam de
   sistemas diferentes, a mutação que ninguém viu.
3. **Capítulos 12–15 — o tempo.** Callback, promessa, async/await, closure.
   Três operações que terminam fora de ordem.
4. **Capítulos 16–18 — a tela.** DOM, o bug impossível, duas partes da
   interface que discordam.
5. **Capítulos 19–21 — virar projeto.** Módulo, npm, o teste do Paulo.
6. **Capítulos 22–23 — o contrato e o custo.** A API que discorda do
   front, a lista que ficou cara.
7. **Capítulos 24–26 — sair da máquina.** Git, deploy, o projeto final na
   semana do dia 6 de maio.

Operadores, condicionais e repetições não estavam na lista de vinte temas.
Estão no livro porque sem eles a lista não se sustenta: o tema 1 já precisa
de comparação, e uma lista de entregas precisa de um laço. São três
capítulos, não três apostilas.

## Onde entra cada cena já escrita

A cena não é o capítulo. Ela abre o capítulo e cria a dúvida. A aula ocupa
o resto. Nenhuma delas se chama piada, e nenhuma termina com o narrador
dizendo o que significou.

| Cena | Capítulo | O que a aula ensina em seguida |
|---|---|---|
| Segunda, 8h17. Três clientes HTTP. "Descubra." | 02, já escrito | Ler `package.json` e um `git log`. Instalar o Node. |
| A função de 187 linhas e o `// NÃO MEXER. FUNCIONA.` | 08 Funções | Parâmetro, retorno, e separar **uma** responsabilidade com saída visível. O comentário fica. A função não é reescrita inteira nesse dia. |
| A entrega some quando a janela diminui. O ticket falava de cancelar. | 17 Debugging | Reproduzir, DevTools, estilo calculado. O cancelamento era a isca. |
| `git commit -m "ajustes"` às 17h43. | 24 Git | A mensagem que ainda responde daqui a seis meses, com ticket ou sem ticket. |
| Sexta, 16h52. "Quem falou produção?" | 25 Deploy | Por que a sexta àquela hora é uma decisão, e o que tem de ser verdade na segunda. |

## Ganchos que voltam

Plantar cedo, cobrar depois, variar um pouco a cada volta.

1. `// NÃO MEXER. FUNCIONA.` — visível na abertura; a origem é o commit de
   18 de março de 2024; a cobrança é o capítulo de funções, e de novo quando
   alguém tiver uma razão concreta para mexer.
2. Três clientes HTTP — abertura e capítulo 02; a escolha de ficar com um
   é o capítulo de npm, não antes.
3. A mensagem `ajustes` — no histórico, capítulo 02, sem sermão. O sermão
   só cabe quando a Bia escreve a dela, no capítulo de Git.
4. A lista impressa das 5h35 — abertura; volta toda vez que o painel mente.
5. "Temporário dura três anos." — uma fala do Rafael no capítulo 1. O
   painel está com quatro. Não vira bordão de narrador.
6. "Funciona na minha máquina." — capítulo 3, o Neto na porta. Volta no
   deploy, com versão de Node no lugar de opinião.
7. Sexta, 16h52 — só no deploy. Não antecipar.
8. A janela estreita — só no debugging.
9. O número do ticket **1847** — reservado para o bug da janela. Não usar
   como código de entrega.

## Régua de cada capítulo que falta

Um capítulo só fecha quando o leitor executa, explica e altera o exemplo.
Três a cinco assuntos. Ciclo de mostrar, rodar, ver a saída, quebrar, ler
a mensagem, consertar. Referência para frente: nenhuma. Referência para
trás: `@cap:<slug>`, e a frase precisa sobreviver se o número for apagado.

### 04 — Variáveis e tipos (`part: p2`)

- **Mudança:** distinguir os tipos do dia a dia, ler `typeof`, e parar uma
  coerção antes que ela vire regra de negócio.
- **Dor:** uma alteração pequena no status. Em um canto o valor é o número
  `0`; em outro, o texto `"0"`. Uma comparação frouxa trata os dois como a
  mesma coisa. A entrega muda de estado.
- **Evidência:** um script que imprime `typeof` de texto, número, booleano,
  `null` e `undefined`, mostra `"5" + 1` e `"5" - 1`, e quebra de propósito
  na comparação que o painel fazia.
- **Cuidado:** `typeof null` é `"object"`. Explicar na hora, como defeito
  histórico, sem piada em cima. Dinheiro não mora em `number`: um só tipo
  numérico, IEEE-754. `0.1 + 0.2` entra aqui, com a saída real, e o frete
  passa a ser centavos inteiros.

### 05 — Operadores

- **Mudança:** escolher `===`, escrever conta sem colar texto sem querer, e
  ler precedência no trecho em que ela muda o resultado.
- **Dor:** o frete de `"10"` mais `"20"` vira `"1020"` na tela da Lívia.
- **Evidência:** o mesmo cálculo com `+` entre textos, com `Number`, e com
  centavos. Saída das três versões.

### 06 — Condicionais

- **Mudança:** escrever `if` / `else` e um `switch` pequeno só se o status
  for de fato um conjunto fechado; recusar um par de estados impossível.
- **Dor:** a entrega consta como entregue e como cancelada, porque dois
  `if` independentes rodaram.
- **Evidência:** uma função curta que recebe o status e devolve um único
  estado, mais o caso que ela recusa.

### 07 — Repetições

- **Mudança:** percorrer a lista com `for...of`, saber o que `for` clássico
  acrescenta, e ver um `continue` pular a entrega errada.
- **Dor:** a lista impressa tem quatro entregas; o painel mostra três. O
  laço pulou a que tinha cidade vazia.
- **Evidência:** antes e depois, com as quatro linhas impressas.

### 08 — Funções

- **Mudança:** declarar função, passar argumento, devolver valor, e tirar
  **uma** responsabilidade de `processarEntrega` sem "limpar" as outras 180
  linhas.
- **Dor:** a função valida, calcula prazo, muda estado, formata endereço,
  grava log, chama a rede, dispara notificação, mexe na tela e, em algum
  ponto, calcula o frete. O comentário está na última linha.
- **Cena:** a da função, quase como foi escrita. O Rafael deixa separar. A
  separação que cabe neste capítulo é uma função só, com nome e saída.
- **Evidência:** `calcularFrete` (ou o pedaço que estiver mais isolado no
  trecho) rodando com um valor conhecido. O arquivo antigo continua no ar.

### 09 — Escopo

- **Mudança:** prever onde um nome existe, com bloco, função, `let` e
  `const`. Ver o que `var` faz de diferente, porque `entrega.js` tem `var`.
- **Dor:** um nome criado para a entrega do laço continua existindo depois,
  e a notificação usa a entrega errada.
- **Evidência:** o mesmo trecho com `var` e com `let`, duas saídas.

### 10 — Arrays e objetos

- **Mudança:** modelar uma entrega como objeto e a manhã como array; ler
  propriedade; perceber dois formatos para a mesma entrega.
- **Dor:** o aplicativo do motorista manda `status`; o sistema antigo manda
  `situacao`. Os dois estão certos no sistema de origem.
- **Evidência:** uma função que recebe os dois formatos e devolve um objeto
  só, impresso.

### 11 — Desestruturação e spread

- **Mudança:** ler um objeto por desestruturação e copiar com spread sem
  achar que copiou o que está aninhado.
- **Dor:** alguém altera o objeto "só nesta tela" e a lista, que guardava
  o mesmo objeto, muda junto.
- **Evidência:** mutação compartilhada impressa, depois a cópia, e o caso
  raso que a cópia não resolve.

### 12 — Callbacks

- **Mudança:** passar uma função para outra e ler uma cadeia de três
  continuações sem se perder.
- **Dor:** gravar status chama quem notifica, que chama quem atualiza a
  tela. O erro no meio some.
- **Evidência:** três `console.log` com a ordem em que as continuações
  rodam, inclusive quando uma delas falha.

### 13 — Promises

- **Mudança:** criar e consumir uma `Promise`, encadear `then` / `catch`, e
  explicar por que três operações terminam fora da ordem do código.
- **Dor:** o frete, o status e a notificação voltam fora de ordem. A tela
  mostra frete antigo com status novo.
- **Evidência:** log com horários (ou um contador) da versão ingênua e da
  versão com `Promise.all` ou com encadeamento, a que for honesta para o
  caso. Não usar `async` ainda: este capítulo é a forma anterior, de
  propósito.

### 14 — async/await

- **Mudança:** reescrever o fluxo do capítulo anterior com `async` /
  `await` e `try` / `catch`, e apontar o ponto em que o programa espera.
- **Dor:** a mesma três operações, agora legíveis, ainda com um `await`
  esquecido que devolve uma promessa no lugar do frete.
- **Evidência:** a saída igual à versão certa do capítulo 13, e a saída
  errada do `await` faltando.

### 15 — Closures

- **Mudança:** dizer qual variável uma função interna enxerga, e reproduzir
  o bug do laço que prende o último valor.
- **Dor:** cada botão de cancelar cancela a última entrega da lista. Quem
  olha o handler não vê o número errado escrito em lugar nenhum.
- **Evidência:** o laço com `var` imprimindo sempre o último código; o
  mesmo laço com `let`, imprimindo o código de cada volta.

### 16 — DOM e eventos

- **Mudança:** achar um elemento, ler texto, escutar um clique, e evitar
  dois ouvintes no mesmo botão.
- **Dor:** o cancelamento dispara duas vezes. A primeira chamada cancela; a
  segunda opera em cima de uma entrega que já mudou.
- **Evidência:** uma página mínima, aberta no navegador, com o clique
  contado. Um ouvinte: o contador sobe de um. Dois: sobe de dois.

### 17 — Debugging

- **Mudança:** reproduzir um bug antes de explicar, usar o DevTools
  (elementos, estilo calculado, console) e separar causa de sintoma.
- **Dor:** o ticket 1847 diz que a entrega some da lista quando o usuário
  cancela. Ninguém reproduz. O Paulo diminui a janela.
- **Cena:** a do bug impossível.
- **Evidência:** a regra de CSS que esconde o item quando a largura passa
  de um limite e o estado é cancelado. O cancelamento só fornecia o estado.
  A causa é a regra. O conserto é uma linha, mostrada antes e depois.

### 18 — Estado

- **Mudança:** ter um lugar só de onde a tela lê a lista, e renderizar a
  partir dele.
- **Dor:** a lista diz "cancelada" e o detalhe ao lado ainda diz "a
  caminho". Cada pedaço guardou a sua cópia.
- **Evidência:** uma atualização que muda o dado e as duas regiões, contra
  a versão em que só uma muda.

### 19 — Módulos

- **Mudança:** separar arquivo com `export` / `import` em ESM, e
  desfazer uma dependência circular.
- **Dor:** `entrega.js` passa a importar `lista.js`, que já importava
  `entrega.js`. Um dos dois chega vazio.
- **Evidência:** o erro (ou o valor `undefined`) da circularidade, e a
  divisão que deixa um terceiro arquivo com o dado.

### 20 — npm

- **Mudança:** ler `package.json` e o lockfile, instalar de propósito, e
  atualizar uma dependência vendo o que quebra.
- **Dor:** três clientes para a mesma pergunta. Uma atualização do Axios,
  de 0.21 para uma major atual, quebra o único canto que ainda o usa.
- **Evidência:** a suíte mínima (mesmo que seja um script) verde com um
  cliente só. Os outros dois saem do caminho de uma chamada nomeada, não
  de uma faxina geral. O `left-pad` de 22 de março de 2016 cabe como fato
  desta história, não como anedota solta: um pacote de onze linhas saiu do
  registro e um monte de build quebrou.

### 21 — Testes

- **Mudança:** escrever um teste com `node:test` que falha pelo motivo
  certo e passa quando o código muda.
- **Dor:** o Paulo cancela a entrega enquanto a gravação do status ainda
  não voltou. Ninguém tinha imaginado o intervalo.
- **Evidência:** a saída do teste vermelha, depois verde. O caso é o
  intervalo, não um espelho do código feliz.

### 22 — APIs

- **Mudança:** fazer um `fetch`, ler status HTTP, e escrever o contrato
  que os dois lados vão obedecer.
- **Dor:** a página manda `status: "cancelado"`. O servidor aceita
  `"CANCELADA"`. Os dois têm teste verde.
- **Evidência:** a resposta `422` (ou a que o servidor pequeno devolver)
  com o corpo que diz o campo rejeitado, e a chamada ajustada ao contrato
  escrito na página, em tabela curta.

### 23 — Performance

- **Mudança:** medir antes de reescrever, e parar de refazer a lista
  inteira a cada evento que não muda a lista.
- **Dor:** um ouvinte de mouse, ou de relógio, reconstrói cento e sessenta
  cartões. A página responde tarde. A decisão parecia inocente.
- **Evidência:** uma contagem de reconstruções antes e depois. Número, não
  adjetivo.

### 24 — Git

- **Mudança:** escrever mensagem de commit que responde "o que mudou e
  por quê" seis meses depois, e concluir um merge pequeno sem apagar o
  lado do outro.
- **Dor:** a Bia commita `ajustes` às 17h43. O ticket pode deixar de
  existir. Ela pode estar de férias. O Rafael pode ser quem precisa saber.
- **Cena:** a do commit, com a fala dele até "Você escreve no commit."
- **Evidência:** a mensagem reescrita, e um merge em que os dois lados
  mexeram na mesma função curta, resolvido no arquivo.

### 25 — Deploy

- **Mudança:** dizer o que tem de ser igual entre a máquina local e o
  servidor (versão do Node, variável de ambiente, o comando que sobe o
  processo) e recusar um horário.
- **Dor:** funciona na máquina da Bia, em Node 24. No servidor, Node 20,
  uma sintaxe ou uma variável falta. São 16h52 de uma sexta.
- **Cena:** a da sexta. O Neto pergunta quem falou produção. O Rafael fecha
  o notebook: segunda-feira.
- **Evidência:** um checklist de cinco linhas que a segunda de manhã
  consegue cumprir, e a diferença concreta que quebrava o 20.

### 26 — Projeto final

- **Mudança:** juntar lista, status, uma função pequena de frete, um teste
  do caso do Paulo, um commit legível e um jeito de subir que o Neto
  aceitaria numa segunda.
- **Dor:** falta menos de uma semana para 6 de maio. A Lívia vai imprimir
  a lista às 5h35 e comparar com a tela.
- **Evidência:** a pasta `borba/` com comando de subir, comando de teste,
  e três entregas de exemplo em que papel e tela coincidem. O legado não
  é apagado no capítulo: o painel novo cobre a manhã. `entrega.js` antigo
  continua citado como o lugar de onde as regras foram tiradas.

## O que este livro não é

Não é um livro de React, nem de TypeScript, nem de logística. Framework,
fila, banco e autenticação só entram se uma dor do painel ficar sem saída
mais barata. Até o capítulo 26, a saída mais barata é JavaScript, uma página
e um Node pequeno. Se um capítulo futuro precisar de mais do que isso, o
roteiro muda com a dor na mesa, não com um slide.
