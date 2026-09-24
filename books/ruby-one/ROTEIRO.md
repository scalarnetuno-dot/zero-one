# Ruby One — roteiro editorial

**Volume 5 da coleção Zero One.** 29 capítulos numerados em 6 partes, mais
a abertura. Ruby primeiro, Rails depois. A locação de equipamento é o
**cenário**. O enredo é o código do contrato: modelo, método, associação,
callback, controller, console, teste, deploy.

O capítulo de história segue a mesma linha do JavaScript One: o fato
documentado, em ordem, com nome e data. Sem o molde fama / defeito / o que
melhorou.

## O que já está escrito

| Arquivo | Estado |
|---|---|
| `00-antes-de-comecar.md` | escrito |
| `01-fevereiro-de-1993.md` | escrito. História do Ruby e do Rails |
| `02-o-que-vamos-construir.md` | escrito |
| `03-primeiro-programa.md` | escrito |
| `04` a `29` | escritos, seguindo a régua abaixo |

Decisões tomadas na escrita, para manter a coerência:

- O `nortea` roda **Rails 7.2.2** e **Ruby 3.3.6** (`.ruby-version`),
  PostgreSQL, Sidekiq desde 2021, deploy por Capistrano. O prompt do
  console é `nortea(dev)>` / `nortea(prod)>`, e as saídas de hash no
  console do `nortea` usam o formato do 3.3 (`=>`). Na `patio`, 3.4.
- `equipment` já é incontável no Rails; o `inflections.rb` de 2016 só
  repete a regra (cap. 15).
- As três datas: `start_date` = primeiro dia cobrado (faturamento),
  `begin_date` = assinatura/vigência (jurídico, Paula), `started_at` =
  saída do pátio (ocupação, Sérgio). A API expõe `started_at` como
  `chegada`.
- A regra de ocupação mora em `Contract#occupying?` e no escopo
  `occupying_on`: ativo e (dentro do prazo ou não devolvido).
- Contagens citadas: 212 contratos sem status (importação de 2019), 94
  sem responsável, 41 reservas duplicadas em produção, 41 linhas da
  Serra Azul no dia 3.

## O mundo

**Nortea Equipamentos**, Betim. Aluga máquina para construtora: betoneira,
gerador, plataforma elevatória, compactador. Cerca de 430 equipamentos no
pátio. Fundada pelo **Seu Nestor Noronha**. Quem toca a operação é a filha,
**Helena Noronha**. O pátio carrega às 6h.

O sistema em produção é um Rails antigo, repositório `nortea`, no ar desde
**março de 2016**. Ruby **3.3** no servidor. Planilha `patio_SEMANAL.xlsx`
ainda manda: se a tela e a planilha discordam, o caminhão sai pela
planilha. O Seu Nestor acredita na planilha.

A missão é o **Nortea Hub**, começando pelo módulo de contratos, dentro
desse mesmo sistema. Não é um produto novo ao lado. É a parte que reserva
equipamento e que a cliente vai consultar.

### A data e o dinheiro

A **Construtora Serra Azul**, Belo Horizonte, nove canteiros, renova em
**quarta-feira, 3 de junho de 2026**. O contrato de locação vale **R$ 3,6
milhões** por ano. O adendo que o comercial já assinou exige que a Serra
Azul consulte, numa página, qual equipamento está preso a qual contrato.

A cláusula que já existe cobra **R$ 1.800 por dia** em que uma máquina
contratada não está no canteiro. No último trimestre a Nortea pagou cerca
de **R$ 46 mil** dessa multa. Quase sempre o sistema e o pátio diziam
coisas diferentes sobre a mesma plataforma.

| O livro precisa de | O arranjo entrega |
|---|---|
| prazo com data real | 3 de junho de 2026 |
| dinheiro | a renovação de R$ 3,6 milhões e a multa de R$ 1.800 por dia |
| alguém que cobra | a Helena toda manhã; a Marta com o ticket; o Rômulo, que assinou o adendo |
| algo em produção | o Rails de 2016 e a planilha das 6h |

