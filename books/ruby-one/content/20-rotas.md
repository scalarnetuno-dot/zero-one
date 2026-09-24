---
title: "Rotas"
number: 20
slug: rotas
part: p5
kicker: "O botão dizia Cancelar contrato. O pedido que ele mandava era POST /contracts — o mesmo endereço de criar um contrato."
goal: >-
  Ler o pedido HTTP como verbo e caminho, entender o que resources declara,
  dar ao cancelamento uma rota com nome em vez de um parâmetro escondido, e
  usar os nomes de rota em vez de montar endereço à mão.
---

:::story O mesmo endereço
Na segunda, 20 de abril, véspera do feriado, a Marta pediu para ver o
cancelamento funcionando. A Lívia abriu um contrato de teste, clicou em
**Cancelar contrato**, e o navegador, no painel de rede, mostrou o pedido:

```text
POST /contracts
cancel=1&contract_id=2033
```

— POST em `/contracts` — disse ela. — Esse é o endereço de criar
contrato.

A Marta leu por cima do ombro.

— E por que cancela?

— Porque o `create` começa com um `if`. Se vier `cancel`, ele não cria:
procura o contrato e cancela.

— Então o botão de cancelar chama o criar.

— Chama.

O Caio, sem virar a cadeira:

— 2019. Não tinha rota para cancelar, e alguém não quis mexer no
`routes.rb`.
:::

## Um pedido é verbo e caminho

Todo pedido que chega ao `nortea` tem duas partes que decidem para onde
ele vai: o **verbo** e o **caminho**.

```text
GET /contracts/2033
```

`GET` é o verbo; `/contracts/2033` é o caminho. O verbo diz a intenção:

| Verbo | Intenção |
|---|---|
| `GET` | ler, sem mudar nada |
| `POST` | criar |
| `PATCH` | alterar parte de um registro |
| `DELETE` | apagar |

Tabela: São convenções do HTTP, não do Rails. O Rails as segue, e o
navegador, o cache e as ferramentas de monitoramento também.

`GET` é o verbo que o navegador usa quando você digita um endereço ou
clica num link. Um `GET` nunca deve mudar nada: o navegador pode repeti-lo
sozinho, e um robô de busca pode segui-lo.

## `config/routes.rb`

O arquivo de rotas diz quais pedidos existem e quem os atende:

```ruby title="config/routes.rb" numbered
Rails.application.routes.draw do
  resources :contracts
  resources :equipment, only: [:index, :show]
end
```

`resources :contracts` declara, numa linha, as sete rotas do cadastro de
contratos:

```text
$ bin/rails routes -c contracts
       Prefix Verb   URI Pattern                 Controller#Action
    contracts GET    /contracts                  contracts#index
              POST   /contracts                  contracts#create
 new_contract GET    /contracts/new              contracts#new
edit_contract GET    /contracts/:id/edit         contracts#edit
     contract GET    /contracts/:id              contracts#show
              PATCH  /contracts/:id              contracts#update
              DELETE /contracts/:id              contracts#destroy
```

`:id` no caminho é um pedaço variável: em `/contracts/2033`, o `id` vale
`"2033"`, e o controller o recebe. O mesmo caminho com verbos diferentes
vai para métodos diferentes: `GET /contracts/:id` mostra, `PATCH` altera,
`DELETE` apaga.

`only:` restringe. O cadastro de equipamento não se faz pelo `nortea`, e
as rotas de criar e apagar equipamento não existem.

:::term Rota
A ligação entre um verbo mais um caminho e um método de controller. Uma
rota que não está em `routes.rb` não existe: o pedido recebe `404`, sem
chegar a nenhum código da Nortea.
:::

## O cancelamento com nome

Cancelar não é criar, e também não é apagar. O contrato cancelado continua
existindo: é histórico, é o que a Helena consulta quando o cliente liga. É
uma **ação sobre um contrato**, que muda o estado dele.

A rota diz isso:

```ruby title="config/routes.rb" numbered
Rails.application.routes.draw do
  resources :contracts do
    member do
      patch :cancel
    end
  end
end
```

```text
      Prefix Verb   URI Pattern                   Controller#Action
cancel_contract PATCH  /contracts/:id/cancel      contracts#cancel
```

`member` declara rotas sobre **um** contrato: o caminho tem `:id`.
`patch :cancel` cria `PATCH /contracts/:id/cancel`, atendida pelo método
`cancel` do controller. O verbo é `PATCH` porque altera parte do
contrato — o status.

Agora o pedido diz o que faz:

```text
PATCH /contracts/2033/cancel
```

Quem lê o log do servidor, o painel de rede do navegador ou a lista de
rotas sabe o que aconteceu, sem abrir o controller. E o `create` volta a
fazer uma coisa só.

:::key
Se o botão diz uma coisa e o pedido diz outra, o pedido está errado. A
rota é o nome que o sistema dá à ação: é o que aparece no log, no
monitoramento e no histórico do navegador. Um parâmetro escondido num
formulário não aparece em nenhum deles.
:::

