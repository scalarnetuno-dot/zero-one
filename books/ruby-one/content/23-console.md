---
title: "Console"
number: 23
slug: console
part: p5
kicker: "Contract.last não era o contrato que a Lívia queria. O update seguinte gravou nele mesmo assim, e o console respondeu true."
goal: >-
  Usar o console do Rails sabendo, linha por linha, o que só lê e o que
  grava; ler o que cada expressão devolve; trabalhar em sandbox; e
  conferir no log o UPDATE que não parecia gravação.
---

:::story Só consulta
Na quarta, 29 de abril, às 17h10, a Helena pediu pelo telefone para
corrigir o responsável do contrato que ela tinha acabado de criar para a
Serra Azul, em Nova Lima. Tinha digitado "Rogerio", sem acento e com o
sobrenome errado.

A Lívia, com o Caio do lado, abriu o console de produção.

```text
nortea(prod)> c = Contract.last
=> #<Contract id: 3197, code: "CT-3197", site: "betim", ...>
```

A Marta estava na mesa ao lado.

— Isso altera alguma coisa?

— Não — disse a Lívia. — Isso é só consulta.

E digitou a linha seguinte:

```text
nortea(prod)> c.update(responsible: "Rogério Tavares")
=> true
```

O Caio pôs a mão no braço da cadeira dela.

— Betim.

A Lívia olhou para o `site` na primeira linha. O contrato da Helena era de
Nova Lima. O `3197` tinha sido criado dois minutos depois, pelo Rômulo,
para outro canteiro.

— A primeira linha era consulta — disse ela, baixo. — A segunda, não.

— A Marta perguntou da segunda — disse o Caio.
:::

## O `irb` com o `nortea` dentro

O capítulo @cap:primeiro-programa apresentou o `irb`: o Ruby esperando uma
linha. O console do Rails é o mesmo `irb`, com o projeto inteiro
carregado — models, banco, configuração:

```text
$ bin/rails console
Loading development environment (Rails 7.2.2)
nortea(dev)>
```

O prompt diz o projeto e o ambiente. `dev` é o banco da sua máquina.
`prod`, o do pátio. É a informação mais importante da tela, e fica à
esquerda de toda linha que você digita.

Cada linha é executada ao apertar Enter, e o console mostra depois de
`=>` o **valor que ela devolveu** — o mesmo `=> nil` do `puts`, lá do
começo. O valor devolvido não diz se a linha mudou alguma coisa. Um
`true` pode ser uma pergunta respondida ou uma gravação feita.

## O que lê e o que grava

Uma linha só lê quando todos os métodos dela só leem.

**Só leem:** `find`, `find_by`, `where`, `first`, `last`, `count`,
`pluck`, os escopos, os atributos (`c.responsible`), os predicados
(`c.occupying?`).

**Gravam:** `save`, `update`, `create`, `destroy`, `delete`, `toggle!`,
`increment!`, `update_column`, `update_all`, `delete_all`, `destroy_all`.

E há os que **não gravam ainda**, e enganam por isso:

```text
nortea(dev)> c.responsible = "Rogério Tavares"
=> "Rogério Tavares"
nortea(dev)> c.changed?
=> true
nortea(dev)> c.reload.responsible
=> "Rogerio"
```

A atribuição muda o objeto na memória. `changed?` confirma que há
mudança não gravada. `reload` busca de novo no banco — e o banco continua
com o valor antigo. Só o `save` levaria a mudança para lá.

| Linha | O banco muda? | O console devolve |
|---|---|---|
| `Contract.last` | não | o contrato |
| `c.responsible = "x"` | não | `"x"` |
| `c.save` | sim | `true` |
| `c.update(responsible: "x")` | sim | `true` |
| `Contract.where(site: "betim").update_all(site: "contagem")` | sim, em todos | quantas linhas mudaram |

Tabela: Três linhas devolvem uma coisa que parece resposta. Duas delas
gravaram.

:::term Console
O `irb` com a aplicação Rails carregada, aberto com `bin/rails console`.
Cada linha roda contra o banco do ambiente do prompt.

O console não pede confirmação. `update` no console de produção é uma
gravação em produção, igual à do formulário, sem a validação de quem olha
a tela.
:::

## O log diz o que a linha fez

O console mostra o SQL de cada linha. É a forma de conferir se uma linha
gravou sem precisar saber de cor a lista de métodos:

```text
nortea(dev)> c = Contract.find_by(code: "CT-3190")
  Contract Load (0.6ms)  SELECT "contracts".* FROM "contracts"
  WHERE "contracts"."code" = $1 LIMIT $2  [["code", "CT-3190"], ...]
nortea(dev)> c.update(responsible: "Rogério Tavares")
  TRANSACTION (0.2ms)  BEGIN
  Contract Update (0.9ms)  UPDATE "contracts" SET "responsible" = $1,
  "updated_at" = $2 WHERE "contracts"."id" = $3
  TRANSACTION (1.4ms)  COMMIT
=> true
```

`SELECT` é leitura. `UPDATE`, `INSERT` e `DELETE` são gravação. `COMMIT` é
o banco confirmando. A palavra que a Marta queria ouvir não era "consulta"
nem "correção": era a que aparece no log.

:::key
Antes de apertar Enter numa linha no console de produção, diga em voz
alta se ela grava. Depois, confira no log: `SELECT` é leitura; `UPDATE`,
`INSERT`, `DELETE` e `COMMIT` são o pátio mudando.
:::

## O registro certo

`Contract.last` devolve o contrato com o maior `id`: o último **criado por
qualquer pessoa**, não o último que você viu. Às 17h10, com três pessoas
cadastrando contrato, "o último" mudou de dono em dois minutos.

No console de produção, o registro se busca pelo que o identifica de
verdade, e com o `!` que falha se não achar:

```text
nortea(prod)> c = Contract.find_by!(code: "CT-3196")
=> #<Contract id: 3196, code: "CT-3196", site: "nova_lima", ...>
nortea(prod)> [c.code, c.site, c.responsible]
=> ["CT-3196", "nova_lima", "Rogerio"]
```

A segunda linha é a conferência: os três campos que dizem que este é o
contrato da Helena, antes de qualquer gravação. `find_by!` levanta
`RecordNotFound` se o código não existir, em vez de devolver `nil` e
deixar o `update` seguinte falhar com `NoMethodError` — ou, pior, a
variável `c` ainda apontar para o contrato da linha anterior.

## Sandbox

O console tem um modo em que nada fica:

```text
$ bin/rails console --sandbox
Loading development environment in sandbox (Rails 7.2.2)
Any modifications you make will be rolled back on exit
nortea(dev)>
```

Tudo que você fizer roda dentro de uma transação que é desfeita quando o
console fecha. Serve para experimentar uma correção antes de aplicá-la:
rodar o `update`, olhar o resultado, sair, e só então abrir o console de
verdade.

:::pitfall
O sandbox desfaz o banco. Não desfaz o que sai dele: um e-mail enviado por
callback, um job agendado, uma chamada à API da Serra Azul. E, enquanto
está aberto, a transação dele pode segurar linhas que o formulário da
Helena precisa gravar. Sandbox em produção, só com o pátio parado.
:::

## O que foi feito com o `3197`

O contrato do Rômulo tinha agora o responsável da Helena. A Lívia não
apagou nem "desfez": não havia um valor anterior guardado em lugar nenhum
além da memória do Rômulo. Ela ligou para ele, que disse o nome certo, e
fez as duas correções com o código na mão:

```text
nortea(prod)> a = Contract.find_by!(code: "CT-3196")
nortea(prod)> [a.site, a.responsible]
=> ["nova_lima", "Rogerio"]
nortea(prod)> a.update!(responsible: "Rogério Tavares")
=> true
nortea(prod)> b = Contract.find_by!(code: "CT-3197")
nortea(prod)> [b.site, b.responsible]
=> ["betim", "Rogério Tavares"]
nortea(prod)> b.update!(responsible: "Juliana Prates")
=> true
```

`update!` em vez de `update`: se a validação recusasse, o console
mostraria a exceção, e não um `false` que passa despercebido numa tela
cheia de linhas.

Na sexta, o Renato pôs uma regra no documento da equipe: correção em
produção pelo console é feita por duas pessoas, com o código do registro,
e a linha que grava é lida em voz alta antes do Enter. A Marta pediu para
ser uma das duas, quando fosse contrato da Serra Azul.

:::milestone
Fim da Parte 5. O pedido chega por uma rota com nome, o controller tem sete
linhas no `create` e o cancelamento tem ação própria, a tela da Helena
pergunta ao model em vez de refazer a regra, e o console é usado sabendo
que linha grava. Falta provar que tudo isso continua funcionando quando
alguém mexer — que é o que a última parte faz.
:::

:::summary
- `bin/rails console` é o `irb` com o projeto carregado. O prompt diz o
  ambiente.
- O `=>` mostra o valor devolvido, não se houve gravação. `update` devolve
  `true` depois de gravar.
- Atribuição muda a memória; `save` e `update` mudam o banco; `reload`
  confere.
- O log diz o que a linha fez: `SELECT` lê; `UPDATE`, `INSERT`, `DELETE`
  gravam.
- `last` é o último criado por qualquer um. Busque pelo código, com
  `find_by!`, e confira antes de gravar. `--sandbox` desfaz o banco, e só
  o banco.
:::

:::exercise level=1
Para cada linha, diga se grava no banco:

```ruby
Contract.where(status: "reserved").count
c.status = "cancelled"
c.cancel_reason
Contract.where(site: "betim").update_all(responsible: nil)
c.toggle!(:billing_day)
```

:::answer
Não, não, não, sim, sim.

O `update_all` grava em todos os contratos de Betim de uma vez, sem
validação e sem callback. O `toggle!` com `!` grava — e aqui nem faz
sentido, porque `billing_day` é um número, não verdadeiro ou falso.
:::

:::exercise level=2
Escreva a sequência de linhas, no console, para corrigir a data de
devolução do contrato `CT-3150` para 15 de maio, com conferência antes e
depois.

:::answer
```ruby
c = Contract.find_by!(code: "CT-3150")
[c.code, c.site, c.equipment.patrimony, c.end_date]
c.update!(end_date: Date.new(2026, 5, 15))
c.reload.end_date
```

A segunda linha confere que é o contrato certo, pelos campos que a Helena
reconheceria. O `update!` falha alto se a validação do período recusar —
um fim antes do início, a mesma máquina em outro contrato. O `reload`
confirma pelo banco, não pela memória.
:::

:::exercise level=3
O Sérgio corrige dados no console de produção há anos e diz que "nunca deu
problema". Proponha uma alternativa ao console para correções que se
repetem — como o responsável digitado errado —, e diga o que ela ganha.

:::answer
Uma ação na tela, para quem tem permissão: editar o responsável de um
contrato pelo formulário, com o mesmo `update` do controller. Ela passa
pelas validações, pelos strong parameters e pelo registro de quem alterou,
e não depende de alguém saber o que `Contract.last` devolve.

Para correções pontuais que não cabem em tela, um script em
`script/`, revisado como qualquer código, rodado com `bin/rails runner`, e
guardado no repositório. Ele ganha histórico: daqui a um ano, quem
perguntar por que o `CT-3197` mudou de responsável acha o commit.

O console continua existindo. Ele fica para o que é realmente único, e com
as duas pessoas que o Renato pediu.
:::
