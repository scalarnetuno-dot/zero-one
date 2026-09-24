---
title: "Gems e Bundler"
number: 13
slug: gems-e-bundler
part: p3
kicker: "Um bundle update sem nome de gem mexeu em quarenta e uma linhas do Gemfile.lock. A página de contratos parou de abrir, e só na máquina da Lívia."
goal: >-
  Usar uma biblioteca de terceiros, ler o Gemfile e o Gemfile.lock,
  entender o que o ~> promete, distinguir bundle install de bundle update,
  e rodar o nortea na sua máquina sem trocar o Ruby do servidor.
---

:::story Quarenta e uma linhas
Na sexta, 27 de março, a Lívia clonou o `nortea` pela primeira vez. O
primeiro comando parou:

```text
$ bundle install
Your Ruby version is 3.4.0, but your Gemfile specified ~> 3.3.0
```

— O Gemfile pede o três ponto três — disse o Caio. — Instala o três ponto
três do lado. Não mexe na linha.

Ela instalou. O `bundle install` passou, a página de contratos abriu. À
tarde, a leitura da planilha deu um aviso de depreciação, e ela fez o que
a mensagem sugeria:

```text
$ bundle update
```

A página de contratos não abriu mais. O `git status` mostrava uma
alteração só: `Gemfile.lock`, quarenta e uma linhas.

— Você atualizou tudo — disse o Caio. — O servidor não. Se isso sobe, a
manhã de segunda é essa tela.

— Como volto?

— O lock está no Git.
:::

## Gem

Uma **gem** é uma biblioteca Ruby empacotada, com nome e versão. O
capítulo @cap:fevereiro-de-1993 contou de onde vieram: o RubyGems, em
2004. Elas moram em <https://rubygems.org>, e o comando `gem` instala
uma:

```text
$ gem install roo
Successfully installed roo-2.10.1
```

O `roo` lê planilhas do Excel. Com ele, a `patio` para de depender do
arquivo que o Sérgio exportava à mão:

```ruby title="planilha.rb" numbered
# frozen_string_literal: true

require "roo"

planilha = Roo::Spreadsheet.open("patio_SEMANAL.xlsx")
aba = planilha.sheet(0)

aba.each(contrato: "Contrato", patrimonio: "Patrimônio") do |linha|
  puts "#{linha[:patrimonio]} -> #{linha[:contrato]}"
end
```

`require "roo"` carrega a gem. `Roo::Spreadsheet` é o nome completo —
módulo e classe, a forma do capítulo @cap:modulos. O `each` da aba recebe
um hash dizendo qual coluna vira qual chave: o problema das chaves de texto
do capítulo @cap:arrays-e-hashes, resolvido na leitura.

## O problema que o `gem install` não resolve

`gem install roo` instalou a versão mais nova **na sua máquina**. O
servidor pode ter outra. O computador do Caio, outra. E o `roo` depende de
outras gems — `rubyzip`, `nokogiri` —, que também têm versões.

Um programa que funciona com o `roo` 2.10 e o `rubyzip` 2.3 pode não
funcionar com o `rubyzip` 3.0. Se cada máquina instala o que achar, cada
máquina roda um programa diferente.

## `Gemfile` e `Gemfile.lock`

O Bundler resolve isso com dois arquivos. O `Gemfile` é o pedido, escrito
por gente:

```ruby title="Gemfile" numbered
source "https://rubygems.org"

ruby "~> 3.4.0"

gem "roo", "~> 2.10"
```

`source` diz de onde baixar. `ruby` diz qual Ruby o projeto aceita. Cada
`gem` é uma dependência, com a faixa de versões aceitas.

```text
$ bundle install
Resolving dependencies...
Fetching rubyzip 2.3.2
Fetching roo 2.10.1
Bundle complete! 1 Gemfile dependency, 4 gems now installed.
```

O Bundler resolve o pedido — acha versões de todas as gems, inclusive as
dependências das dependências, que combinem entre si — e grava o
resultado no `Gemfile.lock`:

