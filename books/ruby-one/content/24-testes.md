---
title: "Testes"
number: 24
slug: testes
part: p6
kicker: "O teste passava desde 2016. A factory fabricava um contrato sem equipamento, sem cliente e sem data — um contrato que o pátio devolveria no portão."
goal: >-
  Ler e escrever testes com RSpec, entender o que uma factory fabrica,
  ver o teste ficar vermelho quando o contrato é impossível e verde quando
  a factory passa a exigir o que o pátio exige, e transformar a reprodução
  da reserva dupla num teste que roda sozinho.
---

:::story O contrato impossível
Na segunda, 4 de maio, a Lívia rodou os testes do `nortea` pela primeira
vez inteiros.

```text
$ bundle exec rspec
.........

Finished in 0.41 seconds
9 examples, 0 failures
```

— Nove — disse ela. — Para um sistema de dez anos.

O Diego abriu a factory:

```ruby title="spec/factories/contracts.rb"
FactoryBot.define do
  factory :contract do
    code { "CT-0001" }
  end
end
```

— Isso fabrica o quê? — perguntou ele.

— Um contrato com código — disse o Caio. — Mais nada.

— Sem equipamento?

— Sem equipamento, sem cliente, sem data. O teste do `active?` monta um
desses, põe status e data de fim, e pergunta.

O Diego leu o teste e depois olhou para a Lívia.

— Então os nove passam porque nenhum deles tenta gravar.

— Nenhum.
:::

## O que um teste é

Um teste é um programa que roda o seu código e confere o resultado. Não
prova que o código está certo em todos os casos. Prova que **um
comportamento combinado continua acontecendo** — hoje, e depois da próxima
alteração de qualquer pessoa.

A reprodução do capítulo @cap:callbacks já era quase isso: um script que
criava um contrato e contava as reservas. Faltava ele conferir sozinho e
rodar junto com os outros, sem alguém olhar a saída.

O `nortea` usa RSpec. Os testes ficam em `spec/`, e os arquivos terminam
em `_spec.rb`:

```ruby title="spec/models/contract_spec.rb" numbered
require "rails_helper"

RSpec.describe Contract do
  describe "#occupying?" do
    it "é verdadeiro para contrato ativo dentro do prazo" do
      contrato = Contract.new(status: "active",
                              end_date: Date.new(2026, 6, 30))

      expect(contrato.occupying?(Date.new(2026, 5, 4))).to be(true)
    end
  end
end
```

`describe` agrupa. `it` é um exemplo — um comportamento, com uma frase
que diz qual. `expect(...).to be(true)` é a conferência: se o valor não
for `true`, o teste falha e diz o que veio.

```text
$ bundle exec rspec spec/models/contract_spec.rb
.

Finished in 0.08 seconds
1 example, 0 failures
```

O ponto é um exemplo que passou. Um `F` seria um que falhou.

:::term Teste
Um programa que executa um pedaço do sistema e confere o resultado.
`describe` diz o que está sendo testado; `it` diz o comportamento;
`expect` confere.

Um teste verde diz que o comportamento descrito na frase aconteceu. Não
diz nada sobre o que a frase não descreve.
:::

## Factory

Montar um contrato em cada teste, com os campos à mão, fica longo. A
factory é uma receita: o teste pede um contrato, e ela o fabrica com
valores padrão.

```ruby
contrato = build(:contract, status: "active")
contrato = create(:contract, status: "active")
```

`build` monta o objeto na memória, sem gravar. `create` monta e grava no
banco de teste — e passa pelas validações do capítulo @cap:validacoes.

A factory de 2016 tinha um campo. Com `build`, ela funciona, porque nada
confere o contrato: o teste só pergunta ao objeto. Os nove testes usavam
`build`. Nenhum sabia que o contrato fabricado não seria aceito pelo
próprio sistema.

## O vermelho

O Diego escreveu o primeiro teste que precisava gravar: o dos disponíveis,
do capítulo @cap:associacoes.

