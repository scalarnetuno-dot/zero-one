---
title: "Migrations"
number: 16
slug: migrations
part: p4
kicker: "O banco de produção tinha uma coluna que o schema.rb não tinha. Alguém a criou à mão em 2023, direto no servidor, numa sexta."
goal: >-
  Mudar uma tabela com histórico em vez de mão: escrever uma migration,
  rodá-la e desfazê-la, entender o que o schema.rb é e o que ele não é, e
  preencher os 212 contratos sem status sem apagar nenhuma das três datas.
---

:::story A coluna que não existia
Na segunda, 6 de abril, a Lívia rodou no console de produção — só
leitura, com o Caio do lado — a mesma consulta que tinha rodado em casa:

```text
nortea(prod)> Contract.column_names.size
=> 24
```

Em casa eram vinte e três.

— Vinte e quatro — disse ela.

O Caio pediu a lista e comparou com o `schema.rb`. A diferença era uma
coluna: `site_code`.

O Sérgio ouviu o nome e fechou os olhos um segundo.

— Novembro de 2023. O relatório de medição da construtora precisava do
código do canteiro. Eu criei direto no banco, com o SQL, numa sexta. Era
para ser uma migration na segunda.

— E na segunda?

— Na segunda, o relatório estava funcionando.
:::

## O que uma migration é

A tabela `contracts` não nasceu com vinte e três colunas. Ganhou uma de
cada vez, em dez anos. Cada mudança é um arquivo em `db/migrate`, com data
no nome:

```text
db/migrate/
  20160314101500_create_contracts.rb
  20190508143000_add_begin_date_to_contracts.rb
  20211119170200_add_started_at_to_contracts.rb
  ...
```

Uma migration é uma classe Ruby que descreve **uma** mudança no banco:

```ruby title="db/migrate/20211119170200_add_started_at_to_contracts.rb"
class AddStartedAtToContracts < ActiveRecord::Migration[7.2]
  def change
    add_column :contracts, :started_at, :datetime
  end
end
```

`add_column` acrescenta a coluna `started_at`, do tipo `datetime`, à tabela
`contracts`. O `[7.2]` diz com qual versão das regras de migration ela foi
escrita — o Sérgio a atualizou na migração para o Rails 7.2; a original
dizia `[6.1]`.

O número no começo do nome é a data e a hora em que o arquivo foi criado.
É por ele que as migrations rodam em ordem.

:::term Migration
Um arquivo em `db/migrate` que descreve uma mudança no banco, com data no
nome. Rodadas em ordem, as migrations constroem o banco do zero; cada
ambiente guarda quais já rodou.

A migration é o histórico. O banco é o resultado.
:::

## Rodar, e onde o banco guarda o que já rodou

```text
$ bin/rails db:migrate
== 20260406150000 AddCommentsToContractDates: migrating =======
-- change_column_comment(:contracts, :start_date, ...)
== 20260406150000 AddCommentsToContractDates: migrated (0.0123s)
```

O Rails olha a tabela `schema_migrations`, que existe em todo banco
gerenciado por ele. Ela tem uma coluna só, com o número de cada migration
que já rodou naquele banco. `db:migrate` roda as que não estão lá, em
ordem, e acrescenta o número de cada uma.

```text
$ bin/rails db:migrate:status
 Status   Migration ID    Migration Name
--------------------------------------------------
   up     20160314101500  Create contracts
   up     20211119170200  Add started at to contracts
   up     20260406150000  Add comments to contract dates
```

`up` é rodada. `down` seria uma que existe no arquivo e não rodou naquele
banco.

## O `schema.rb` é gerado

Depois de cada `db:migrate`, o Rails **reescreve** o `db/schema.rb` a
partir do banco. O arquivo que o capítulo @cap:modelos leu não é escrito
por ninguém: é a fotografia do banco de quem rodou a última migration.

Por isso ele mentiu desde novembro de 2023. O `site_code` foi criado com
SQL direto no banco de produção. Nenhuma migration o descreve. Nenhum
banco de desenvolvimento o tem. O `schema.rb`, gerado sempre de um banco
de desenvolvimento, nunca o mostrou.