```text title="Gemfile.lock"
GEM
  remote: https://rubygems.org/
  specs:
    nokogiri (1.18.3-x64-mingw-ucrt)
      racc (~> 1.4)
    racc (1.8.1)
    roo (2.10.1)
      nokogiri (~> 1)
      rubyzip (>= 1.3.0, < 3.0.0)
    rubyzip (2.3.2)
```

O lock não é para ser editado à mão. É a fotografia do que foi resolvido,
com a versão **exata** de cada gem. Quem rodar `bundle install` numa
máquina com esse lock recebe essas versões, e não as mais novas.

:::key
O `Gemfile` diz o que o projeto aceita. O `Gemfile.lock` diz o que o
projeto usa. Os dois vão para o Git. Sem o lock no repositório, duas
máquinas com o mesmo `Gemfile` podem rodar programas diferentes.
:::

## O `~>`

A faixa mais comum no `Gemfile` é o `~>`, chamado de operador pessimista:

| Escrito | Aceita | Não aceita |
|---|---|---|
| `"~> 2.10"` | 2.10, 2.11, 2.99 | 3.0 |
| `"~> 2.10.1"` | 2.10.1, 2.10.9 | 2.11 |
| `">= 2.10"` | qualquer coisa a partir da 2.10 | nada abaixo |

Tabela: O `~>` libera o último número escrito e trava os anteriores.

A convenção que a maioria das gems segue — a versão semântica — promete
que mudança no primeiro número pode quebrar quem usa; no segundo, só
acrescenta; no terceiro, só corrige. `"~> 2.10"` aceita correções e
acréscimos, e recusa o que pode quebrar.

O `ruby "~> 3.3.0"` do `nortea` é o mesmo operador: aceita qualquer 3.3,
recusa o 3.4. Foi o que parou a Lívia no primeiro comando.

## `bundle install` e `bundle update`

Os dois comandos parecem sinônimos, e fazem coisas opostas.

**`bundle install`** instala o que está no lock. Se o lock existe e
satisfaz o `Gemfile`, ele não resolve nada de novo: só baixa as versões
gravadas. É o comando do dia a dia, e o do servidor.

**`bundle update`** ignora o lock, resolve tudo de novo com as versões mais
novas que o `Gemfile` aceitar, e reescreve o lock. Sem nome de gem, faz
isso com **todas**. Foi o comando da Lívia: quarenta e uma linhas, entre
elas o `rack`, de uma versão do meio da faixa para a última, com uma
mudança de comportamento que o controller de contratos não esperava.

Para atualizar uma gem só:

```text
$ bundle update roo --conservative
```

Com o nome, só o `roo` é resolvido de novo. Com `--conservative`, as
dependências dele só mudam se for inevitável. O `git diff` do lock mostra
duas ou três linhas, não quarenta.

E para desfazer o que foi feito:

```text
$ git checkout Gemfile.lock
$ bundle install
```

O lock volta à versão do repositório, e o `install` reinstala o que ele
diz.

:::pitfall
Dentro de um projeto com Gemfile, rode os comandos das gems com
`bundle exec`:

```text
$ bundle exec rspec
$ bundle exec rails server
```

Sem ele, o terminal chama a versão mais nova da gem instalada na máquina,
que pode não ser a do lock. O sintoma é um erro que o Caio não consegue
reproduzir no computador dele, porque lá só existe uma versão instalada.
:::

## Dois Rubys na mesma máquina

O `nortea` exige 3.3. A `patio` usa 3.4. As duas pastas estão no
computador da Lívia.

A solução é um **gerenciador de versões do Ruby**: um programa que instala
várias linhas lado a lado e escolhe qual usar em cada pasta, lendo um
arquivo chamado `.ruby-version`:

```text
$ cat nortea/.ruby-version
3.3.6
$ cat patio/.ruby-version
3.4.1
```