O Ruby 3.3 do servidor: manutenção normal até **1º de abril de 2026**,
correção de segurança até **31 de março de 2027**. Quem lê o livro instala
**Ruby 3.4** (Natal de 2024). O Ruby 4.0 saiu no Natal de 2025. Os
exemplos deste começo usam sintaxe que as duas linhas falam. O servidor
não é atualizado "para a mais nova" no meio da semana do pátio.

A história da sala abre na **quinta, 5 de março de 2026**. A Lívia entrou
na segunda, 2 de março. O acesso ao repositório chegou na sexta, 6 de
março.

### O repositório

```text
nortea/
  Gemfile
  Gemfile.lock
  app/models/contract.rb
  app/models/equipment.rb
  app/controllers/contracts_controller.rb
  app/views/contracts/
  db/schema.rb
  spec/factories/contracts.rb
```

A tabela `contracts` tem vinte e três colunas. Três guardam um começo:

| Coluna | Quem | Quando | Mensagem |
|---|---|---|---|
| `start_date` | Sérgio | março de 2016 | `contrato` |
| `begin_date` | Paula Ribeiro | março de 2019 | `vigência` |
| `started_at` | Sérgio | novembro de 2021 | `temporário` |

Paula saiu em 2021. Não é vilã. As três colunas continuam porque algum
relatório lê cada uma.

O leitor **não clona** esse repositório no capítulo 3. Cria a pasta
`patio/` e escreve Ruby ali. O Rails de produção aparece em trecho, quando
o defeito precisa ser visto.

### Convenção do código novo

Ruby 3.4. Aspas duplas, `snake_case` em método e variável, classe em
`CamelCase`. `frozen_string_literal` só quando o capítulo de strings
explicar o comentário mágico. Recuo de dois espaços. Método que responde
sim ou não termina em `?`. Método que altera o objeto, quando a convenção
pedir, termina em `!` — e o capítulo que usar isso explica na hora.

Tabela `equipment`: o Rails, por padrão, pluralizaria `Equipment` como
`equipments`. O arquivo de 2016 tem uma inflexão que faz a tabela se
chamar `equipment`. Isso é assunto do capítulo de modelos, não da
abertura. Até lá, o texto diz "a tabela de equipamentos" sem mostrar o
nome errado.

## O elenco

- **Lívia** — chegou em 2 de março de 2026. Boa tecnicamente. Ainda está
  aprendendo a convenção da casa. É por onde o leitor entra.
- **Caio** — Ruby há anos. Calmo demais para quem já leu aquele model.
  Explica curto, quando explica.
- **Renato** — tech lead. Quer o código simples e desconfia de abstração
  que a Marta não pediu. A simplicidade, para ele, é uma restrição, não um
  slogan.
- **Marta** — product manager. Conhece o pátio e o contrato. Não tem
  paciência para caixa que não muda o que a Helena confere às 6h.
- **Diego** — QA. Aparece com a combinação que ninguém combinou: cancelar
  enquanto a reserva ainda não voltou, equipamento sem responsável, data
  de devolução anterior à de saída.
- **Sérgio** — mantém partes do sistema de 2016. Solução temporária, para
  ele, é uma forma de respeito ao que está funcionando no pátio. A coluna
  `started_at` é dele, e a mensagem do commit era `temporário`.
- **Helena Noronha** — operação. Não escreve Ruby. Sabe qual plataforma
  está em qual canteiro.
- **Seu Nestor** — pátio, 6h, planilha. Quase não entra na sala.
- **Rômulo** — comercial. Assinou o adendo de 3 de junho. Aparece pouco.
- **Paula Ribeiro** — ausente. A coluna `begin_date` é dela.

## Onde entra cada cena já escrita

A cena abre o capítulo. A aula ocupa o resto.

