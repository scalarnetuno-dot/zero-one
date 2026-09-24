---
title: "Controllers"
number: 21
slug: controllers
part: p5
kicker: "Trinta e sete commits num método de vinte e oito linhas. Cada um corrigia um caso, e nenhum tirava a correção anterior."
goal: >-
  Ler um controller sabendo o que é dele e o que já devia estar no model:
  params e strong parameters, o if do save, render e redirect, e o begin
  que some quando a falha vira validação.
---

:::story Trinta e sete
Na quarta, 22 de abril, com o `cancel` já na rota própria, a Lívia abriu o
`create` para tirar de lá o `if params[:cancel]`. Antes de apagar, rodou:

```text
$ git log --oneline -- app/controllers/contracts_controller.rb | wc -l
37
```

— Trinta e sete commits — disse ela.

O Caio chegou a cadeira mais perto.

— Lê de baixo para cima. Cada um é um dia em que alguma coisa deu errado
no pátio.

Ela leu. `corrige cancelamento`. `nao duplicar codigo`. `aviso sem
responsavel`. `reserva nao ativa`. `temporário`. `hotfix serra azul`.

O método tinha vinte e oito linhas.

— E se eu reescrever do zero? — perguntou ela.

— Aí você apaga as trinta e sete correções junto — disse o Caio. — Tira
uma de cada vez. A que você sabe onde foi parar.
:::

## O `create` de 2021

```ruby title="app/controllers/contracts_controller.rb" numbered
def create
  if params[:cancel]
    c = Contract.find(params[:contract_id])
    c.update(status: "cancelled")
    redirect_to contracts_path and return
  end

  @contract = Contract.new(params[:contract].permit!)
  @contract.status = "active" unless params[:reserve]

  begin
    @contract.save
  rescue ActiveRecord::RecordNotUnique
    @contract.code = "#{@contract.code}-2"
    @contract.save
  end

  unless @contract.persisted?
    flash[:alerta] = "Não foi possível salvar"
    redirect_to new_contract_path and return
  end

  flash[:alerta] = "Sem responsável" unless @contract.responsible
  redirect_to @contract
end
```

Quatro problemas empilhados, e todos já têm solução em capítulos
anteriores. O controller não precisa de uma faxina. Precisa perder, um por
um, o que não é dele.

## O que é do controller

Um controller recebe o pedido que a rota entregou, pede ao model o que
precisa, e decide a resposta. Cada método público atende uma rota: `index`,
`show`, `create`, `cancel`.

```ruby title="app/controllers/contracts_controller.rb" numbered
class ContractsController < ApplicationController
  def show
    @contract = Contract.find(params[:id])
  end
end
```

`params` é um hash com tudo que veio no pedido: o `:id` do caminho, os
campos do formulário, os parâmetros depois do `?` no endereço. `@contract`,
com `@`, é uma variável de instância do controller — e é por ela que a
view vai receber o contrato. Sem nenhuma outra linha, o Rails procura
`app/views/contracts/show.html.erb` e a monta.

:::term Controller
A classe que atende as rotas de um recurso. Cada método público é uma
ação. O controller lê `params`, chama o model e responde: com uma view,
com um redirecionamento ou com um status.

O que decide se um contrato é válido não é dele. É do model.
:::

## Primeiro: o cancelamento sai

O capítulo @cap:rotas deu ao cancelamento a própria rota. O primeiro
bloco do `create` vira a ação `cancel`:

```ruby title="app/controllers/contracts_controller.rb" numbered
def cancel
  @contract = Contract.find(params[:id])
  @contract.update!(status: "cancelled")
  redirect_to @contract, notice: "Contrato cancelado."
end
```

`update!` em vez de `update`: se o cancelamento falhar, a falha sobe. Nada
de redirecionar para a lista como se tivesse dado certo. O callback do
capítulo @cap:callbacks libera a reserva sozinho.

## Segundo: o `permit!` sai

`params[:contract].permit!` aceita **qualquer campo** que venha do
formulário. O formulário da Nortea tem oito campos. O pedido pode ter
vinte e três — todas as colunas —, inclusive `status`, `cancelled_at` e
`created_by`, se alguém montar o pedido à mão.

