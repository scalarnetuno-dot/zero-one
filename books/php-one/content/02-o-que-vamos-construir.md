---
title: "O que vamos construir"
number: 1
slug: o-que-vamos-construir
part: p1
kicker: "Onze caixas num slide, e ninguém na sala capaz de dizer o que o sistema faz hoje."
epigraph: "Eu não sabia como parar. Eu não tinha ideia de como escrever uma linguagem de programação. Eu só fui acrescentando o próximo passo lógico no caminho."
epigraph_by: "Rasmus Lerdorf, criador do PHP"
goal: >-
  Saber o que é uma API REST, por que a Casa Amarela precisa de uma, qual a
  diferença entre livro e exemplar — e ter PHP, Composer e editor instalados
  e testados.
---

:::story A Jornada de Modernização 360°
O Dr. Aurélio projetou o slide às 9h04 de uma terça. Eram onze caixas
ligadas por setas, e no meio estava escrito **CORE**.

— É simples — disse ele. — A gente moderniza o core, expõe via API,
plugga o mobile, e escala.

Dedé levantou a mão.

— O que o core faz hoje?

Silêncio de uns três segundos, que numa reunião de doze pessoas é bastante
tempo.

— Ele... processa — disse Cléber.

— Processa o quê?

Márcia olhou para o Dr. Aurélio. O Dr. Aurélio olhou para o slide.

— O Nonato sabe — disse Márcia.

— O Nonato está de férias.

— Ele volta dia 28.

A reunião durou mais cinquenta minutos e produziu três decisões
arquiteturais sobre um sistema que ninguém presente conseguia descrever.
:::

Às sete da noite daquela mesma terça, Dedé passou na biblioteca do bairro
para devolver um livro atrasado.

:::story A segunda reunião do dia
— Você mexe com computador, né? — perguntou a Vera, sem levantar os olhos da
etiqueta.

— Mexo.

— O Sistema tá ruim.

— Ruim como?

Ela apontou para o monitor. Uma tela cinza, com um formulário de dezoito
campos, três deles chamados `obs`, `obs2` e `obs_nova`.

— Quando duas pessoas emprestam ao mesmo tempo, some um. Quando eu imprimo o
relatório de atrasados, ele trava. E quando alguém devolve no domingo, ele
cobra multa, porque domingo a gente nem abre.

Dedé demorou a responder, porque acabara de perceber uma coisa
desconfortável: em quarenta segundos, a Vera tinha descrito o
comportamento do sistema dela com mais precisão do que doze pessoas tinham
conseguido descrever o da Vertexo em uma hora.

— Quanto vocês podem pagar?

— Nada.

— Eu topo.
:::

## A pergunta que trava o projeto

A reunião da manhã não foi um caso de incompetência. Aconteceu o que
acontece em empresa grande: o sistema é antigo, quem o escreveu saiu, quem
o mantém está de férias, e a pressão por um roadmap chega antes do
entendimento.

O resultado é sempre o mesmo — decisões arquiteturais tomadas sobre uma
caixa escrita **CORE**.

Este livro faz o contrário, e por isso o projeto é uma biblioteca de bairro:
é pequena o bastante para você conseguir manter o sistema inteiro na cabeça,
e real o bastante para ter regras que discordam entre si.

:::note Na sua carreira
"O que esse sistema faz hoje?" é a pergunta mais barata e mais impopular de
qualquer projeto de modernização. Ela costuma travar a reunião — e travar a
reunião é exatamente o serviço que ela presta.

Quando você for quem faz a pergunta, faça-a pedindo um exemplo concreto, não
uma definição: *"me mostra uma coisa que um usuário faz nesse sistema, do
começo ao fim"*. Definição todo mundo improvisa. Exemplo, não.
:::

## Três programas, um acervo

Uma **API** é um contrato entre dois programas: um sabe fazer alguma coisa,
o outro precisa que ela seja feita, e existe um jeito combinado de pedir.

A Casa Amarela precisa de uma por um motivo concreto — são três programas
querendo o mesmo dado:

| Quem | O que precisa |
|---|---|
| O painel da Vera | cadastrar, emprestar, devolver |
| O aplicativo do leitor | consultar acervo, ver os próprios empréstimos |
| O totem da entrada | buscar um título, ver se há exemplar livre |

Tabela: Três telas, um acervo. Sem uma API, cada uma conversa com o banco do
seu jeito — e a regra de empréstimo passa a existir em três versões que
divergem em três velocidades diferentes.

O **REST** é o estilo de combinar que este livro usa. Ele diz que cada coisa
que o sistema conhece — um livro, um exemplar, um empréstimo — é um
**recurso** com um endereço, e que o verbo da requisição diz o que fazer com
ele.

:::anatomy title="Uma requisição HTTP, por partes"
lang: http
code: |
  POST /emprestimos HTTP/1.1
  Content-Type: application/json
  Authorization: Bearer 3|kT9x...

  {"exemplar_id": 812, "leitor_id": 47}
notes:
  - { line: 1, text: "**Verbo**: a intenção. `POST` cria, `GET` lê, `PUT` substitui, `DELETE` apaga." }
  - { line: 1, text: "**Caminho**: o recurso. Substantivo no plural, sem verbo dentro." }
  - { line: 2, text: "**Cabeçalho**: metadado — formato, autenticação, idioma." }
  - { line: 3, text: "O token diz quem está pedindo. Mais adiante, ele também vai decidir o que essa pessoa pode fazer." }
  - { line: 5, text: "**Corpo**: os dados. Só existe em `POST`, `PUT` e `PATCH`." }
:::

Repare no caminho: `/emprestimos`, e não `/criarEmprestimo`. O verbo já está
do lado de fora. Um dos erros mais comuns de API iniciante é colocar o verbo
no endereço e acabar com `/criarEmprestimo`, `/renovarEmprestimo` e
`/devolverEmprestimo` — três endereços para um recurso só, e nenhum deles
combinável com nada.

E toda resposta traz um número de três dígitos que resume o destino da
requisição:

| Faixa | Significado | Os que você vai usar |
|---|---|---|
| `2xx` | deu certo | `200`, `201`, `204` |
| `4xx` | quem pediu errou | `401`, `403`, `404`, `409`, `422` |
| `5xx` | quem respondeu errou | `500` — e o objetivo é nunca |

Tabela: O código de status é a primeira coisa que outro programa lê. Errar
nele é mentir para quem confia em você.

## Primeiro contato

```text
$ php -v
PHP 8.3.14 (cli) (built: Nov 21 2026 09:42:15) (NTS)
Copyright (c) The PHP Group
Zend Engine v4.3.14, Copyright (c) Zend Technologies
```

Se aparecer `8.3` ou mais alto, está pronto.

| Sistema | Como instalar |
|---|---|
| Ubuntu / Debian | PPA `ondrej/php`, depois `apt install php8.3-cli` |
| macOS | `brew install php` |
| Windows | `windows.php.net/download`, ou WSL2 com Ubuntu |

Tabela: No Windows, o WSL2 poupa dor de cabeça a partir do capítulo
@cap:banco-de-dados-e-sql — tudo fica mais parecido com o servidor.

Depois, o Composer:

```text
$ composer --version
Composer version 2.8.4 2026-10-30 12:18:44
```

Ele entra quando o projeto ganhar dependências. Instalar agora evita
interromper o ritmo quando isso acontecer.

:::practice
Rode `php -m`. A lista que aparece são as extensões compiladas no seu PHP.
Procure por `mbstring`, `pdo_mysql`, `intl` e `json` — as quatro vão fazer
falta. Descobrir que faltam agora custa cinco minutos; descobrir no capítulo
@cap:strings custa uma tarde.
:::

## A coluna que confundia tudo

Na quarta-feira, Dedé abriu o banco do Sistema para entender a modelagem.
Havia uma tabela `livros`, e dentro dela uma coluna:

```text
mysql> DESCRIBE livros;
+-------------+--------------+
| Field       | Type         |
+-------------+--------------+
| id          | int          |
| titulo      | varchar(255) |
| autor       | varchar(255) |
| quantidade  | int          |
+-------------+--------------+
```

