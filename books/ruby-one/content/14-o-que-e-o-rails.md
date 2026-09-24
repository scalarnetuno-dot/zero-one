---
title: "O que é o Rails"
number: 14
slug: o-que-e-o-rails
part: p4
kicker: "Nenhum arquivo do nortea diz que o endereço /contracts chama o ContractsController. O Rails decide pelo nome."
goal: >-
  Abrir o nortea sabendo onde cada coisa mora, subir o servidor local,
  seguir um pedido do endereço à página, e reconhecer o que o framework
  decide sozinho pelo nome dos arquivos.
---

:::story Onde está escrito
Na segunda, 30 de março, a Lívia subiu o `nortea` na máquina dela pela
primeira vez e abriu `localhost:3000/contracts`. A lista de contratos de
homologação apareceu.

Ela procurou, no projeto inteiro, onde estava escrito que aquele endereço
abria aquela lista.

— Tem uma linha nas rotas — disse ela. — `resources :contracts`. Mas não
diz qual arquivo.

— Diz — disse o Caio. — Pelo nome.

— E a tabela? O `contract.rb` não fala `contracts` em lugar nenhum.

— Também pelo nome.

O Renato, que passava com a caneca, parou atrás deles.

— É a parte que mais ajuda e a que mais engana. Funciona sem você
escrever. E, quando alguém muda um nome, para de funcionar sem ninguém ter
mexido.
:::

## Framework

O capítulo @cap:fevereiro-de-1993 definiu: o Rails é um programa Ruby que
espera os arquivos da Nortea em pastas combinadas. Até aqui, na `patio`,
quem decidia tudo era você: o arquivo que roda, a ordem, o que chama o
quê. No Rails, o framework decide a forma do programa e chama o seu código
nos pontos combinados.

Um script da `patio` começa na primeira linha e termina na última. O
`nortea` não tem primeira linha sua. Ele sobe, espera um pedido, e o
framework escolhe qual pedaço do código da Nortea atende.

## As pastas

:::tree title="O nortea, as pastas que importam"
nortea/
  Gemfile, Gemfile.lock    # capítulo anterior
  .ruby-version            # 3.3.6
  app/
    models/                # contract.rb, equipment.rb, reservation.rb
    controllers/           # contracts_controller.rb
    views/contracts/       # as páginas
    jobs/
  config/
    routes.rb              # quais endereços existem
    database.yml           # em qual banco cada ambiente grava
    environments/          # development, test, production
  db/
    schema.rb              # o desenho das tabelas
    migrate/               # o histórico das mudanças nelas
  spec/                    # os testes
  bin/rails                # o comando do framework
:::

A pasta `app` é o código da Nortea. A pasta `config` é o que diz ao Rails
como juntar esse código. Quase todo o trabalho dos próximos capítulos
acontece em `app/models`, `app/controllers`, `app/views` e
`config/routes.rb`.

A versão está no `Gemfile.lock`:

```text
$ grep " rails (" Gemfile.lock
    rails (7.2.2)
```

O `nortea` nasceu num Rails 4.2, em março de 2016. Passou pelo 5, pelo 6, e
chegou ao 7.2 no fim de 2024, numa atualização que o Sérgio fez em três meses.
As pastas são as mesmas desde 2016. O que mudou foi o miolo.

## Subir o servidor

```text
$ bin/rails server
=> Booting Puma
=> Rails 7.2.2 application starting in development
=> Run `bin/rails server --help` for more startup options
* Listening on http://127.0.0.1:3000
```

`bin/rails` é o comando do framework, na versão do lock — o equivalente a
`bundle exec rails`. `server` sobe um servidor web local. Puma é o nome do
servidor; o Rails o usa por padrão.

`development` é o **ambiente**. O mesmo código roda em três: `development`
na sua máquina, `test` quando os testes rodam, `production` no servidor. O
`database.yml` aponta cada um para um banco diferente. A lista que a Lívia
viu era do banco de desenvolvimento dela, preenchido com uma cópia
anonimizada da homologação.

:::warning O banco da sua máquina
O `database.yml` de desenvolvimento aponta para um banco local. Se alguém
um dia apontá-lo para o de produção "só para testar uma coisa", o
`bin/rails` da sua máquina passa a gravar no pátio. O arquivo com a senha
de produção não fica no repositório por isso.
:::

## Um pedido, do endereço à página

O navegador pede `GET /contracts`. O caminho:

:::diagram type="flowchart" caption="O pedido entra por uma rota, passa por um controller, fala com um model, e a resposta volta por uma view."
nodes:
  - { id: req, type: io, text: "GET /contracts" }
  - { id: r, type: process, text: "config/routes.rb" }
  - { id: c, type: process, text: "ContractsController#index" }
  - { id: m, type: process, text: "Contract (tabela contracts)" }
  - { id: v, type: process, text: "views/contracts/index" }
  - { id: out, type: io, text: "página HTML" }
edges:
  - { from: req, to: r }
  - { from: r, to: c }
  - { from: c, to: m }
  - { from: m, to: c }
  - { from: c, to: v }
  - { from: v, to: out }
:::

**A rota** decide qual controller e qual método atendem aquele verbo e
aquele caminho.