## `collection` e rota aninhada

Existe o irmão do `member`, para ações sobre **a coleção**, sem `:id`:

```ruby
resources :contracts do
  collection do
    get :occupancy
  end
end
```

```text
GET /contracts/occupancy   contracts#occupancy
```

E a rota aninhada, para quando um recurso só faz sentido dentro de outro:

```ruby
resources :equipment, only: [:index, :show] do
  resources :contracts, only: [:index]
end
```

```text
GET /equipment/:equipment_id/contracts   contracts#index
```

"Os contratos da PT-118" é `/equipment/412/contracts`. O controller recebe
o `equipment_id` e filtra por ele — com a associação do capítulo
@cap:associacoes.

:::pitfall
Rota aninhada em mais de um nível —
`/customers/7/sites/3/contracts/2033/reservations` — fica difícil de
montar e de ler, e carrega `id` que o controller nem usa. A casa aninha um
nível, no máximo. O contrato tem `id` próprio; não precisa do cliente no
caminho para ser encontrado.
:::

## Nome de rota, não endereço montado

A coluna `Prefix` da listagem é o nome da rota. Cada nome vira um método
que monta o endereço:

```ruby
contracts_path                    # => "/contracts"
contract_path(contrato)           # => "/contracts/2033"
cancel_contract_path(contrato)    # => "/contracts/2033/cancel"
edit_contract_path(contrato)      # => "/contracts/2033/edit"
```

Os métodos existem nas views e nos controllers. Recebem o registro e usam
o `id` dele. Com `_url` no lugar de `_path`, devolvem o endereço completo,
com o domínio — o que um e-mail precisa.

A view de 2019 tinha o endereço montado à mão:

```erb
<form action="/contracts" method="post">
  <input type="hidden" name="cancel" value="1">
  <input type="hidden" name="contract_id" value="<%= c.id %>">
```

A de agora usa o nome:

```erb
<%= button_to "Cancelar contrato", cancel_contract_path(c),
              method: :patch %>
```

`button_to` monta um formulário com um botão, com o verbo e o caminho
certos. Se um dia o caminho mudar no `routes.rb`, o botão acompanha,
porque ele pergunta o endereço pelo nome.

:::summary
- Um pedido é verbo e caminho. `GET` lê e nunca muda nada; `POST` cria;
  `PATCH` altera; `DELETE` apaga.
- `resources` declara as sete rotas de um cadastro. `only:` restringe.
- Ação sobre um registro vai em `member`; sobre a coleção, em
  `collection`. Aninhe um nível, no máximo.
- `bin/rails routes` lista o que existe. O que não está lá recebe `404`.
- Use `contract_path(c)`, não `"/contracts/#{c.id}"`.
:::

:::exercise level=1
Diga o verbo e o método de controller de cada ação, com o `routes.rb` do
capítulo:

1. Abrir a página de um contrato.
2. Salvar a edição do responsável.
3. Cancelar um contrato.
4. Ver a lista de contratos da PT-118.

:::answer
1. `GET /contracts/:id`, `contracts#show`.
2. `PATCH /contracts/:id`, `contracts#update`.
3. `PATCH /contracts/:id/cancel`, `contracts#cancel`.
4. `GET /equipment/:equipment_id/contracts`, `contracts#index`.

O 2 e o 3 usam o mesmo verbo. O que os separa é o caminho.
:::

:::exercise level=2
O Diego descobre que existe um link, na tela de ocupação, para
`GET /contracts/2033?cancelar=sim`, e que ele cancela o contrato.
Explique por que isso é perigoso mesmo que ninguém clique por engano.

:::answer
Um `GET` pode ser repetido por qualquer coisa que siga links sem pedir
licença: o navegador que pré-carrega páginas, um robô de busca num
ambiente exposto, a ferramenta de verificação de links, o histórico que
alguém abre de novo. Cada um desses cancela o contrato.

Um `GET` que muda estado também pula a proteção contra falsificação de
formulário que o Rails aplica aos outros verbos. Um link numa página de
fora poderia cancelar um contrato de quem estivesse com o `nortea` aberto.

A correção é a do capítulo: cancelar é `PATCH` numa rota com nome, chamado
por um `button_to`.
:::

:::exercise level=3
A Marta quer uma ação "renovar", que cria um contrato novo a partir de um
existente, com o mesmo equipamento, cliente e responsável, e o período
seguinte. Escreva a rota e justifique o verbo e o lugar — `member` ou
`collection`.

:::answer
```ruby
resources :contracts do
  member do
    patch :cancel
    post :renew
  end
end
```

```text
POST /contracts/:id/renew   contracts#renew
```

`member`, porque a renovação parte de **um** contrato: o `:id` diz qual.
`POST`, porque o resultado é um registro novo — criar é `POST`. O
contrato original não muda.

Uma alternativa seria `POST /contracts` com um `from_id`. Ela esconde a
intenção num parâmetro, que é o defeito do começo do capítulo com outra
roupa.
:::