O Rails chama a proteção de *strong parameters*: o controller declara quais
campos aceita.

```ruby title="app/controllers/contracts_controller.rb" numbered
private

def contract_params
  params.require(:contract).permit(
    :code, :customer_id, :equipment_id, :site, :responsible,
    :start_date, :end_date, :daily_rate_cents,
  )
end
```

`require(:contract)` exige que o pedido tenha a chave `contract`; sem ela,
responde `400`. `permit` lista os campos aceitos; o resto é descartado.
`status` não está na lista. O status de um contrato muda por ação com
nome — `cancel`, a ativação — e não por um campo que o formulário
esqueceu de esconder.

:::pitfall
`permit!` é o `attr_accessor` do capítulo @cap:classes levado ao
formulário: tudo aberto, para qualquer um. Ele aparece em código escrito
com pressa porque o erro de `permit` esquecido é chato. O erro chato é a
proteção funcionando.
:::

## Terceiro: o `begin` sai

O `begin ... rescue ActiveRecord::RecordNotUnique` de 2020 existe porque
dois contratos com o mesmo código estouravam o índice único do banco, e o
formulário mostrava a página de erro do servidor. A correção da época foi
capturar a exceção e inventar um código: `CT-2041-2`.

Há um contrato `CT-2041-2` em produção. Ninguém sabe se ele é uma
renovação ou um clique duplo.

O capítulo @cap:validacoes deu a resposta que faltava em 2020: a
validação de unicidade do código. Com ela, o código repetido é recusado
**antes** de chegar ao banco, com uma mensagem na tela, e o `save`
simplesmente devolve `false`.

O `create` fica:

```ruby title="app/controllers/contracts_controller.rb" numbered
def create
  @contract = Contract.new(contract_params)
  @contract.status = params[:reserve] ? "reserved" : "active"

  if @contract.save
    redirect_to @contract, notice: "Contrato criado."
  else
    render :new, status: :unprocessable_entity
  end
end
```

`if @contract.save` usa o retorno do `save` — `true` ou `false` — como
condição. Deu certo: redireciona para a página do contrato. Não deu: mostra
de novo o formulário, com os erros.

O `begin` não foi reescrito. Ele deixou de ser necessário, porque a falha
que ele capturava virou validação. A regra "código único" mora no model,
onde o console, o script e a API também a encontram.

:::key
Um `begin`/`rescue` num controller quase sempre está tratando uma falha
que deveria ter sido recusada antes. Pergunte: essa exceção é uma regra
de negócio que o model não conhece? Se for, a regra vai para o model, e o
`rescue` sai. O que sobra no controller é o `if` do `save`.
:::

## `render` e `redirect_to`

As duas formas de responder, e não são intercambiáveis.

**`redirect_to`** responde ao navegador: "vá para outro endereço". O
navegador faz um pedido novo, `GET`. Depois de gravar com sucesso, é o
certo: se a pessoa apertar F5, recarrega a página do contrato, e não
reenvia o formulário.

**`render :new`** monta a view `new` **neste mesmo pedido**, com o
`@contract` que está na memória — inclusive os erros e os campos que a
pessoa preencheu. Depois de falhar, é o certo: a pessoa não perde o que
digitou.

O `status: :unprocessable_entity` é o código `422`: o pedido chegou certo e
os dados não passaram. O código de 2021 redirecionava depois de falhar, e
a Helena perdia os oito campos toda vez que esquecia o responsável.

## Quarto: o aviso sai

A última linha de 2021:

```ruby
flash[:alerta] = "Sem responsável" unless @contract.responsible
```

Salvava o contrato sem responsável e mostrava um aviso **depois**. Com a
validação de presença do capítulo @cap:validacoes, o contrato sem
responsável não chega a ser gravado, e o aviso vira a mensagem de erro do
formulário. A linha sai.

`flash` é uma mensagem que sobrevive a um redirecionamento: gravada neste
pedido, mostrada no próximo, apagada depois. O `notice:` do `redirect_to`
é um atalho para `flash[:notice]`.