| Cena | Capítulo | Aula |
|---|---|---|
| `class Contract < ApplicationRecord`, vinte e três campos, três começos | 15 Modelos | Classe Rails, `schema.rb`, e o que uma coluna a mais faz com o objeto. A cena fica inteira. |
| `def active?` que ninguém chama | 05 Métodos | Definir método, o `?` no nome, parêntese opcional, e por que ausência de chamada no arquivo não é ausência de chamada. |
| `belongs_to` / `has_many` e o equipamento que continua disponível | 17 Associações | A associação devolve a coleção. O cancelamento é um filtro que alguém não escreveu. |
| `after_create` e `after_save` na mesma reserva | 19 Callbacks | Ordem de callback, o que cada um observa, e um registro duplicado reproduzido. |
| `create` com `if`, `unless` e `begin`, 37 commits | 21 Controllers | O que é do controller e o que já devia estar no model. O histórico mostra correções que não se apagaram. |
| `rails console` e `Contract.last` | 23 Console | Irb e console, o que uma expressão devolve, e o comando que grava sem parecer gravação. |
| Factory com só um `name` | 24 Testes | O teste passou porque fabricou um contrato que o pátio não aceitaria. |

## Régua dos capítulos que faltam

Ruby antes do Rails. Três a cinco assuntos. Sem referência para frente.
Quando um símbolo de Rails precisar aparecer cedo — `def active?` no
capítulo de métodos —, a explicação do pedaço cabe na página, curta, e o
capítulo de modelo não fica sem aula.

### 04 — Objetos e tipos

Tudo é objeto, inclusive número, `true` e `nil`. `class` pergunta o tipo.
Inteiro não é ponto flutuante: dinheiro da locação em centavos, inteiro.
**Dor:** diária de R$ 480 somada como texto, ou como `Float`, e o boleto
não fecha. **Evidência:** `480.class`, a soma errada, a soma em centavos.

### 05 — Métodos

A cena do `active?`. **Evidência:** o método extraído num arquivo que a
Lívia roda, com `"active"` e com `"cancelled"`, e uma busca que mostra
onde mais o nome aparece.

### 06 — Condicionais

`if`, `unless`, `case`. **Dor:** contrato cancelado e ainda "ativo" porque
dois `if` independentes rodaram. O modificador `unless` no fim da linha,
que o controller de 2021 usa, aparece aqui com nome.

### 07 — Strings e símbolos

String mutável, símbolo imutável, e por que `status` às vezes é `:"active"`
e às vezes `"active"`. **Dor:** `==` entre os dois é falso. A coluna e o
código não combinaram o tipo.

### 08 — Arrays e hashes

A manhã é uma lista. O contrato é um hash vindo de dois sistemas com
chaves diferentes. **Evidência:** normalizar um contrato da planilha e um
do banco para o mesmo hash.

### 09 — Blocos e enumerables

`each`, `map`, `select`, `find`. O bloco é o desenho de 1993, agora com
sintaxe. **Dor:** a lista da Helena tem quatro plataformas; o `select`
cortou a que estava com `status` nulo.

### 10 — Classes

`class`, `initialize`, instância. O contrato sem Rails, escrito à mão, para
o Rails ter o que comparar. **Evidência:** dois contratos, mesma classe,
datas diferentes.

### 11 — Módulos

Mixin, `include`, e um módulo `Billable` que o Sérgio copiou para dois
models. **Dor:** os dois incluem o módulo e um deles redefine o método sem
chamar `super`.

### 12 — Exceções

`begin` / `rescue` / `ensure`. **Dor:** o `begin` que a Lívia vai encontrar
no controller nasce aqui, num arquivo pequeno, com a mensagem de verdade.
O controller de 37 commits fica para o capítulo 21, já com essa gramática
aprendida.

### 13 — Gems e Bundler

`Gemfile`, `Gemfile.lock`, uma gem, uma versão conflitante. **Dor:** subir
a versão de uma gem que o `contracts_controller` usa e quebrar a manhã no
computador da Lívia, não no servidor.

