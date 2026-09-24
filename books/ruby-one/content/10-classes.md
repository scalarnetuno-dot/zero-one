---
title: "Classes"
number: 10
slug: classes
part: p3
kicker: "O hash aceitava qualquer chave, inclusive statsu. Durante dois dias, o contrato CT-2058 esteve ativo e sem status ao mesmo tempo."
goal: >-
  Transformar o hash do contrato numa classe com nome: initialize, variável
  de instância, attr_reader, métodos que perguntam ao próprio objeto, e um
  construtor de classe que lê a linha da planilha.
---

:::story Statsu
Na quinta, 19 de março, o Diego achou o CT-2058 duas vezes na lista da
manhã: uma entre os ativos, outra entre os sem status.

A Lívia procurou no código da `patio` e achou em cinco minutos:

```ruby
{ code: "CT-2058", equipment: "BT-051", statsu: "active" }
```

— Erro de digitação num teste que eu fiz à mão — disse ela. — O hash
aceitou.

— O hash aceita qualquer coisa — disse o Renato. — É para isso que ele
serve.

— Então o contrato não devia ser um hash.

O Renato demorou a responder, o que nele era concordar.

— Faz a classe. Pequena. Sem Rails. Quero ver o que o Rails vai fazer de
diferente quando a gente chegar lá.
:::

## `class` e `new`

Uma classe é o molde de um tipo de objeto. O capítulo
@cap:objetos-e-tipos perguntou `480.class` e ouviu `Integer`: o Ruby já
tem as dele. Esta é a primeira da Nortea:

```ruby title="contrato.rb" numbered
# frozen_string_literal: true

class Contrato
end

c = Contrato.new
puts c.class
```

```text
$ ruby contrato.rb
Contrato
```

`class Contrato ... end` define a classe. O nome começa com maiúscula e,
se tiver mais de uma palavra, cada uma começa com maiúscula:
`ContratoDeLocacao`. `Contrato.new` cria um objeto dessa classe — uma
**instância**.

## `initialize` e a variável de instância

Uma instância vazia não serve. O contrato nasce com código, patrimônio,
datas e status:

```ruby title="contrato.rb" numbered
# frozen_string_literal: true

require "date"

class Contrato
  def initialize(codigo:, patrimonio:, inicio:, fim:, status:)
    @codigo = codigo
    @patrimonio = patrimonio
    @inicio = inicio
    @fim = fim
    @status = status
  end
end

c = Contrato.new(
  codigo: "CT-2041",
  patrimonio: "PT-118",
  inicio: Date.new(2026, 3, 3),
  fim: Date.new(2026, 6, 30),
  status: "active",
)
```

`initialize` é o método que o `new` chama. Os argumentos passados ao `new`
chegam a ele.

`@codigo` é uma **variável de instância**: o `@` diz que o nome pertence ao
objeto, não ao método. A variável local `codigo` some quando o
`initialize` termina. `@codigo` fica guardada na instância enquanto ela
existir.

E o erro de digitação agora tem onde parar:

```ruby
Contrato.new(codigo: "CT-2058", patrimonio: "BT-051",
             inicio: hoje, fim: fim, statsu: "active")
```

```text
contrato.rb:6:in 'initialize': missing keyword: :status
(ArgumentError)
```

O `status` certo faltou, e o Ruby diz qual. Com o `status` presente e o
`statsu` sobrando, a mensagem seria `unknown keyword: :statsu`. A classe
declara o que o contrato **é**: uma chave que falta não passa, e uma que
não faz parte dele não entra.

:::term Instância
Um objeto criado a partir de uma classe com `new`. Cada instância tem as
suas próprias variáveis de instância — os `@nome`.

Dois contratos da mesma classe têm os mesmos métodos e valores próprios.
:::

## Ler de fora: `attr_reader`

As variáveis de instância são do objeto. De fora, não se lê `c.@codigo`.
Para expor um valor, a classe define um método que o devolve:

```ruby
def codigo
  @codigo
end
```

Como isso se repete para cada campo, o Ruby tem um atalho:

```ruby title="contrato.rb" numbered
class Contrato
  attr_reader :codigo, :patrimonio, :inicio, :fim, :status

  def initialize(codigo:, patrimonio:, inicio:, fim:, status:)
    # ... como antes
  end
end

puts c.codigo
puts c.fim
```

```text
CT-2041
2026-06-30
```

`attr_reader :codigo` escreve o método `codigo` por você. Os nomes vêm
como símbolos — são nomes de método, o uso que o capítulo
@cap:strings-e-simbolos reservou para eles.

Existe `attr_writer`, que cria o método para atribuir, e `attr_accessor`,
que cria os dois. A casa começa com `attr_reader`. Um contrato cujo
`status` qualquer um pode trocar de fora com `c.status = "x"` volta a ser
um hash com outro nome.

## Métodos que perguntam ao objeto

O `ativo?` do capítulo @cap:metodos recebia status e datas de fora. Dentro
da classe, ele pergunta ao próprio objeto:

```ruby title="contrato.rb" numbered
class Contrato
  attr_reader :codigo, :patrimonio, :inicio, :fim, :status

  def initialize(codigo:, patrimonio:, inicio:, fim:, status:)
    @codigo = codigo
    @patrimonio = patrimonio
    @inicio = inicio
    @fim = fim
    @status = status
  end

  def ativo?(hoje = Date.today)
    status == "active" && fim >= hoje
  end

  def cancelado?
    status == "cancelled"
  end

  def to_s
    "#{codigo} (#{patrimonio}) até #{fim.strftime('%d/%m')}"
  end
end
```

`status` e `fim`, dentro de `ativo?`, são chamadas aos métodos que o
`attr_reader` criou. O objeto responde a si mesmo.