```ruby title="spec/models/equipment_spec.rb" numbered
require "rails_helper"

RSpec.describe Equipment do
  describe ".available" do
    it "inclui a máquina cujo único contrato foi cancelado" do
      pt121 = create(:equipment, patrimony: "PT-121")
      create(:contract, equipment: pt121, status: "cancelled")

      expect(Equipment.available).to include(pt121)
    end
  end
end
```

```text
$ bundle exec rspec spec/models/equipment_spec.rb
F

Failures:

  1) Equipment.available inclui a máquina cujo único contrato foi
     cancelado
     Failure/Error: create(:contract, equipment: pt121,
                           status: "cancelled")

     ActiveRecord::RecordInvalid:
       A validação falhou: Cliente é obrigatório, Responsável no
       canteiro não pode ficar em branco, Início da cobrança não
       pode ficar em branco, Devolução prevista não pode ficar em
       branco
```

Vermelho, e pelo motivo certo. O teste não falhou na regra de
disponibilidade. Falhou ao fabricar o contrato: a factory produz um
contrato que o model recusa, e o `create` usa `save!`, que levanta.

A mensagem é a lista do que o pátio exige: cliente, responsável, início,
devolução. Tudo que a factory de 2016 não sabia.

## A factory honesta

```ruby title="spec/factories/contracts.rb" numbered
FactoryBot.define do
  factory :contract do
    sequence(:code) { |n| format("CT-%04d", 5000 + n) }
    customer
    equipment
    site { "contagem" }
    responsible { "Rogério Tavares" }
    status { "active" }
    start_date { Date.new(2026, 5, 4) }
    end_date { Date.new(2026, 6, 30) }
    daily_rate_cents { 48_000 }

    trait :cancelled do
      status { "cancelled" }
      cancelled_at { Time.zone.local(2026, 5, 4, 9, 0) }
    end

    trait :overdue do
      start_date { Date.new(2026, 3, 2) }
      end_date { Date.new(2026, 4, 30) }
      returned_at { nil }
    end
  end
end
```

`sequence(:code)` gera um código diferente a cada contrato fabricado —
`CT-5001`, `CT-5002` —, porque o código é único e dois contratos no mesmo
teste recusariam um ao outro. `customer` e `equipment`, sem valor, dizem à
factory para fabricar também o cliente e o equipamento, com as factories
deles.

`trait` é uma variação com nome: `create(:contract, :cancelled)` é um
contrato cancelado, com a data do cancelamento. O teste diz o que importa
para ele e herda o resto.

As datas são fixas. Uma factory com `Date.today` fabrica contratos que
vencem em dias diferentes conforme o dia em que o teste roda, e o teste
que passava em maio falha em julho sem ninguém ter mexido.

```ruby
create(:contract, :cancelled, equipment: pt121)
```

```text
$ bundle exec rspec spec/models/equipment_spec.rb
.

1 example, 0 failures
```

Verde. Agora o verde diz uma coisa: um contrato **que o pátio aceitaria**,
cancelado, não prende a máquina.

:::key
Uma factory é uma afirmação sobre o que é um registro válido. A de 2016
afirmava que um contrato era um código. Todo teste construído sobre ela
testava um objeto que não existe no pátio. A factory precisa passar pelas
mesmas validações que o formulário — e o jeito de conferir é criar com
`create` pelo menos uma vez.
:::

Os nove testes antigos continuaram verdes com a factory nova. O que mudou
não foi o resultado deles. Foi o que eles significam.

## A reserva dupla, de novo

O script do capítulo @cap:callbacks vira um teste:

```ruby title="spec/models/contract_spec.rb" numbered
describe "reserva" do
  it "cria uma reserva ao criar contrato ativo" do
    expect { create(:contract, status: "active") }
      .to change(Reservation, :count).by(1)
  end

  it "não cria reserva ao corrigir o responsável" do
    contrato = create(:contract, status: "active")

    expect { contrato.update!(responsible: "Juliana Prates") }
      .not_to change(Reservation, :count)
  end

  it "cria a reserva quando a reserva vira ativa" do
    contrato = create(:contract, status: "reserved")

    expect { contrato.update!(status: "active") }
      .to change(Reservation, :count).by(1)
  end
end
```