No macOS e no Linux, o mais comum é o `rbenv`. No Windows, a Nortea usa o
WSL — o Linux que roda dentro do Windows —, com `rbenv` dentro dele,
porque o servidor também é Linux e as gems com código em C se comportam
como lá. O Caio passou a tarde de sexta com a Lívia nessa instalação.

```text
$ cd nortea && ruby -v
ruby 3.3.6 (2024-11-05 revision 75015d4c1f) [x86_64-linux]
$ cd ../patio && ruby -v
ruby 3.4.1 (2024-12-25 revision 48d4efcb85) [x86_64-linux]
```

É a resposta ao "não mexe no três ponto três" do capítulo
@cap:primeiro-programa: cada pasta chama o seu.

:::milestone
Fim da Parte 3. O contrato é uma classe com nome, o cálculo de cobrança
está num módulo que ninguém substitui sem `super`, as falhas da manhã têm
tipo e mensagem, e a planilha é lida por uma gem com versão travada. O
`nortea` roda na máquina da Lívia, com o Ruby dele. A próxima parte abre
o que está dentro dele.
:::

:::summary
- Gem é biblioteca com nome e versão. `require` a carrega.
- `Gemfile` é o pedido; `Gemfile.lock` é o resolvido, com versões exatas.
  Os dois vão para o Git.
- `~> 2.10` aceita até antes da 3.0; `~> 2.10.1`, até antes da 2.11.
- `bundle install` instala o lock. `bundle update` sem nome reescreve tudo;
  com nome e `--conservative`, só o necessário.
- `bundle exec` roda a versão do lock. `.ruby-version` e um gerenciador
  deixam cada pasta com o seu Ruby.
:::

:::exercise level=1
Para cada faixa, diga se a versão 2.11.0 é aceita:

```ruby
gem "roo", "~> 2.10"
gem "roo", "~> 2.10.1"
gem "roo", ">= 2.10", "< 2.11"
```

:::answer
Sim, não, não.

`~> 2.10` libera o segundo número: 2.11 entra. `~> 2.10.1` libera o
terceiro: aceita 2.10.x e para antes da 2.11. A terceira faixa é escrita
por extenso e exclui a 2.11 com o `<`.
:::

:::exercise level=2
A Lívia precisa de uma correção de segurança do `nokogiri` no `nortea`.
Escreva os comandos, em ordem, desde a atualização até conferir que só o
necessário mudou.

:::answer
```text
$ bundle update nokogiri --conservative
$ git diff Gemfile.lock
$ bundle exec rspec
```

O `update` com nome e `--conservative` resolve só o `nokogiri`. O `diff`
do lock deve mostrar poucas linhas: a do `nokogiri` e, no máximo, a de uma
dependência dele. Se mostrar quarenta, alguma coisa foi resolvida de novo
sem necessidade, e vale entender por quê antes de seguir.

Os testes rodam com `bundle exec`, na versão do lock. O lock alterado vai
para o Git junto com a explicação de por que mudou.
:::

:::exercise level=3
O Sérgio propõe tirar o `Gemfile.lock` do Git do `nortea` "porque vive dando
conflito quando duas pessoas mexem". Responda com o que passaria a
acontecer no servidor e nas máquinas, e com o que resolve o conflito sem
perder o lock.

:::answer
Sem o lock no repositório, cada `bundle install` resolve do zero com as
versões mais novas que o `Gemfile` aceita. O servidor, no próximo deploy,
instala versões que ninguém testou. A máquina de quem clonou ontem e a de
quem clonou hoje rodam programas diferentes. A falha da Lívia de sexta
passa a acontecer no servidor, às 6h, sem ninguém ter rodado `update`.

O conflito no lock quase sempre vem de duas pessoas atualizando gems em
ramos diferentes. O que resolve: atualizar gem num commit separado, com
nome da gem e `--conservative`, e, quando o conflito aparecer, não editar
o lock à mão — aceitar a versão de um dos lados e rodar `bundle install`
para o Bundler reconciliar.
:::
