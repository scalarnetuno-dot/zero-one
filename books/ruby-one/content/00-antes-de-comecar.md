---
title: "Antes de começar"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Três colunas para o começo de um contrato, uma planilha que ainda manda no pátio, e uma multa de R$ 1.800 por dia quando a tela mente."
---

Esta é a pasta do sistema da Nortea, no ar desde março de 2016:

```text
nortea/
  Gemfile
  Gemfile.lock
  app/models/contract.rb
  app/models/equipment.rb
  app/controllers/contracts_controller.rb
  app/views/contracts/
  db/schema.rb
  spec/factories/contracts.rb
```

O `Gemfile` lista as bibliotecas do projeto e as versões. Uma delas é o
Rails, o framework em que esse sistema foi escrito. O `Gemfile.lock`
grava a versão exata que foi instalada, para o servidor e a máquina de
alguém não "atualizarem" sozinhos no meio do caminho.

O `schema.rb` é o arquivo em que o Rails descreve as tabelas. A tabela
`contracts` tem vinte e três colunas. Três delas guardam um começo:

```text
start_date
begin_date
started_at
```

Uma coluna é um campo da tabela. Três campos para a mesma pergunta — quando
o contrato começa — significa que o sistema respondeu essa pergunta três
vezes, e não apagou as respostas antigas.

E funciona.

Cerca de quatrocentas e trinta máquinas, o pátio carregando às 6h. A Helena
confere a tela. O Seu Nestor confere a planilha `patio_SEMANAL.xlsx`.
Quando as duas discordam, o caminhão sai pela planilha. No último
trimestre a Nortea pagou cerca de R$ 46 mil de multa porque uma máquina
contratada não estava no canteiro. A cláusula cobra R$ 1.800 por dia.

Você vai escrever o módulo de contratos que merece ser comparado com essa
planilha. A pasta de produção fica onde está.

## A Nortea e a data

A **Nortea Equipamentos**, em Betim, aluga máquina para construtora:
betoneira, gerador, plataforma elevatória, compactador. A **Construtora
Serra Azul**, em Belo Horizonte, nove canteiros, renova o contrato em
**quarta-feira, 3 de junho**. São R$ 3,6 milhões por ano.

O adendo, que o comercial já assinou, pede uma página em que a Serra Azul
veja qual equipamento está preso a qual contrato. Hoje essa resposta sai
por telefone, ou pela planilha.

## Quem aparece

**Lívia** entrou na Nortea em 2 de março. O acesso ao repositório chegou na
sexta, dia 6. É boa tecnicamente. A convenção da casa ela ainda está
lendo.

**Caio** escreve Ruby há anos. Já viu o `contract.rb`. Fala baixo, e às
vezes não fala.

**Renato** é o tech lead. Quer o código simples. Simples, para ele, é o
que a Marta consegue conferir sem uma aula.

**Marta** é a product manager. Conhece o contrato e o pátio. Abstração que
não muda a manhã da Helena ela devolve.

**Diego** é o QA. O caso que ele traz é uma combinação: cancelar no meio da
reserva, devolver antes de sair, equipamento sem responsável.

**Sérgio** mantém pedaços do sistema de 2016. Solução temporária, na mão
dele, dura.

**Helena Noronha** toca a operação. Não escreve Ruby. Sabe em qual canteiro
está cada plataforma.

**Seu Nestor** fundou a Nortea. Está no pátio às 6h. A planilha é o sistema
em que ele confia.

**Rômulo** fechou o adendo de 3 de junho. Aparece quando a data que ele
assinou precisa virar tela.

E o **Rails de 2016**, com três começos na mesma tabela, é o sistema em
produção. Cada coisa nova vai ser medida contra ele e contra a planilha.

## Como o código aparece

Código aparece assim, às vezes com o nome do arquivo:

```ruby title="contrato.rb"
codigo = "CT-2041"
puts "Contrato #{codigo}"
```

Um nome em minúscula, com `=`, guarda um valor. `puts` escreve esse valor
no terminal e pula a linha. Dentro de aspas duplas, `#{codigo}` é trocado
pelo valor do nome. Fora das chaves, o texto sai como foi escrito.

O que o terminal responde aparece sem nome de arquivo e sem realce:

```text
Contrato CT-2041
```

Quando o programa quebra, a primeira linha diz o arquivo, a linha e o tipo
da falha. É essa que se lê primeiro.

:::key
Comando de terminal aparece com `$` na frente. O `$` representa o prompt e
não faz parte do comando: não digite.
:::

Você não precisa instalar nada para começar a ler. Quando o primeiro
programa precisar rodar, a instalação vem junto.

A data que ninguém pode empurrar é 3 de junho. Até lá, o pátio carrega às
6h, e o caminhão sai pela planilha quando a tela discorda.