### 14 — O que é o Rails

A estrutura de pastas do `nortea`, o comando que sobe o servidor local, e
o que o framework decide sozinho. **Evidência:** a página local responde.
Ainda não se mexe no `create`.

### 15 — Modelos

A cena do `schema.rb`, inteira. **Evidência:** no console local, um
`Contract` mostra as três colunas de começo com valores diferentes, e fica
óbvio qual relatório lê qual.

### 16 — Migrations

Uma mudança de tabela com histórico, em vez de editar o `schema.rb` à mão.
**Dor:** alguém no passado editou o banco na mão e o `schema.rb` mentiu
por um tempo. A migration nova é pequena: não apaga as três colunas neste
capítulo. Esconder coluna sem migração de dado é como a multa nasce.

### 17 — Associações

A cena do equipamento disponível depois do cancelamento. **Evidência:**
`equipment.contracts` devolve o cancelado; o escopo `active` devolve só o
que a Helena chamaria de ocupado.

### 18 — Validações

Presença de equipamento, cliente, período e responsável. **Dor:** o
formulário grava contrato sem responsável. A validação recusa, com a
mensagem na tela.

### 19 — Callbacks

A cena dos dois `after_*`. **Evidência:** um create gera dois registros de
reserva; depois da correção, um. O teste do Diego entra como reprodução,
não como framework de teste ainda.

### 20 — Rotas

O pedido HTTP chega num verbo e num caminho. **Dor:** o cancelamento está
em `POST /contracts` quando a Marta acha que está em "cancelar". A rota
diz o contrário do botão.

### 21 — Controllers

A cena das 37 commits. **Evidência:** o `create` perde o `begin` interno
porque a falha passa a ser exceção ou validação, já ensinadas. O arquivo
fica menor de um problema, não de uma faxina.

### 22 — Views

O que a Helena vê. ERB só o quanto a página precisa. **Dor:** a view
pergunta `active?` e também repete a comparação do status. As duas
divergem.

### 23 — Console

A cena do `Contract.last`. **Evidência:** uma expressão que só lê, e uma
que grava (`update`, `save`) com a volta do `=>`. A Marta tinha razão em
perguntar.

### 24 — Testes

A cena da factory. Minitest ou RSpec: o repositório de 2016 está de RSpec
(`spec/factories`). O livro ensina o que está no arquivo, RSpec, com a
factory. **Evidência:** o teste vermelho quando o contrato não tem
equipamento; verde quando a factory passa a exigir o que o pátio exige.

### 25 — Jobs

A reserva e o aviso à Helena não cabem dentro do pedido. **Dor:** o
`create` espera o e-mail e a Marta acha que o sistema travou. O job faz o
e-mail depois, e o pedido devolve o contrato.

### 26 — APIs

O adendo da Serra Azul. **Dor:** o JSON devolve `status: "active"` e o
sistema deles compara com `"ativo"`. Contrato escrito numa tabela curta,
um endpoint, um `422`.

### 27 — Autenticação

A Helena entra com usuário. A Serra Azul consulta com uma credencial que
só lê os próprios contratos. **Dor:** a credencial de leitura aceitava
`POST`. O teste mostra o `403`.

### 28 — Deploy

O 3.3 do servidor, o 3.4 da Lívia, e o horário. O pátio carrega às 6h. Não
é a sexta às 16h52 de outro livro: é a véspera de um despacho, e o Sérgio
quer "só subir o ajuste". **Evidência:** o que tem de ser igual entre as
máquinas, e o horário que o Renato recusa.

### 29 — Projeto final

O módulo de contratos cobre a manhã de 3 de junho: lista igual à
planilha para os nove canteiros da Serra Azul, cancelamento que libera o
equipamento, teste da factory honesta, um endpoint de leitura. O Rails de
2016 não é apagado. O módulo novo é o que a Helena aceita comparar com o
papel.
