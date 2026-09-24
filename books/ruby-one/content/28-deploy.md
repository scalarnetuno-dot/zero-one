---
title: "Deploy"
number: 28
slug: deploy
part: p6
kicker: "Terça, 2 de junho, 17h40. O Sérgio queria só subir o ajuste. O pátio carregava a Serra Azul às seis da manhã seguinte."
goal: >-
  Levar o código da sua máquina ao servidor sabendo o que precisa ser
  igual entre os dois, em que ordem as coisas acontecem, como voltar
  atrás — e em que horário não se sobe nada.
---

## O que tem de ser igual

O código da Lívia roda na máquina dela desde o capítulo
@cap:gems-e-bundler. O servidor roda outro computador, outro sistema e,
até aqui, outra pessoa decidindo o que está nele. Um deploy é levar uma
versão do código de um lado para o outro. Ele dá certo quando o que
importa é igual nos dois lados, e só isso.

| O quê | Onde está escrito | O que dá errado se divergir |
|---|---|---|
| a linha do Ruby | `.ruby-version` e `Gemfile` | sintaxe que um aceita e o outro não |
| as gems | `Gemfile.lock` | o `bundle update` da Lívia, no servidor |
| as tabelas | `db/migrate` | o `site_code` que o `schema.rb` não tinha |
| as senhas e chaves | credenciais, fora do Git | o sistema sobe sem falar com o banco |
| o que roda | Puma e o worker do Sidekiq | job com código velho |

Tabela: Cinco coisas. As três primeiras estão no repositório. As duas
últimas, não — e são as que se esquecem.

A linha do Ruby já pegou a Lívia uma vez, em maio. Ela escreveu num job:

```ruby
contratos.map { it.code }
```

Na `patio`, com o 3.4, funciona. No `nortea`, o `.ruby-version` diz 3.3.6,
e o `it` do capítulo @cap:blocos-e-enumerables não existe nessa linha: ali,
`it` é só um nome qualquer, que não foi definido. A esteira de testes pegou
antes do servidor, porque ela lê o mesmo `.ruby-version`:

```text
NameError:
  undefined local variable or method `it' for an instance of
  NotifySerraAzulJob
```

Foi o primeiro teste vermelho da esteira que ninguém da sala tinha
provocado de propósito.

## A esteira

Antes de qualquer deploy, a versão passa pela esteira — um servidor que,
a cada `push`, instala o projeto do zero e roda os testes:

```yaml title=".github/workflows/ci.yml" numbered
name: ci
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with:
          bundler-cache: true
      - run: bin/rails db:prepare
      - run: bundle exec rspec