O sistema funcionou dois anos e meio assim, porque só o relatório de
medição, que só roda em produção, lia a coluna. Qualquer teste desse
relatório falharia em qualquer máquina — e não havia teste dele.

:::key
O banco de produção só muda por migration. Mudança à mão, "só esta vez",
faz o `schema.rb` e o banco divergirem calados, e o próximo ambiente
criado do zero — o de teste, a máquina nova, o servidor de reserva — sai
sem ela.
:::

A correção do `site_code` é uma migration que descreve o que já existe em
produção:

```ruby title="db/migrate/20260406140000_add_site_code_to_contracts.rb"
class AddSiteCodeToContracts < ActiveRecord::Migration[7.2]
  def change
    add_column :contracts, :site_code, :string,
               if_not_exists: true
  end
end
```

`if_not_exists: true` faz a migration não quebrar no banco onde a coluna
já está. Em produção, ela só registra o número em `schema_migrations`. Nos
outros bancos, cria a coluna. Depois dela, os dois lados contam a mesma
história.

## `change`, `up` e `down`

Uma migration pode ser desfeita:

```text
$ bin/rails db:rollback
```

`rollback` desfaz a última. Para `add_column`, o Rails sabe o inverso:
`remove_column`. Por isso o método se chama `change`: você escreve a ida, e
ele deduz a volta.

Nem toda mudança tem volta dedutível. Quando não tem, a migration escreve
os dois sentidos:

```ruby
def up
  execute "UPDATE contracts SET status = 'closed' WHERE ..."
end

def down
  raise ActiveRecord::IrreversibleMigration
end
```

`up` é a ida; `down`, a volta. Um `UPDATE` que sobrescreve valores não tem
volta — o valor antigo não foi guardado —, e o `down` que levanta
`IrreversibleMigration` diz isso em vez de fingir.

:::pitfall
Uma migration que já rodou em produção **não se edita**. O banco de
produção já tem o número dela em `schema_migrations` e não vai rodá-la de
novo. Editar o arquivo muda o que os bancos novos recebem e não muda o de
produção: é o `site_code` de novo, pelo outro lado. Corrigir uma migration
aplicada é escrever outra.
:::

## Os 212 sem status

O capítulo @cap:blocos-e-enumerables deixou uma promessa: os 212
contratos da importação de 2019 com `status` nulo seriam resolvidos quando
o livro chegasse às tabelas. A Helena conferiu a lista no papel e deu a
regra:

- devolvido (`returned_at` preenchido): encerrado;
- sem devolução e com fim já passado: encerrado, e ela confere um por um;
- sem devolução e com fim no futuro: ativo.

A migration de dados:

```ruby title="db/migrate/20260406160000_backfill_contract_status.rb"
class BackfillContractStatus < ActiveRecord::Migration[7.2]
  def up
    execute <<~SQL
      UPDATE contracts SET status = 'closed'
      WHERE status IS NULL
        AND (returned_at IS NOT NULL OR end_date < CURRENT_DATE)
    SQL

    execute <<~SQL
      UPDATE contracts SET status = 'active'
      WHERE status IS NULL AND end_date >= CURRENT_DATE
    SQL
  end

  def down
    raise ActiveRecord::IrreversibleMigration
  end
end
```

`<<~SQL ... SQL` é um *heredoc*: um texto de várias linhas, que termina na
palavra escolhida. O `~` tira o recuo comum das linhas.

A migration usa SQL e não `Contract.where(...).update_all(...)`. O model
muda com o tempo; a migration não. Uma migration de dados que usa o model
pode quebrar daqui a dois anos, quando alguém rodar todas do zero e o
model já tiver outra forma.

Depois dela, e só depois, a coluna passa a exigir valor:

```ruby title="db/migrate/20260406170000_require_contract_status.rb"
class RequireContractStatus < ActiveRecord::Migration[7.2]
  def change
    change_column_default :contracts, :status,
                          from: nil, to: "active"
    change_column_null :contracts, :status, false
  end
end
```