## O que sobrou

```ruby title="app/controllers/contracts_controller.rb" numbered
class ContractsController < ApplicationController
  before_action :set_contract, only: [:show, :cancel]

  def show
  end

  def create
    @contract = Contract.new(contract_params)
    @contract.status = params[:reserve] ? "reserved" : "active"

    if @contract.save
      redirect_to @contract, notice: "Contrato criado."
    else
      render :new, status: :unprocessable_entity
    end
  end

  def cancel
    @contract.update!(status: "cancelled")
    redirect_to @contract, notice: "Contrato cancelado."
  end

  private

  def set_contract
    @contract = Contract.find(params[:id])
  end

  def contract_params
    params.require(:contract).permit(
      :code, :customer_id, :equipment_id, :site, :responsible,
      :start_date, :end_date, :daily_rate_cents,
    )
  end
end
```

`before_action :set_contract, only: [...]` roda `set_contract` antes das
ações listadas. O `Contract.find` deixa de se repetir. `find` levanta
`RecordNotFound` quando o `id` não existe, e o Rails responde `404`.

O `create` tem sete linhas. Cada uma das trinta e sete correções foi para
algum lugar: a rota, a validação, o callback, o strong parameters. O
commit de hoje foi o trigésimo oitavo, e a mensagem listava para onde
cada uma foi.

:::summary
- Controller lê `params`, chama o model e responde. Variável `@` chega à
  view.
- `require` e `permit` declaram os campos aceitos. `permit!` aceita
  qualquer um.
- `begin`/`rescue` que trata regra de negócio sai quando a regra vira
  validação. Sobra o `if @contract.save`.
- `redirect_to` depois de sucesso; `render` com `422` depois de falha.
- `before_action` tira a repetição. `find` inexistente vira `404`.
:::

:::exercise level=1
Diga o que o navegador mostra, e se o formulário preenchido é preservado,
em cada caso:

1. `create` com sucesso, e a pessoa aperta F5.
2. `create` sem responsável, com `render :new`.
3. `create` sem responsável, com `redirect_to new_contract_path`.

:::answer
1. A página do contrato de novo. O F5 repete o `GET` do redirecionamento,
   não o `POST`.
2. O formulário, com os campos preenchidos e a mensagem de erro no
   responsável.
3. O formulário vazio. O redirecionamento é um pedido novo, e o `@contract`
   com os dados ficou no pedido anterior.
:::

:::exercise level=2
O Diego monta à mão um pedido `POST /contracts` com
`contract[status]=closed`. O que acontece com o controller novo, e o que
acontecia com o de 2021?

:::answer
Com o controller novo, `status` não está no `permit`, e é descartado. O
contrato é criado `active` ou `reserved`, pelo `params[:reserve]`.

Com o de 2021, o `permit!` aceitava o `status`, e a linha seguinte o
sobrescrevia com `"active"`, a menos que viesse `reserve`. Por sorte, o
`status` não passava. Mas `cancelled_at`, `created_by` e
`daily_rate_cents` passavam — inclusive uma diária de zero centavos.
:::

:::exercise level=3
A Marta quer que o `create` avise a Helena por e-mail. O Sérgio sugere pôr
`ContractMailer.new_contract(@contract).deliver_now` dentro do
`if @contract.save`, antes do `redirect_to`, "que é o lugar em que o
contrato já está salvo". Diga o que acontece quando o servidor de e-mail
demora ou falha, e o que você proporia até o capítulo de jobs.

:::answer
`deliver_now` manda o e-mail durante o pedido. Se o servidor de e-mail
demora oito segundos, a Helena espera oito segundos para ver o contrato
criado. Se falha, a exceção sobe e a Helena vê a página de erro — com o
contrato **já gravado**. Ela tenta de novo, e a validação de código único
recusa, ou, se o código for gerado, cria o segundo.

Até o capítulo de jobs, a proposta é não mandar e-mail no pedido: a
Helena já vê o contrato na lista da manhã. Quando o job existir, o
controller chama `deliver_later`, que só agenda o envio e responde na hora.
:::