```

`ruby/setup-ruby` sem versão lê o `.ruby-version`: 3.3.6, a do servidor.
`bundler-cache: true` roda o `bundle install` com o lock. `db:prepare`
cria o banco de teste pelas migrations — o `site_code` do capítulo
@cap:migrations teria aparecido aqui, se existisse esteira em 2023.

Esteira vermelha, sem deploy. Não é uma recomendação: o botão de deploy
só aparece para a versão que passou.

## A ordem

O `nortea` sobe com Capistrano, desde 2016. Um comando:

```text
$ bundle exec cap production deploy
```

E o que ele faz, em ordem, no servidor:

```text
1. baixa a versão nova numa pasta nova, ao lado da atual
2. bundle install --deployment     (as gems do lock)
3. bin/rails assets:precompile     (CSS e JavaScript da tela)
4. bin/rails db:migrate            (as migrations pendentes)
5. troca o atalho "current" para a pasta nova
6. reinicia o Puma                 (as telas e a API)
7. reinicia o Sidekiq              (os jobs)
```

A pasta nova fica **ao lado** da atual até o passo 5. Se as gems não
instalarem, ou uma migration falhar, a troca não acontece: o sistema
continua na versão anterior, inteiro.

O passo 7 é o que se esquece. O worker do capítulo @cap:jobs carregou o
código quando subiu. Sem reiniciá-lo, as telas rodam a versão nova e os
jobs, a antiga — e a antiga pode procurar uma coluna que a migration de
hoje acabou de mudar.

:::pitfall
O passo 4 muda o banco **antes** de o passo 6 trocar o código. Durante
alguns segundos, a versão antiga roda sobre o banco novo. Uma migration que
remove ou renomeia coluna quebra a versão antiga nesses segundos. É por
isso que o capítulo @cap:migrations separou a remoção do `site_code` em
dois deploys: primeiro o código para de ler, depois a coluna sai.
:::

## Voltar

```text
$ bundle exec cap production deploy:rollback
```

O `rollback` troca o atalho de volta para a pasta anterior e reinicia. O
código volta em segundos.

O banco **não** volta. As migrations do deploy continuam aplicadas. Se
alguma delas for incompatível com o código anterior, voltar o código não
basta. A regra da casa, desde este mês: toda migration de um deploy precisa
funcionar com o código de antes **e** com o de depois. É o que faz o
`rollback` ser uma opção real, e não uma esperança.

:::key
Um deploy seguro é um que se desfaz. Antes de subir, pergunte: se isto der
errado às 6h10, o `rollback` resolve? Se a resposta depende de desfazer
uma migration, o deploy está grande demais para aquele horário.
:::

## `/up`

Depois de subir, o Capistrano confere que o sistema responde:

```text
$ curl -s -o /dev/null -w "%{http_code}\n" https://nortea.com.br/up
200
```

`/up` é uma rota que o Rails 7 traz pronta: responde `200` se a aplicação
subiu. Não confere se a lista da manhã está certa. Confere que há um
sistema para conferir. A conferência da lista é da Helena, às 6h.

:::story Só o ajuste
Terça, 2 de junho, 17h40. O Sérgio parou na mesa do Renato com o notebook
aberto.

— Um ajuste só. O rótulo "Em uso, devolução atrasada" está cortando na
tela do tablet do pátio. Tirei o "devolução". Uma linha no helper. A
esteira passou.

O Renato olhou o relógio do canto da tela.

— Amanhã às seis o pátio carrega os nove canteiros da Serra Azul. Às dez,
o Rômulo mostra a página para eles.

— É uma linha.

— É uma linha que ninguém olhou no tablet. Se o `rollback` for preciso,
quem roda? Às 5h50?

— Eu.

— E se não for o rótulo? Se for a pasta de assets, ou o Sidekiq que não
reinicia?

O Sérgio não respondeu.

— O último deploy foi ontem às 14h — disse o Renato. — A Helena conferiu a
lista hoje de manhã contra a planilha. Bateu. É essa versão que o pátio
usa amanhã.

— E o rótulo cortado?

— A Helena lê "Em uso, devol...". Ela sabe o que vem depois.

O Sérgio fechou o notebook.

— Quinta?

— Quinta, às 14h. Com a Helena olhando o tablet.
:::

## O horário

A versão que vai para o dia 3 de junho subiu na segunda, 1º, às 14h. A
escolha não foi do calendário da sprint:

- 14h é depois da carga das 6h e antes da devolução das 17h. O pátio está
  quieto.
- Segunda deixa terça inteira para a Helena conferir a lista da manhã
  contra a planilha, uma vez, com a versão que vai valer.
- Quem subiu fica até as 18h. Se algo der errado, o `rollback` é rodado
  por quem sabe o que subiu.

E a véspera fica sem deploy. Não por superstição. Porque um erro às 17h40
de terça só é descoberto às 6h de quarta, por quem não pode fazer nada a
não ser voltar para a planilha.

:::summary
- Deploy dá certo quando Ruby, gems, tabelas, credenciais e processos são
  iguais entre a máquina e o servidor.
- A esteira lê o `.ruby-version` e o lock, e roda os testes do zero.
  Vermelho, sem deploy.
- A ordem: código ao lado, gems, assets, migrations, troca, Puma, Sidekiq.
  O worker esquecido roda código velho.
- `rollback` volta o código, não o banco. Toda migration precisa funcionar
  com o código de antes e o de depois.
- O horário é parte do deploy: longe da carga, com tempo para conferir, e
  nunca na véspera do que não pode falhar.
:::

:::exercise level=1
Ponha os passos na ordem em que o Capistrano os executa, e diga qual deles
não pode ser esquecido quando o deploy muda um job:

reiniciar o Sidekiq · `db:migrate` · `bundle install` · trocar o atalho ·
baixar o código · reiniciar o Puma · `assets:precompile`

:::answer
Baixar o código, `bundle install`, `assets:precompile`, `db:migrate`,
trocar o atalho, reiniciar o Puma, reiniciar o Sidekiq.

Reiniciar o Sidekiq. Sem ele, o worker continua com o código do job
anterior na memória, e a mudança não vale para nenhum job até alguém
reiniciar.
:::

:::exercise level=2
A esteira passa na máquina da Lívia com Ruby 3.4 e falha no servidor de
CI. O erro é ``undefined local variable or method `it'``. Explique por que a
esteira está certa e a máquina dela, errada — e o que fazer para não
acontecer de novo.

:::answer
A esteira roda o Ruby do `.ruby-version` do `nortea`: 3.3.6, o do servidor.
O `it` só existe a partir do 3.4. A máquina da Lívia rodou os testes com o
Ruby errado — o da `patio` —, provavelmente num terminal aberto antes de o
gerenciador de versões trocar a linha, ou fora da pasta do projeto.

Para não acontecer de novo: `ruby -v` dentro da pasta antes de rodar os
testes, o que o gerenciador do capítulo @cap:gems-e-bundler resolve
sozinho quando está bem instalado. E a regra de não usar `it` no `nortea`
até o servidor sair do 3.3.
:::

:::exercise level=3
Escreva, em até dez linhas, a lista que o Renato pôs no documento da
equipe para qualquer deploy entre 1º e 5 de junho.

:::answer
1. Só sobe o que a esteira aprovou.
2. Sobe entre 14h e 15h, de segunda a quinta. Nunca na véspera de
   carga da Serra Azul.
3. Migration que remove ou renomeia coluna não sobe nesta semana.
4. Quem sobe fica até as 18h.
5. Depois do deploy: `/up` com `200`, e o Sidekiq processando um job de
   teste.
6. A Helena confere a lista da manhã seguinte contra a planilha.
7. Se a lista não bater, `rollback` antes das 6h10, e o caminhão sai pela
   planilha.
8. Ajuste de texto ou de layout espera a semana seguinte.

A lista não fala de tecnologia além do necessário. Ela fala do pátio,
porque é o pátio que diz se o deploy deu certo.
:::