`change_column_null ... false` faz o banco recusar status nulo. Se ela
rodasse antes da de dados, falharia: o banco não aceita a regra enquanto
houver 212 linhas que a violam. As duas migrations estão na ordem do que o
banco consegue aceitar.

## As três datas ficam

A migration que a Lívia escreveu primeiro, naquela segunda, foi a menor:

```ruby title="db/migrate/20260406150000_add_comments_to_contract_dates.rb"
class AddCommentsToContractDates < ActiveRecord::Migration[7.2]
  def change
    change_column_comment :contracts, :start_date,
      from: nil, to: "primeiro dia cobrado (faturamento)"
    change_column_comment :contracts, :begin_date,
      from: nil, to: "assinatura, início da vigência (jurídico)"
    change_column_comment :contracts, :started_at,
      from: nil, to: "saída do pátio (ocupação)"
  end
end
```

O comentário vai para o banco e aparece no `schema.rb`. Nenhuma coluna foi
apagada nem renomeada. Esconder uma delas sem migrar os dados de quem a lê
é exatamente como a multa de R$ 1.800 nasce: o relatório de alguém passa a
ler outra coisa, sem erro.

:::summary
- Migration é uma classe em `db/migrate`, com data no nome, que descreve uma
  mudança. `db:migrate` roda as pendentes; `schema_migrations` guarda as
  rodadas.
- O `schema.rb` é gerado do banco. Mudança à mão no banco faz os dois
  divergirem.
- `change` deduz a volta; `up` e `down` escrevem os dois sentidos.
  `IrreversibleMigration` diz que não há volta.
- Migration aplicada não se edita. Corrige-se com outra.
- Migration de dados usa SQL, não o model, e roda antes da que exige o dado.
:::

:::exercise level=1
Escreva a migration que acrescenta à tabela `equipment` a coluna
`last_inspection_on`, do tipo `date`. Diga o que `db:rollback` faria logo
depois de rodá-la.

:::answer
```ruby
class AddLastInspectionOnToEquipment < ActiveRecord::Migration[7.2]
  def change
    add_column :equipment, :last_inspection_on, :date
  end
end
```

O `rollback` remove a coluna: o inverso de `add_column`, que o Rails deduz
do `change`. Se já houvesse dados nela, eles iriam junto.
:::

:::exercise level=2
O Diego rodou as migrations do zero num banco novo e a
`BackfillContractStatus` não fez nada. Por quê, e isso é um problema?

:::answer
Num banco novo, a tabela `contracts` está vazia quando a migration roda.
Os dois `UPDATE` não encontram linhas com `status` nulo e não alteram
nada.

Não é um problema. A migration de dados existe para os bancos que já têm
os 212 contratos — produção e homologação. Num banco novo, ela é inócua, e
a seguinte, que exige o status, passa. É por isso que ela usa SQL: rodar
do zero não pode quebrar por causa de um model que mudou.
:::

:::exercise level=3
O Sérgio quer "limpar" o `site_code`, agora que ele tem migration: apagar a
coluna e passar o relatório de medição a ler o `site`. Escreva a ordem dos
passos, com o que vai em cada deploy, para que o relatório nunca leia uma
coluna que não existe.

:::answer
Primeiro deploy: o relatório passa a ler `site` — ou, se `site` e
`site_code` não guardam a mesma coisa, uma migration de dados preenche o
que falta antes. A coluna `site_code` continua lá, sem ninguém lendo.

Entre os dois: conferir que nada mais lê `site_code`. A busca no
repositório, a busca pelo pedaço do nome, e a pergunta à Serra Azul — o
relatório de medição vai para ela — se alguém importa a planilha pelo
nome da coluna.

Segundo deploy, dias depois: a migration com `remove_column`.

Se as duas coisas forem no mesmo deploy, há um intervalo em que o código
antigo ainda está rodando e a coluna já não existe. E se o relatório tiver
um leitor fora do repositório, ele quebra no dia do segundo deploy, e não
no primeiro — com a coluna ainda recuperável por um `rollback`.
:::