**O controller** recebe o pedido. O método `index` pede os contratos ao
model.

**O model** fala com a tabela. `Contract.all` vira uma consulta ao banco.

**A view** monta o HTML com os contratos que o controller entregou.

Cada peça ganha o seu capítulo. Por enquanto, basta saber em que ordem
elas aparecem.

## O que o nome decide

Nenhum arquivo do `nortea` diz, por extenso, a maior parte dessas ligações.
O Rails as deduz dos nomes:

| Nome | O Rails conclui |
|---|---|
| `resources :contracts` | endereços `/contracts`, `/contracts/:id`, e os outros |
| `/contracts` | classe `ContractsController`, arquivo `contracts_controller.rb` |
| método `index` | view `app/views/contracts/index.html.erb` |
| classe `Contract` | tabela `contracts` |
| coluna `equipment_id` | liga ao model `Equipment` |

Tabela: O singular é o model; o plural é a tabela e o controller. Os
arquivos têm o nome em `snake_case`; as classes, em `CamelCase`.

É a *convenção sobre configuração* de 2004. O arquivo não repete a ligação
quando a convenção basta. Para quem conhece a convenção, o projeto é
previsível: dado um endereço, você sabe qual arquivo abrir. Para quem não
conhece, é invisível: a ligação não está escrita em lugar nenhum para ser
procurada.

:::key
No Rails, **renomear é mudar comportamento**. Renomear
`contracts_controller.rb` para `contratos_controller.rb` não é faxina: é a
rota apontando para uma classe que não existe mais. Antes de mudar um nome
no `nortea`, pergunte que outro nome o Rails deduz a partir dele.
:::

A convenção fala inglês. `Contract` vira `contracts` porque o Rails sabe
pluralizar inglês. É por isso que o `nortea`, feito por brasileiros, tem
todos os nomes de código em inglês e todos os textos da tela em português.
Com um nome que parece exceção e não é, que o capítulo seguinte abre: a
tabela de equipamentos.

## Ver as rotas

As ligações que o Rails deduziu podem ser listadas:

```text
$ bin/rails routes -c contracts
      Prefix Verb   URI Pattern                Controller#Action
   contracts GET    /contracts(.:format)       contracts#index
             POST   /contracts(.:format)       contracts#create
new_contract GET    /contracts/new(.:format)   contracts#new
    contract GET    /contracts/:id(.:format)   contracts#show
```

A lista tem mais linhas; estas são quatro delas. `contracts#index` quer dizer
"controller `contracts`, método `index`". É a documentação que nunca
desatualiza, porque é gerada do próprio projeto. O capítulo de rotas volta
a ela.

:::summary
- O Rails decide a forma do programa e chama o código da Nortea nos pontos
  combinados.
- `app` é o código; `config` diz como juntá-lo; `db/schema.rb` descreve as
  tabelas.
- `bin/rails server` sobe o servidor local no ambiente `development`, com
  banco próprio.
- Um pedido passa por rota, controller, model e view, nessa ordem.
- Os nomes decidem as ligações: singular é model, plural é tabela e
  controller. Renomear é mudar comportamento.
:::

:::exercise level=1
Para o endereço `GET /equipment/412`, diga, pela convenção, qual
controller, qual método e qual view o Rails procuraria.

:::answer
Controller `EquipmentController`, no arquivo
`app/controllers/equipment_controller.rb`. Método `show`, porque o caminho
tem um identificador. View `app/views/equipment/show.html.erb`.

O controller não é `EquipmentsController`: em inglês, `equipment` não tem
plural, e o Rails sabe. O capítulo seguinte mostra a regra que o `nortea`
escreveu mesmo assim.
:::

:::exercise level=2
A Lívia quer criar uma página nova, "ocupação por canteiro", em
`/occupancy`. Liste os três arquivos que ela vai precisar tocar ou criar,
na ordem em que o pedido os atravessa.

:::answer
`config/routes.rb`, para o endereço existir e apontar para um controller.

`app/controllers/occupancy_controller.rb`, com a classe
`OccupancyController` e um método `index` que busca os dados.

`app/views/occupancy/index.html.erb`, com a página.

O model não precisa ser criado: os dados vêm de `Contract` e `Equipment`,
que já existem.
:::

:::exercise level=3
O Sérgio sugere, "para ficar mais claro para a Helena", renomear o model
`Contract` para `Contrato`. Liste o que deixaria de funcionar pela
convenção, e diga onde a clareza para a Helena de fato mora.

:::answer
A classe `Contrato` passaria a procurar a tabela `contratos`, que não
existe. As associações que apontam para `:contract` e a coluna
`contract_id` em outras tabelas deixariam de achar o model. As rotas
`resources :contracts` continuariam chamando `ContractsController`, que
buscaria `Contract` e não acharia. As views e os testes que chamam
`Contract` quebrariam.

Cada uma dessas ligações pode ser reescrita à mão, com configuração. É o
trabalho de vários dias para trocar um nome que a Helena nunca vê.

A clareza para a Helena mora no texto da tela: o título da página, o
rótulo da coluna, a mensagem de erro. Esses já estão em português, e é lá
que "Contrato" aparece para ela.
:::
