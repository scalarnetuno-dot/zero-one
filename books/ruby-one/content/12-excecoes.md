---
title: "Exceções"
number: 12
slug: excecoes
part: p3
kicker: "A lista da manhã saiu vazia. Não havia erro nenhum no log. Havia um rescue que devolvia uma lista vazia quando não achava o arquivo."
goal: >-
  Ler uma falha pelo tipo, capturar só o que se sabe tratar, criar a
  exceção da Nortea com o dado que quem captura precisa, e usar ensure para
  o que tem de acontecer com ou sem falha.
---

:::story Nenhuma divergência
Na quarta, 25 de março, a lista de divergências das 7h saiu com uma
linha:

```text
Nenhuma divergência entre planilha e sistema.
```

A Marta mandou um joinha. A Helena mandou uma foto do quadro do pátio com
três plataformas riscadas à caneta.

A Lívia abriu o script. O Sérgio, na terça à noite, tinha salvado a
planilha com outro nome — `patio_SEMANAL (1).xlsx` —, porque o Excel não
deixou sobrescrever a aberta. O script procurava o nome antigo, e a
leitura estava assim:

```ruby
def ler_planilha(caminho)
  begin
    Planilha.ler(caminho)
  rescue
    []
  end
end
```

— Sem arquivo, lista vazia — disse ela. — Lista vazia, nenhuma
divergência.

— Nenhuma mentira também — disse o Caio. — A lista estava mesmo vazia.

— A planilha não.

— Não. A planilha, não.
:::

## A falha tem tipo

Os capítulos anteriores já mostraram várias: `NameError`, `NoMethodError`,
`TypeError`, `ArgumentError`, `KeyError`. Cada uma é uma **exceção**: um
objeto que o Ruby cria quando uma operação não pode continuar, e que
interrompe o programa até alguém tratá-lo.

Toda exceção é uma instância de uma classe, e as classes formam uma árvore:

```text
Exception
  StandardError
    ArgumentError
    KeyError
    NameError
      NoMethodError
    TypeError
    ZeroDivisionError
    IOError
    SystemCallError
      Errno::ENOENT
```

`Errno::ENOENT` é o arquivo que não existe. É a que o script do Sérgio
recebeu:

```text
$ ruby lista.rb
lista.rb:4:in 'IO.read': No such file or directory
@ rb_sysopen - patio_SEMANAL.xlsx (Errno::ENOENT)
  from lista.rb:4:in '<main>'
```

A mensagem tem o arquivo, a linha, o tipo e o nome do arquivo procurado.
Tudo que a Lívia precisou descobrir na quarta estava nessa linha, se ela
tivesse chegado a ser escrita.

## `begin`, `rescue`

Tratar uma exceção é dizer o que fazer quando ela acontecer:

```ruby title="lista.rb" numbered
begin
  conteudo = File.read("patio_SEMANAL.xlsx")
rescue Errno::ENOENT => e
  puts "Planilha não encontrada: #{e.message}"
  exit 1
end
```

O Ruby executa o `begin`. Se uma exceção do tipo nomeado acontecer ali
dentro, ele pula para o `rescue`. `=> e` guarda o objeto da exceção no nome
`e`, e `e.message` é o texto dela. Se nenhuma exceção acontecer, o
`rescue` é ignorado.

`exit 1` encerra o programa com código de erro. O agendador que roda o
script às 7h sabe ler esse código e avisar alguém. Um script que termina
com `puts` e código zero diz ao agendador que deu tudo certo.

Dentro de um método, o `begin` pode ser dispensado: o corpo do método já
funciona como um.

```ruby
def ler_planilha(caminho)
  Planilha.ler(caminho)
rescue Errno::ENOENT
  raise "planilha não encontrada em #{caminho}"
end
```

## O `rescue` sem tipo

O `rescue` do script não tinha tipo. Sem tipo, ele captura
`StandardError` — quase tudo da árvore acima. Não só o arquivo ausente: o
erro de digitação num nome de método, a coluna que mudou de nome, a data
que não é data.

E o que ele fazia com tudo isso era devolver `[]`. O programa seguia com
uma lista vazia, perfeitamente válida, e o resto do código fez o que se
faz com uma lista vazia: disse que não havia divergência.

:::key
Um `rescue` responde a uma pergunta: **eu sei o que fazer com esta
falha?** Se sim, capture o tipo exato e faça. Se não, deixe subir.

Uma exceção que chega ao topo encerra o programa com a mensagem certa.
Uma exceção capturada e trocada por um valor "neutro" — `[]`, `nil`, `0` —
continua o programa com uma mentira plausível.
:::

A versão que a Lívia deixou:

```ruby title="lista.rb" numbered
def ler_planilha(caminho)
  Planilha.ler(caminho)
rescue Errno::ENOENT
  arquivos = Dir.glob("patio_SEMANAL*.xlsx")
  raise "planilha não encontrada em #{caminho}. " \
        "Na pasta: #{arquivos.join(', ')}"
end
```

Ela captura só o arquivo ausente, e o que faz é levantar outra exceção com
uma mensagem melhor: o que procurou e o que existe na pasta. Na quarta, a
mensagem teria listado `patio_SEMANAL (1).xlsx`. `Dir.glob` devolve os
arquivos que batem com o padrão; o `*` aceita qualquer coisa no lugar.

A barra invertida no fim da linha continua o texto na linha seguinte.

## `raise` e a exceção da Nortea

`raise` com um texto cria um `RuntimeError`. Para falhas do domínio, a
casa cria classes próprias, com o dado que quem captura vai precisar:

```ruby title="erros.rb" numbered
class EquipamentoOcupado < StandardError
  attr_reader :patrimonio, :contrato

  def initialize(patrimonio:, contrato:)
    @patrimonio = patrimonio
    @contrato = contrato
    super("#{patrimonio} já está no contrato #{contrato}")
  end
end
```

`< StandardError` diz que a classe nova é um tipo de `StandardError`: está
na árvore, abaixo dele. A herança de classe aparece aqui pela primeira vez,
e é só isso que ela faz neste capítulo. `super` chama o `initialize` de
`StandardError`, que guarda a mensagem.

```ruby title="reservar.rb" numbered
def reservar(patrimonio, ocupados)
  if ocupados.key?(patrimonio)
    raise EquipamentoOcupado.new(
      patrimonio: patrimonio,
      contrato: ocupados[patrimonio],
    )
  end

  puts "#{patrimonio} reservado"
end

ocupados = { "PT-118" => "CT-2041" }

begin
  reservar("PT-118", ocupados)
rescue EquipamentoOcupado => e
  puts "Não dá: #{e.message}."
  puts "Ligue para o dono do #{e.contrato}."
end
```

```text
$ ruby reservar.rb
Não dá: PT-118 já está no contrato CT-2041.
Ligue para o dono do CT-2041.
```

Quem captura não lê a mensagem para decidir. Lê `e.contrato`. A mensagem é
para gente; os atributos, para o código.

:::term Exceção
Um objeto que interrompe o fluxo quando uma operação não pode continuar.
`raise` cria e lança; `rescue` captura um tipo e decide o que fazer; o que
ninguém captura encerra o programa com a mensagem.

As exceções do seu programa herdam de `StandardError`, nunca de
`Exception` direto.
:::

:::pitfall
`rescue Exception` captura inclusive o que não é erro de programa: o
`Ctrl+C` de quem quer parar o script, o `exit` chamado de dentro, a falta
de memória. Um script com `rescue Exception` não para quando o Sérgio pede
para parar às 6h55. `rescue` sem tipo já é largo demais. `Exception` é
largo o bastante para prender quem opera o sistema.
:::

## `ensure`

Algumas coisas precisam acontecer com ou sem falha. O script da manhã
grava uma trava para que duas execuções não rodem ao mesmo tempo, e precisa
apagá-la no fim:

```ruby title="lista.rb" numbered
File.write("lista.lock", Process.pid.to_s)

begin
  gerar_lista
ensure
  File.delete("lista.lock")
end
```

O `ensure` roda sempre: quando o `begin` termina bem, e quando uma exceção
passa por ele. A exceção continua subindo depois do `ensure` — ele não a
captura. Sem o `ensure`, uma falha no meio deixaria a trava no disco, e a
execução do dia seguinte encontraria a lista "já rodando".

:::summary
- Exceção tem tipo, e o tipo está numa árvore que começa em `Exception` e
  passa por `StandardError`.
- `begin ... rescue Tipo => e ... end` captura um tipo. Num método, o
  `begin` é dispensável.
- `rescue` sem tipo captura quase tudo. Trocar a falha por `[]` ou `nil`
  continua o programa com um valor que mente.
- A exceção da Nortea herda de `StandardError` e carrega atributos. Quem
  captura decide pelos atributos, não pela mensagem.
- `ensure` roda sempre e não captura. `rescue Exception` prende até o
  `Ctrl+C`.
:::

:::exercise level=1
Diga o tipo da exceção de cada linha:

```ruby
{ a: 1 }.fetch(:b)
Integer("PT-118")
nil.upcase
48_000 / 0
```

:::answer
`KeyError`, `ArgumentError`, `NoMethodError` e `ZeroDivisionError`.

A terceira é a mais comum no `nortea`: um valor que devia estar lá e veio
`nil`, recebendo um método que só texto tem.
:::

:::exercise level=2
O script de 2019 do Sérgio tem isto:

```ruby
diaria = Integer(linha["Diária"]) rescue 0
```

O `rescue` no fim da linha é o modificador: captura `StandardError` da
expressão e devolve o valor da direita. Diga o que acontece com uma
diária `"R$ 480"` e escreva a versão que você aceitaria.

:::answer
`Integer("R$ 480")` levanta `ArgumentError`, o modificador captura e a
diária vira `0`. O contrato é cobrado de graça, sem aviso.

```ruby
texto = linha.fetch("Diária")
diaria = Integer(texto.delete("R$ .,"))
```

Sem `rescue`. Se a diária não for número depois da limpeza, o
`ArgumentError` sobe com o texto que falhou, e a linha é corrigida na
planilha. Diária zero não é um valor padrão aceitável.
:::

:::exercise level=3
Escreva `reservar` de modo que, se o equipamento estiver ocupado **por um
contrato cancelado**, a reserva siga — e só levante `EquipamentoOcupado`
quando o contrato que o segura estiver ativo. O hash `ocupados` passa a
ter o status: `{ "PT-118" => { contrato: "CT-2033", status: "cancelled" } }`.

:::answer
```ruby
def reservar(patrimonio, ocupados)
  atual = ocupados[patrimonio]

  if atual && atual.fetch(:status) == "active"
    raise EquipamentoOcupado.new(
      patrimonio: patrimonio,
      contrato: atual.fetch(:contrato),
    )
  end

  puts "#{patrimonio} reservado"
end
```

`atual` é `nil` quando o patrimônio não está no hash, e o `&&` impede a
chamada ao `fetch` num `nil`. O status é lido com `fetch` porque um
registro de ocupação sem status é um dado quebrado, e o capítulo
@cap:blocos-e-enumerables mostrou o que acontece quando o `nil` passa
calado.

Não há `rescue` aqui. Quem decide o que fazer com a exceção é quem chamou
`reservar` — a tela da Helena, o script, o teste.
:::
