---
title: "Views"
number: 22
slug: views
part: p5
kicker: "Na mesma linha da tela, a plataforma aparecia sem destaque de ocupada e com o rótulo Em uso. A view fazia a mesma pergunta de dois jeitos."
goal: >-
  Montar a página que a Helena vê com ERB: imprimir e executar, percorrer
  uma lista, quebrar em partial, mostrar os erros do formulário, e fazer a
  view perguntar ao model em vez de refazer a conta.
---

:::story Em uso e livre
Na segunda, 27 de abril, a Helena mandou um print da tela de contratos com
um círculo à caneta digital em volta de uma linha:

> PT-133. Sem o fundo amarelo de ocupada. Mas escrito "Em uso". Qual das
> duas?

A Lívia abriu a partial da linha:

```erb title="app/views/contracts/_linha.html.erb"
<tr class="<%= 'ocupado' if contrato.active? %>">
  <td><%= contrato.equipment.patrimony %></td>
  <td><%= contrato.status == "active" ? "Em uso" : "Livre" %></td>
</tr>
```

— O fundo pergunta `active?` — disse ela. — O rótulo compara o status.

— E o `active?` olha a data de fim — disse o Caio. — O CT-1987 venceu na
sexta. O status continua `active`, porque a PT-133 não voltou.

— Então o fundo diz que acabou, e o rótulo diz que não.

— A linha diz as duas coisas — disse o Caio. — Ao mesmo tempo.
:::

## ERB

A view é HTML com Ruby dentro. O formato se chama ERB — *Embedded Ruby* —,
e o arquivo termina em `.html.erb`. Duas marcas:

```erb
<% contratos = @contracts.first(3) %>
<p>Contratos: <%= @contracts.size %></p>
```

`<% ... %>` **executa** o Ruby e não escreve nada na página. `<%= ... %>`
executa e **escreve** o valor. O sinal de igual é a diferença, e esquecê-lo
é o erro mais comum: a conta é feita, e nada aparece.

A view recebe as variáveis de instância do controller. O `@contracts` que
o `index` preencheu está aqui, sem nenhuma linha de ligação — outra
convenção do capítulo @cap:o-que-e-o-rails.

## Percorrer a lista

```erb title="app/views/contracts/index.html.erb" numbered
<h1>Contratos em uso</h1>

<table>
  <thead>
    <tr><th>Equipamento</th><th>Canteiro</th><th>Devolução</th></tr>
  </thead>
  <tbody>
    <% @contracts.each do |contrato| %>
      <tr>
        <td><%= contrato.equipment.patrimony %></td>
        <td><%= contrato.site %></td>
        <td><%= l(contrato.end_date) %></td>
      </tr>
    <% end %>
  </tbody>
</table>
```

O `each` do capítulo @cap:blocos-e-enumerables, com o bloco aberto numa
marca `<% %>` e fechado noutra. O HTML entre as duas se repete para cada
contrato.

`l(...)` formata a data no idioma da página: `30/06/2026`, pelo mesmo
`pt-BR.yml` do capítulo @cap:validacoes.

:::pitfall
`contrato.equipment.patrimony` dentro do `each`, para trezentos
contratos, faz trezentas consultas de equipamento — uma por linha. A
correção fica no controller, não na view:

```ruby
@contracts = Contract.current.includes(:equipment)
```

A view não sabe quantas consultas faz. Quem monta a lista precisa saber o
que a view vai perguntar.
:::

## O que o `<%= %>` escapa

`<%= %>` não escreve o valor cru. Ele troca os caracteres que o HTML
entende como marcação — `<`, `>`, `&`, as aspas — por formas inofensivas.
Um responsável cadastrado como `<script>alert(1)</script>` aparece na tela
como texto, e não roda.

Isso é o que protege a página da Serra Azul de um campo preenchido com
código por alguém de má-fé. Existe a forma de desligar a proteção,
`raw(...)` e `.html_safe`. A casa não usa em valor que veio de cadastro.

## Partial

A linha da tabela aparece em três páginas: contratos, ocupação e a página
do equipamento. Um pedaço de view reaproveitado é uma **partial**, e o
nome do arquivo começa com sublinhado:

```erb title="app/views/contracts/_linha.html.erb"
<tr>
  <td><%= contrato.equipment.patrimony %></td>
  <td><%= contrato.site %></td>
</tr>
```

```erb title="app/views/contracts/index.html.erb"
<% @contracts.each do |contrato| %>
  <%= render "linha", contrato: contrato %>
<% end %>
```

`render "linha", contrato: contrato` monta `_linha.html.erb` e entrega a
ela uma variável local, `contrato`. A partial não enxerga as variáveis do
`each`; ela recebe o que foi passado.

## A mesma pergunta, num lugar só

A linha da PT-133 perguntava "está em uso?" duas vezes, com duas regras:
`active?`, que olha status e data; e `status == "active"`, que olha só o
status. Quando as duas concordam, ninguém nota. Quando o contrato vence e
a máquina não volta, elas discordam na mesma linha.

E há uma terceira resposta, que a Helena deu no capítulo
@cap:condicionais: vencido e ainda não devolvido **continua ocupando**.
Nenhuma das duas da view sabia disso.

A regra vai para o model, uma vez, com o nome que a Helena usaria:

```ruby title="app/models/contract.rb" numbered
def occupying?(hoje = Date.current)
  return false unless status == "active"

  end_date >= hoje || returned_at.nil?
end

def overdue?(hoje = Date.current)
  occupying?(hoje) && end_date < hoje
end
```

E a view só pergunta:

```erb title="app/views/contracts/_linha.html.erb" numbered
<tr class="<%= 'ocupado' if contrato.occupying? %>">
  <td><%= contrato.equipment.patrimony %></td>
  <td><%= rotulo_de_ocupacao(contrato) %></td>
</tr>
```

O texto do rótulo sai de um **helper**, um método que as views podem
chamar:

```ruby title="app/helpers/contracts_helper.rb" numbered
module ContractsHelper
  def rotulo_de_ocupacao(contrato)
    if contrato.overdue?
      "Em uso, devolução atrasada"
    elsif contrato.occupying?
      "Em uso"
    else
      "Livre"
    end
  end
end
```

Um helper é um módulo — o capítulo @cap:modulos — que o Rails inclui nas
views. Ele guarda a lógica **de apresentação**: qual texto, qual classe de
CSS. A regra de negócio — o que é ocupar — fica no model. O helper só a
pergunta.

:::key
A view pergunta; ela não calcula a regra. Toda comparação de `status`
escrita numa view é uma segunda versão de uma regra que já existe, ou
devia existir, no model. Quando a regra muda, a view não é avisada.
:::

A linha da PT-133 passou a dizer, com o fundo amarelo, "Em uso, devolução
atrasada". A Helena respondeu com um polegar e, dez minutos depois, com
outra pergunta: se dava para essa linha vir no topo. Dava: `sort_by`, no
controller.

## Os erros do formulário

O `render :new` do capítulo @cap:controllers devolve o formulário com o
`@contract` que falhou. A view mostra os erros:

```erb title="app/views/contracts/new.html.erb" numbered
<%= form_with model: @contract do |f| %>
  <% if @contract.errors.any? %>
    <div class="erros">
      <% @contract.errors.full_messages.each do |msg| %>
        <p><%= msg %></p>
      <% end %>
    </div>
  <% end %>

  <%= f.label :responsible %>
  <%= f.text_field :responsible %>

  <%= f.label :end_date %>
  <%= f.date_field :end_date %>

  <%= f.submit "Salvar contrato" %>
<% end %>
```

`form_with model: @contract` monta o formulário para aquele registro: o
endereço e o verbo certos — `POST /contracts` para um novo, `PATCH` para um
existente —, e os campos já preenchidos com o que o `@contract` tem. É por
isso que o `render` preserva o que a Helena digitou.

`f.label :responsible` escreve o rótulo com a tradução do `pt-BR.yml`:
"Responsável no canteiro". O mesmo arquivo serve à mensagem de erro e ao
rótulo do campo.

:::summary
- `<% %>` executa; `<%= %>` executa e escreve. A view recebe as variáveis
  `@` do controller.
- `<%= %>` escapa HTML. `raw` e `html_safe` desligam, e não se usam em dado
  de cadastro.
- Partial começa com `_` e recebe variáveis locais pelo `render`.
- A view pergunta ao model. A regra — o que é ocupar — mora no model; o
  texto e a classe de CSS, num helper.
- `form_with model:` monta endereço, verbo e valores; `errors` mostra o que
  falhou.
:::

:::exercise level=1
Diga o que cada linha produz na página, para um contrato com responsável
`"Rogério"`:

```erb
<% contrato.responsible %>
<%= contrato.responsible %>
<%= contrato.responsible.upcase if contrato.occupying? %>
```

:::answer
Nada; `Rogério`; e `ROGÉRIO` se o contrato estiver ocupando, ou nada se não
estiver.

A primeira executa e não escreve: o sinal de igual faltou. A terceira usa
o modificador do capítulo @cap:condicionais, e um `if` falso devolve
`nil`, que o `<%= %>` escreve como vazio.
:::

:::exercise level=2
A página do equipamento mostra "Disponível" ou "Ocupado" com esta linha:

```erb
<%= @equipment.contracts.any? { |c| c.status == "active" } ?
    "Ocupado" : "Disponível" %>
```

Aponte os dois problemas e reescreva.

:::answer
O primeiro: a view refaz a regra de ocupação, e de um terceiro jeito —
qualquer contrato `active`, sem data. Um contrato vencido e devolvido com
status desatualizado prende a máquina.

O segundo: `any?` com bloco carrega todos os contratos da máquina para a
memória, os catorze da PT-121.

```erb
<%= @equipment.available? ? "Disponível" : "Ocupado" %>
```

O `available?` do capítulo @cap:associacoes pergunta ao banco com o
escopo. Para que ele concorde com a partial, o escopo `current` passa a
usar a mesma regra do `occupying?` — um lugar só, de novo.
:::

:::exercise level=3
A Marta quer que a página da Serra Azul, que ainda vai existir, mostre a
mesma linha de contrato, mas **sem** o valor da diária, que é informação
interna. O Sérgio propõe copiar a partial para `_linha_cliente.html.erb` e
apagar a coluna. Diga o que acontece com essa cópia em três meses, e o que
você faria.

:::answer
Em três meses, a regra de ocupação muda de novo — um status novo, um caso
do Diego —, alguém corrige a `_linha.html.erb` e não sabe que existe a
`_linha_cliente.html.erb`. A Serra Azul passa a ver uma coisa e a Helena
outra, que é a multa de R$ 1.800 pelo lado da tela.

O que eu faria: uma partial só, que recebe o que mostrar.

```erb
<%= render "linha", contrato: contrato, interno: false %>
```

```erb
<% if local_assigns.fetch(:interno, true) %>
  <td><%= reais(contrato.daily_rate_cents) %></td>
<% end %>
```

`local_assigns` guarda as variáveis locais que a partial recebeu. O
`fetch` com padrão `true` mantém as páginas antigas iguais. A diferença
entre as duas telas fica visível, numa linha, e a regra de ocupação
continua num lugar só.
:::