Emprestar, no Sistema, era `quantidade = quantidade - 1`. Devolver era
`+ 1`.

Funciona. Funcionou por quinze anos.

Aí Dedé perguntou para a Vera cinco coisas:

> Qual exemplar do *O Cortiço* está com a Dona Marlene?
>
> Qual deles está rasgado?
>
> Qual sumiu em 2017?
>
> Qual foi doado e qual foi comprado?
>
> Se um exemplar for perdido, a quantidade cai — mas cai de quê?

A resposta para todas foi a mesma: o Sistema não sabe.

## O que a coluna não consegue contar

Duas frases que parecem iguais e não são:

> "A biblioteca tem *O Cortiço*."
>
> "A biblioteca tem três *O Cortiço*."

A primeira fala do **livro**: título, autor, ISBN, assunto. Existe um só, e
ele não pode ser emprestado — ninguém empresta um ISBN.

A segunda fala do **exemplar**: o objeto físico, com número de tombo, estado
de conservação e uma etiqueta colada na lombada. É ele que sai pela porta.

A coluna `quantidade` é o que sobra quando alguém funde os dois conceitos em
um. Ela guarda a **contagem** e joga fora a **identidade**, e identidade é
justamente o que todas as cinco perguntas da Vera pediam.

:::key
Toda modelagem tem um par de conceitos que parece um só até você tentar
responder uma pergunta específica. Aqui é livro e exemplar; num e-commerce é
produto e item de estoque; numa escola é disciplina e turma. Descobrir esse
par cedo é a diferença entre um sistema que cresce e um que precisa ser
reescrito.
:::

E há um terceiro conceito, que no Sistema não existia em lugar nenhum: o
**empréstimo**. Ele não é uma coluna — é um fato que aconteceu. Tal exemplar
saiu com tal leitor, em tal data, para voltar em tal outra.

## Um domínio que aguenta perguntas

:::diagram type="er" caption="O domínio da Casa Amarela: o acervo à esquerda, o movimento à direita."
columns: 2
entities:
  - name: "Livro"
    fields: ["id (PK)", "titulo", "isbn", "assunto"]
  - name: "Exemplar"
    fields: ["id (PK)", "livro_id (FK)", "tombo", "status"]
  - name: "Leitor"
    fields: ["id (PK)", "nome", "documento"]
  - name: "Emprestimo"
    fields: ["id (PK)", "exemplar_id (FK)", "leitor_id (FK)", "retirado_em", "devolver_ate"]
relations:
  - { from: "Livro", to: "Exemplar", label: "1:N" }
  - { from: "Leitor", to: "Emprestimo", label: "1:N" }
:::

Quatro tabelas no lugar de uma coluna. Em troca, as cinco perguntas da Vera
viram consultas de uma linha. Mais importante: a estrutura responde às
perguntas sem inventar uma coluna nova para cada exceção.

A `quantidade` deixa de ser guardada e passa a ser **calculada**: contar os
exemplares com status disponível. Isso parece mais trabalho e é menos, por
um motivo que vale guardar: **dado calculado não pode divergir da
realidade**. A coluna `quantidade` do Sistema estava errada em quatorze
livros quando o Dedé conferiu, e ninguém sabia desde quando.

## Da bancada à biblioteca

:::diagram type="blocks" caption="A linguagem inteira antes do framework, e o framework depois do problema."
rows:
  - [{ text: "PHP", note: "tipos, funções, arrays, strings" }]
  - [{ text: "Projeto", note: "Composer, autoload, classes" }]
  - [{ text: "HTTP", note: "requisição, REST, um framework à mão" }]
  - [{ text: "Laravel", note: "rotas, controllers, respostas" }]
  - [{ text: "Dados", note: "SQL, migrations, Eloquent" }]
  - [{ text: "Produção", note: "segurança, filas, testes, deploy" }]
:::

Repare na terceira faixa. Antes de instalar o Laravel, você vai construir um
front controller, um roteador e uma pequena pilha de middleware. O framework
vai chegar depois que essas peças deixarem de parecer mágicas.

