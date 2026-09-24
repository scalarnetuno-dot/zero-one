---
title: "Callbacks"
number: 19
slug: callbacks
part: p4
kicker: "Um contrato criado gerava duas reservas da mesma máquina. Um callback era de 2016, o outro de 2021, e os dois tinham razão sozinhos."
goal: >-
  Entender o que um callback é e em que ordem o Rails os chama, reproduzir
  a reserva duplicada com um script, corrigi-la observando a mudança certa,
  e saber o que não deve morar num callback.
---

:::story Duas reservas
O Diego mandou o print na quarta, 15 de abril: a agenda de reservas da
PT-140, com a mesma linha duas vezes. Mesmo contrato, mesmo período, dois
`id`.

— Toda vez que alguém cria um contrato — disse ele. — Eu criei três hoje,
em homologação. Seis reservas.

A Lívia procurou `Reservation.create` no `contract.rb`. Duas vezes.

```ruby title="app/models/contract.rb"
after_create :reserve_equipment
after_save :register_reservation
```

— Um de 2016 — disse o Caio, que já tinha o `git blame` aberto. — Outro de
2021.

O Sérgio estava na porta.

— O de 2021 é meu. Quando a Helena passava um contrato de reservado para
ativo, a reserva não aparecia. Eu pus no `after_save` para pegar a
edição.

— E o `after_create`?

— Eu não vi. Estava lá em cima, no meio das associações.
:::

## O que é um callback

Um callback é um método do model que o Rails chama sozinho, num momento
combinado da vida do registro: antes de validar, depois de criar, depois
de salvar, antes de apagar.

```ruby title="app/models/contract.rb" numbered
class Contract < ApplicationRecord
  has_many :reservations

  after_create :reserve_equipment
  after_save :register_reservation

  private

  def reserve_equipment
    reservations.create!(equipment: equipment,
                         starts_on: start_date, ends_on: end_date)
  end

  def register_reservation
    return unless status == "active"

    reservations.create!(equipment: equipment,
                         starts_on: start_date, ends_on: end_date)
  end
end
```

Ninguém chama `reserve_equipment` em lugar nenhum. O `after_create`
registra: "depois de criar um contrato, chame este método". É o mesmo
desenho do bloco entregue a um método, do capítulo
@cap:blocos-e-enumerables — só que quem decide quando chamar é o ciclo de
vida do registro.

:::term Callback
Um método do model registrado para ser chamado pelo Rails num momento da
vida do registro: `before_validation`, `before_save`, `after_create`,
`after_save`, `after_commit`, entre outros.

Quem lê o código que salva não vê o callback. Quem lê o callback não vê
quem salvou.
:::

## A ordem

No `create` de um contrato, o Rails chama, nesta ordem:

```text
before_validation
  (validações)
after_validation
before_save
before_create
  (INSERT no banco)
after_create
after_save
  (COMMIT)
after_commit
```

`after_create` e `after_save` rodam **os dois** num registro novo. Um
registro novo está sendo criado e salvo ao mesmo tempo. Num registro já
existente, editado, roda o `after_save` e não o `after_create`.

| Callback | Roda ao criar | Roda ao editar |
|---|---|---|
| `after_create` | sim | não |
| `after_update` | não | sim |
| `after_save` | sim | sim |

Tabela: `after_save` não é "depois de editar". É "depois de qualquer
gravação", e a criação é uma gravação.

O contrato de 2016 era criado já com `status: "active"`. O `after_create`
reservava. O `after_save` de 2021, que queria pegar só a edição, olhava o
status, via `"active"`, e reservava de novo.

## Reproduzir antes de corrigir

A reprodução do Diego vira um script, rodado com o Rails carregado:

```ruby title="script/reproduzir_reserva_dupla.rb" numbered
pt140 = Equipment.find_by!(patrimony: "PT-140")
serra = Customer.find_by!(name: "Construtora Serra Azul")

antes = Reservation.count

Contract.create!(
  code: "CT-9001", equipment: pt140, customer: serra,
  responsible: "Rogério", site: "betim", status: "active",
  start_date: Date.new(2026, 5, 4), end_date: Date.new(2026, 5, 29),
)

puts "reservas criadas: #{Reservation.count - antes}"
```

```text
$ bin/rails runner script/reproduzir_reserva_dupla.rb
reservas criadas: 2
```

`bin/rails runner` roda um arquivo Ruby com o `nortea` inteiro carregado —
models, banco, configuração —, no ambiente de desenvolvimento. É o console
sem a digitação.

O script não é um teste, ainda. É uma frase que se confere rodando:
"criar um contrato ativo cria uma reserva". Hoje ela diz dois.

## A correção: observar a mudança

O que o Sérgio queria em 2021 não era "depois de salvar um contrato
ativo". Era "quando o contrato **passar a ser** ativo". São perguntas
diferentes, e o Rails responde a segunda:

```ruby title="app/models/contract.rb" numbered
class Contract < ApplicationRecord
  has_many :reservations

  after_save :register_reservation, if: :became_active?

  private

  def became_active?
    saved_change_to_status? && status == "active"
  end

  def register_reservation
    reservations.find_or_create_by!(
      equipment: equipment,
      starts_on: start_date,
      ends_on: end_date,
    )
  end
end
```

`saved_change_to_status?` pergunta se **esta gravação** mudou o `status`.
Na criação com `"active"`, mudou — de nada para ativo. Numa edição que
passa de `"reserved"` para `"active"`, mudou. Numa edição que só corrige o
nome do responsável, não mudou, e nenhuma reserva é criada.