`expect { ... }.to change(Reservation, :count).by(1)` roda o bloco e
confere que a contagem de reservas subiu exatamente um. É a frase do
script — "criar um contrato ativo cria uma reserva" — escrita para o
computador conferir.

O segundo exemplo é o que o Diego mais queria: corrigir o nome do
responsável **não** cria reserva. Se alguém, daqui a um ano, trocar o
callback de volta para um `after_save` sem condição, este exemplo fica
vermelho antes de chegar à homologação.

:::pitfall
Cada exemplo começa com o banco de teste limpo, e o que ele grava é
desfeito no fim. Um teste não pode depender de outro ter rodado antes. Se
depender, ele passa rodando a suíte inteira e falha rodando sozinho — ou o
contrário, dependendo da ordem, que o RSpec embaralha de propósito.
:::

:::summary
- Teste confere um comportamento combinado. `describe`, `it` e `expect`.
- `build` monta sem gravar; `create` grava e passa pelas validações.
- Uma factory que só funciona com `build` fabrica registros que o sistema
  recusa. O vermelho do `create` mostra o que falta.
- `sequence` para campos únicos; `trait` para variações com nome; datas
  fixas.
- `change(...).by(1)` transforma "cria uma reserva" numa conferência. O
  exemplo do que **não** deve acontecer é o que protege a correção.
:::

:::exercise level=1
Escreva o exemplo que confere que um contrato fabricado com o trait
`:overdue` está ocupando e atrasado em 4 de maio.

:::answer
```ruby
it "vencido e não devolvido continua ocupando" do
  contrato = build(:contract, :overdue)
  hoje = Date.new(2026, 5, 4)

  expect(contrato.occupying?(hoje)).to be(true)
  expect(contrato.overdue?(hoje)).to be(true)
end
```

`build` basta: o teste pergunta ao objeto e não precisa do banco. A
factory honesta garante que esse mesmo contrato seria aceito se fosse
gravado.
:::

:::exercise level=2
Escreva o teste da validação de sobreposição do capítulo @cap:validacoes:
duas reservas da mesma máquina, com períodos que se cruzam, e a mensagem
com o código do primeiro contrato.

:::answer
```ruby
it "recusa a mesma máquina em períodos que se cruzam" do
  pt118 = create(:equipment, patrimony: "PT-118")
  primeiro = create(:contract, equipment: pt118,
                    start_date: Date.new(2026, 5, 4),
                    end_date: Date.new(2026, 6, 30))

  segundo = build(:contract, equipment: pt118,
                  start_date: Date.new(2026, 6, 1),
                  end_date: Date.new(2026, 7, 15))

  expect(segundo).not_to be_valid
  expect(segundo.errors[:equipment].first)
    .to include(primeiro.code)
end
```

`be_valid` chama `valid?`. O primeiro contrato é criado — precisa estar no
banco para a validação encontrá-lo. O segundo só é montado: o que se
confere é que ele seria recusado.
:::

:::exercise level=3
O Diego propõe um exemplo para cada coluna das vinte e três, "para
cobertura". O Renato pergunta o que a Helena ganha com isso. Responda os
dois, e diga quais cinco exemplos você escreveria primeiro para o dia 3 de
junho.

:::answer
Um exemplo por coluna confere que o Rails lê coluna — o que o Rails já
testa. A cobertura sobe e nenhum comportamento que custa multa fica
protegido. A Helena não ganha nada.

Os cinco primeiros, na ordem da multa:

1. Contrato cancelado libera a máquina nos disponíveis.
2. Vencido e não devolvido continua ocupando.
3. A mesma máquina em dois períodos que se cruzam é recusada.
4. Criar contrato ativo cria uma reserva; corrigir o responsável não.
5. Contrato sem responsável é recusado.

Cada um corresponde a uma ligação da Helena ou a um print do Diego deste
livro. É esse o critério: um exemplo por defeito que já aconteceu, antes
de um exemplo por linha de código.
:::