:::summary
- Ninguém constrói bem o que não consegue descrever — peça um exemplo, não
  uma definição.
- Uma API é um contrato; REST trata cada coisa como recurso com endereço.
- O verbo mora no HTTP, não no caminho.
- O código de status é a primeira coisa que outro programa lê.
- Livro e exemplar são conceitos diferentes, e fundi-los custa uma
  reescrita.
- Empréstimo é um fato com data, não uma coluna.
- Dado calculado não diverge da realidade; dado guardado, sim.
:::

:::milestone
Ambiente instalado e conferido, domínio entendido. A partir do próximo
capítulo, tudo que aparecer no livro roda na sua máquina.
:::

:::exercise level=1
Rode `php -r "echo PHP_VERSION;"` e descubra o caminho do seu `php.ini`.
Anote os dois — você vai precisar no capítulo @cap:primeiro-programa.

:::answer
```text
$ php -r "echo PHP_VERSION;"
8.3.14

$ php -i | grep "Loaded Configuration"
Loaded Configuration File => /etc/php/8.3/cli/php.ini
```
O `-r` roda código direto da linha de comando, sem arquivo e sem `<?php`. É
o jeito mais rápido de tirar uma dúvida pequena, e vai aparecer bastante no
livro.
:::

:::exercise level=2
Escreva o verbo e o caminho de cada operação do acervo: listar livros,
buscar um, cadastrar, alterar, remover. Depois acrescente as três operações
de empréstimo.

:::answer
```text
GET    /livros            lista
GET    /livros/12         busca um
POST   /livros            cadastra
PUT    /livros/12         substitui
DELETE /livros/12         remove

POST   /emprestimos                  empresta
POST   /emprestimos/7/renovacao      renova
POST   /emprestimos/7/devolucao      devolve
```
As três últimas mostram um limite do REST que o capítulo
@cap:o-que-e-uma-api-rest trata com calma: renovar e devolver não são CRUD.
A saída mais usada é tratar a **ação** como um subrecurso, com `POST`.
:::

:::exercise level=3
Vera quer um relatório de "livros mais emprestados". Um livro tem vários
exemplares. Se o relatório contar empréstimos por exemplar, ele responde a
mesma pergunta? Justifique.

:::answer
Não responde, e a diferença é exatamente a deste capítulo.

Contar por **exemplar** responde "qual cópia saiu mais vezes", que é uma
pergunta de conservação: o exemplar mais emprestado é o que vai rasgar
primeiro, e é o que precisa de encadernação.

Contar por **livro** — somando os empréstimos de todos os exemplares daquele
título — responde "o que as pessoas querem ler", que é uma pergunta de
aquisição: é o que a Casa Amarela usa para decidir o que comprar com a verba
do semestre.

As duas são legítimas e servem a decisões diferentes. O erro não é escolher
uma; é entregar uma achando que entregou a outra — e isso acontece com
frequência desconfortável, porque o nome do relatório costuma ser o mesmo
nos dois casos.

E há um terceiro dado escondido aí, que o capítulo @cap:relacionamentos vai
tornar fácil de obter: o título mais **procurado** não é o mais emprestado.
É o que mais aparece em reserva porque nunca tem exemplar livre — e esse
número não está em nenhuma das duas contagens. Se a Casa Amarela comprar
pelo ranking de empréstimos, vai comprar mais cópias do que já circula bem,
e nenhuma do que ninguém consegue pegar.
:::

:::story A piada final
Na quinta, o Dr. Aurélio parou na mesa do Dedé.

— Soube que você está fazendo um sistema pra uma biblioteca.

— De graça, fora do horário.

— Que legal. — Ele pensou um instante. — Escala pra quantos usuários?

— Mil e duzentos. Do bairro.

— Hmm. — Uma pausa. — Já pensou em arquitetura de microsserviços?

Dedé pensou em dizer que a biblioteca tem quatro tabelas e um computador.
Disse só que ia avaliar.

No caderno da Tainá, naquele dia, entrou a primeira frase de uma lista que
ia crescer o livro inteiro: *"perguntar o tamanho antes de escolher a
ferramenta"*.
:::