O `after_create` saiu. Um callback só, que responde ao que interessa: o
contrato passou a ocupar a máquina.

E o `find_or_create_by!` no lugar do `create!`: se a reserva com esse
equipamento e esse período já existe, ele a devolve em vez de criar
outra. É a mesma pergunta do capítulo de filas que vem adiante — o que
acontece se isso rodar duas vezes? —, respondida aqui, onde a duplicata
nasceu.

```text
$ bin/rails runner script/reproduzir_reserva_dupla.rb
reservas criadas: 1
```

:::key
Um callback responde a um momento. Antes de escrever um, pergunte **qual
mudança** ele observa, não **qual evento**. "Depois de salvar" acontece em
toda gravação. "Quando o status passou a ser ativo" acontece uma vez.
`saved_change_to_...?` é a pergunta certa quase sempre.
:::

As seis reservas duplicadas de homologação e as quarenta e uma de
produção — contadas com um `group_by` por contrato e período — foram
removidas por uma migration de dados, depois de a Helena conferir a lista.

## O que não mora num callback

O `register_reservation` grava outra linha na mesma transação do contrato.
Se ele falhar, o contrato também não é gravado. Isso é bom: contrato ativo
sem reserva é o que a multa cobra.

Mas o `contract.rb` de 2021 tinha um terceiro callback:

```ruby
after_save :notify_helena
```

Ele mandava um e-mail. Dentro da transação. Se o servidor de e-mail
demorasse oito segundos, o formulário esperava oito segundos. Se o e-mail
falhasse, o contrato... era gravado, porque alguém tinha posto um `rescue`
em volta. Se o banco desfizesse a transação depois, a Helena recebia o
e-mail de um contrato que não existia.

O e-mail não é parte do contrato. É uma consequência dele, que pode
acontecer depois e pode ser tentada de novo. O capítulo de jobs o tira
daqui. Até lá, a regra:

:::pitfall
Callback serve para manter o próprio registro e os registros que dependem
dele coerentes, dentro da transação. E-mail, chamada a outro sistema,
geração de PDF — tudo que sai do banco — não vai em `after_save`. Se
precisar esperar o banco confirmar, é `after_commit`, e mesmo assim o
trabalho pesado vai para fora do pedido.
:::

:::milestone
Fim da Parte 4. O `nortea` está aberto na sua máquina, com o Ruby dele. As
três datas de começo têm significado e comentário no banco; os 212
contratos sem status foram preenchidos por migration; a PT-121 aparece
disponível depois do cancelamento; o formulário recusa contrato sem
responsável e a mesma máquina em dois períodos; e criar um contrato cria
uma reserva, não duas.
:::

:::summary
- Callback é um método que o Rails chama num momento da vida do registro.
  Quem salva não o vê.
- Na criação rodam `after_create` e `after_save`; na edição, `after_update`
  e `after_save`.
- Reproduza antes de corrigir. `bin/rails runner` roda um script com o
  Rails carregado.
- `saved_change_to_campo?` observa a mudança, não o evento.
  `find_or_create_by!` evita a duplicata.
- Callback mantém o registro coerente dentro da transação. O que sai do
  banco não mora nele.
:::

:::exercise level=1
Para cada operação, diga quais destes callbacks rodam: `after_create`,
`after_update`, `after_save`.

1. `Contract.create!(...)`
2. `contrato.update!(responsible: "Rogério")`
3. `contrato.update_column(:status, "active")`

:::answer
1. `after_create` e `after_save`.
2. `after_update` e `after_save`.
3. Nenhum. `update_column` escreve direto no banco, sem validação e sem
   callback — o caminho por cima do capítulo @cap:validacoes.

O terceiro é como um contrato passa a ativo sem gerar reserva. É por isso
que ele só aparece em migration de dados, com a reserva criada na mesma
migration.
:::

:::exercise level=2
Quando um contrato passa a `cancelled`, a reserva dele deve ser removida.
Escreva o callback, observando a mudança certa.

:::answer
```ruby
after_save :release_reservation, if: :became_cancelled?

private

def became_cancelled?
  saved_change_to_status? && status == "cancelled"
end

def release_reservation
  reservations.where(equipment: equipment).destroy_all
end
```

Roda uma vez, na gravação em que o status mudou para cancelado. Editar o
contrato já cancelado depois — corrigir o motivo do cancelamento — não
roda de novo.

É o outro lado do capítulo @cap:associacoes: lá, o cancelamento tinha de
ser filtrado na consulta. Aqui, ele libera a reserva na hora em que
acontece.
:::

:::exercise level=3
O Renato pergunta se a reserva deveria mesmo ser criada por callback, ou
se o controller deveria chamar `contrato.reservar!` depois de salvar.
Escreva os dois argumentos e a sua escolha para o `nortea`.

:::answer
**A favor do callback:** todo caminho que torna um contrato ativo — o
formulário, o console, a importação, a API futura — cria a reserva sem
ninguém lembrar. A regra "contrato ativo tem reserva" fica num lugar só,
dentro da transação.

**A favor da chamada explícita:** quem lê o controller vê a reserva sendo
criada. O teste de um contrato que não precisa de reserva não precisa
montá-la. E o `update_column` da migration não é um buraco escondido: ele
nunca criaria reserva, e todo mundo sabe.

**Para o `nortea`:** callback, com a condição da mudança. A regra é do
contrato, não da tela, e o sistema tem pelo menos quatro caminhos que
ativam contrato. O custo — o callback é invisível — se paga com o nome
claro (`became_active?`) e com o teste que o capítulo de testes escreve.
O e-mail da Helena, que não é regra do contrato, sai do callback.
:::