`to_s` é o método que o Ruby chama quando precisa do objeto como texto —
no `puts`, na interpolação. Sem ele, o `puts` mostraria algo como
`#<Contrato:0x000...>`. Com ele:

```ruby
puts c
```

```text
CT-2041 (PT-118) até 30/06
```

`strftime('%d/%m')` formata a data: dia e mês com dois dígitos.

## Duas instâncias, mesma classe

```ruby title="dois.rb" numbered
hoje = Date.new(2026, 3, 19)

a = Contrato.new(codigo: "CT-2041", patrimonio: "PT-118",
                 inicio: Date.new(2026, 3, 3),
                 fim: Date.new(2026, 6, 30), status: "active")
b = Contrato.new(codigo: "CT-2012", patrimonio: "PT-118",
                 inicio: Date.new(2026, 1, 5),
                 fim: Date.new(2026, 3, 2), status: "active")

puts a.ativo?(hoje)
puts b.ativo?(hoje)
```

```text
true
false
```

Os dois contratos são da mesma plataforma e da mesma classe. O método
`ativo?` é o mesmo código. A resposta é diferente porque cada instância
tem o seu `@fim`. É o que o hash também fazia — e o que ele não fazia era
recusar `statsu`.

## Um construtor de classe: `self.`

A planilha entra como hash de texto. O capítulo @cap:arrays-e-hashes tinha
uma função solta, `da_planilha`. Ela pode morar na classe:

```ruby title="contrato.rb" numbered
class Contrato
  def self.da_planilha(linha)
    new(
      codigo: linha.fetch("Contrato").strip,
      patrimonio: linha.fetch("Patrimônio").strip.upcase,
      inicio: Date.strptime(linha.fetch("Saída"), "%d/%m/%Y"),
      fim: Date.strptime(linha.fetch("Devolução"), "%d/%m/%Y"),
      status: "active",
    )
  end
end

c = Contrato.da_planilha(linha)
```

`def self.da_planilha` define um método **da classe**, não da instância.
Ele é chamado em `Contrato`, não num contrato. Dentro dele, `new` é
`Contrato.new`.

A planilha não tem coluna de status: se a linha está lá, o Seu Nestor
considera o contrato em uso. O `status: "active"` registra essa regra em
um lugar, com nome, em vez de espalhá-la.

:::pitfall
`self.` na frente do nome muda de quem o método é. Sem ele,
`def da_planilha` seria um método de instância, e `Contrato.da_planilha`
daria `NoMethodError: undefined method 'da_planilha' for class Contrato`.

A mensagem diz `for class Contrato`: o Ruby procurou o método na classe, e
ele estava nas instâncias.
:::

:::summary
- `class Nome ... end` define o molde; `Nome.new` cria uma instância e chama
  `initialize`.
- `@nome` é variável de instância: pertence ao objeto e dura enquanto ele
  existir.
- `attr_reader` cria os métodos de leitura. `attr_accessor` também deixa
  escrever de fora, e a casa não começa por ele.
- Argumento com nome no `initialize` recusa a chave errada e a que falta.
- `to_s` é o texto do objeto. `def self.nome` é método da classe.
:::

:::exercise level=1
Acrescente à classe o método `dias(hoje)`, que devolve quantos dias
faltam até o fim do contrato. Use `(fim - hoje).to_i`.

:::answer
```ruby
def dias(hoje = Date.today)
  (fim - hoje).to_i
end
```

A subtração de duas datas devolve um número racional de dias — `(103/1)` —,
e `to_i` o transforma em inteiro. Para o contrato que vence em 30 de junho,
consultado em 19 de março, são 103 dias. Para um vencido, o número é
negativo, e quem chama decide o que isso significa.
:::

:::exercise level=2
A Lívia quer poder escrever `c.status = "cancelled"`. Escreva um método
`cancelar!` em vez de um `attr_writer`, e diga o que ele pode fazer que o
`attr_writer` não faria.

:::answer
```ruby
def cancelar!
  raise "contrato #{codigo} já cancelado" if cancelado?

  @status = "cancelled"
end
```

O `!` avisa que o método altera o objeto, a convenção do capítulo
@cap:strings-e-simbolos.

O método pode recusar a operação — cancelar duas vezes —, e tem nome de
ação: quem lê `c.cancelar!` sabe o que aconteceu. O `attr_writer` aceita
qualquer valor, inclusive `"calcelled"`, e não sabe a diferença entre
cancelar e corrigir um erro de digitação.
:::

:::exercise level=3
A planilha tem uma linha sem a coluna "Devolução" — contrato sem data de
fim, que o Seu Nestor chama de "até segunda ordem". O que
`Contrato.da_planilha` faz com ela hoje, e como você mudaria a classe para
aceitá-la sem deixar `ativo?` quebrar?

:::answer
Hoje, `linha.fetch("Devolução")` levanta `KeyError` e a linha para.

Para aceitar, a leitura passa a tolerar a ausência, e a classe passa a
tratar `fim` nulo:

```ruby
devolucao = linha["Devolução"]
fim = devolucao && Date.strptime(devolucao, "%d/%m/%Y")
```

```ruby
def ativo?(hoje = Date.today)
  status == "active" && (fim.nil? || fim >= hoje)
end
```

`devolucao && ...` só converte se houver texto; senão, `fim` fica `nil`. E
`ativo?` diz explicitamente o que "até segunda ordem" significa: sem fim,
continua ativo. Sem essa linha, `nil >= hoje` levantaria `NoMethodError` na
primeira chamada.

`to_s` também precisa do cuidado: `fim.strftime` num `nil` quebra.
:::
