---
title: "O primeiro projeto"
number: 28
slug: primeiro-projeto-laravel
part: p6
kicker: "Seu Juvenal viu a tela de boas-vindas, leu o nome do framework em letras grandes e perguntou se já dava para cadastrar os livros."
goal: >-
  Criar o projeto da Casa Amarela com o Laravel, entender o papel de cada
  pasta de topo, saber o que o `.env` guarda e por que ele não vai para o
  Git, e fazer a primeira rota responder.
---

:::story Já tá pronto?
Dedé projetou a tela na parede da sala da associação para mostrar que o
ambiente estava de pé. Fundo claro, o nome do framework no meio, alguns
links de documentação em volta.

Seu Juvenal olhou por uns segundos.

— Bonito. Já tá pronto?

— Isso é a tela que vem de fábrica.

— Mas tem o nome do sistema ali.

— Tem o nome do framework.

Seu Juvenal apontou para a parede com o queixo, do jeito que a Vera aponta
o monitor.

— Pra mim tá escrito que funciona.
:::

## `composer create-project`

Um comando cria o projeto inteiro:

```text
$ composer create-project laravel/laravel casa-amarela
```

```text
Creating a "laravel/laravel" project at "./casa-amarela"
Installing laravel/laravel (v12.0.0)
Created project in /home/dede/casa-amarela

> @php -r "file_exists('.env') || copy('.env.example', '.env');"

Loading composer repositories with package information
Updating dependencies
Package operations: 107 installs, 0 updates, 0 removals
  - Installing symfony/polyfill-mbstring (v1.31.0)
  - Installing illuminate/support (v12.0.0)
  ...
Generating optimized autoload files

> @php artisan key:generate --ansi

   INFO  Application key set successfully.
```

Cento e sete pacotes. É bem mais que os três do `var-dumper`, e a diferença
é o que o capítulo anterior listou: fila, e-mail, sessão, validação,
console, cache e o resto.

Repare nas duas últimas linhas, porque elas não são instalação: são o
projeto se preparando. O `.env` foi criado a partir do `.env.example`, e uma
chave de aplicação foi gerada. Você vai ouvir falar das duas em cinco
minutos.

## A rota que responde em dois minutos

```text
$ cd casa-amarela
$ php artisan serve
```

```text
   INFO  Server running on [http://127.0.0.1:8000].

  Press Ctrl+C to stop the server
```

Abra `routes/web.php` e acrescente quatro linhas:

```php title="routes/web.php" numbered
Route::get('/saude', function () {
    return [
        'status' => 'ok',
        'hora' => now()->toIso8601String(),
    ];
});
```

```text
$ curl -s localhost:8000/saude
{"status":"ok","hora":"2026-01-13T09:41:12-03:00"}
```

Três coisas aconteceram sem você pedir.

A rota devolveu um **array**, e chegou JSON. O Laravel converte array e
objeto automaticamente, e já manda o `Content-Type` certo.

O `now()` existe sem nenhum `use`. É uma das funções de conveniência que o
framework registra globalmente — e devolve um objeto de data, não um texto.

E o endereço é `/saude`, não `/saude.php`. O front controller do capítulo
@cap:um-framework-de-quarenta-linhas está lá, em `public/index.php`,
fazendo exatamente o que o seu fazia.

:::trivia
O esqueleto já vem com uma rota de saúde pronta, em `/up`, configurada no
`bootstrap/app.php`. Ela existe para o serviço de monitoramento bater e
saber se a aplicação está viva.

A `/saude` deste capítulo é sua, para você ver a rota funcionar. Num projeto
de verdade, quem responde ao monitoramento é a `/up`.
:::

## As pastas que importam

O projeto tem doze pastas de topo. Seis delas você vai abrir todo dia.

:::tree title="O que existe depois do create-project"
casa-amarela/
  app/          # o seu código
  bootstrap/    # app.php monta a aplicação; cache/ é gerado
  config/       # um arquivo por assunto
  database/     # migrações, seeders e factories
  public/       # index.php e arquivos servidos direto
  resources/    # views Blade, CSS e JS de origem
  routes/       # web.php e console.php
  storage/      # log, cache, arquivos enviados, sessão
  tests/
  vendor/       # do Composer, fora do Git
  .env          # configuração desta máquina, fora do Git
  artisan       # o comando de terminal do projeto
:::

Três merecem um parágrafo agora.

**`app/`** começa quase vazia: um controller base, um model de usuário e um
provedor. Isso é de propósito — o Laravel não adivinha a sua arquitetura, e
as pastas que você criar aqui dentro são decisão sua.

**`storage/`** é a única pasta em que a aplicação **escreve**. Log, cache
compilado das views, sessões e uploads moram aí. É também a origem do
primeiro erro de quase todo mundo.

**`public/`** é a única que o servidor web deve enxergar. Tudo que estiver
fora dela — o `.env`, o `vendor/`, o seu código — fica inalcançável pela
internet, e é isso que separa este projeto da pasta do Sistema, em que o
backup de 2019 podia ser baixado por qualquer um.

## O primeiro erro de permissão

Mais cedo ou mais tarde, e sempre no servidor:

```text
The stream or file "/var/www/casa-amarela/storage/logs/laravel.log"
could not be opened in append mode: Failed to open stream:
Permission denied
```

A causa é sempre a mesma: quem roda o PHP no servidor não é você. É um
usuário do sistema — `www-data` no Debian e no Ubuntu, `nginx` ou `apache`
em outras distribuições — e ele precisa poder escrever em duas pastas.

```text
$ sudo chown -R www-data:www-data storage bootstrap/cache
$ sudo chmod -R 775 storage bootstrap/cache
```

:::pitfall
A receita que aparece em fórum é `chmod -R 777 storage`. Ela funciona, e
significa "qualquer usuário do servidor pode escrever aqui".

Num servidor compartilhado, isso inclui os outros sites hospedados na mesma
máquina. Num servidor só seu, inclui qualquer processo que um invasor
consiga rodar com qualquer usuário.

O `775` com o dono certo resolve o mesmo problema e não abre a porta. A
diferença entre os dois comandos é de dez segundos para escrever e de anos
para descobrir que foi por ali.
:::

## `.env`: a configuração desta máquina

```text title=".env"
APP_NAME="Casa Amarela"
APP_ENV=local
APP_KEY=base64:0sT3qk9... 
APP_DEBUG=true
APP_URL=http://localhost

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=casa_amarela
DB_USERNAME=root
DB_PASSWORD=senha
```

O `.env` guarda o que **muda de máquina para máquina**: endereço do banco,
senha, se os erros aparecem na tela, para onde vão os e-mails. A sua máquina
tem um, o servidor tem outro, e os dois nunca são iguais.

Três regras, e as três têm consequência.

**O `.env` não entra no Git.** Ele já vem no `.gitignore` do esqueleto. O
que entra é o `.env.example`, com as mesmas chaves e sem os valores — é ele
que conta a quem clonar o projeto o que precisa ser preenchido.

**A `APP_KEY` é usada para criptografar.** Sessões e dados cifrados dependem
dela. Trocar a chave num sistema no ar derruba todas as sessões abertas;
rodar sem ela dá erro na primeira requisição que precisar de criptografia.
Ela é gerada uma vez, por ambiente, e guardada com as senhas.

**`APP_DEBUG=true` nunca vai para produção.** Com ela ligada, um erro
devolve a página de diagnóstico do Laravel — que mostra o trecho do código,
os valores das variáveis e, dependendo do ponto, o conteúdo do próprio
`.env`.

:::key
No Laravel 11 em diante o banco padrão do `.env.example` é SQLite, porque
ele funciona sem instalar nada.

O projeto da Casa Amarela já tem um MySQL desde o capítulo
@cap:do-arquivo-ao-banco, com quatro tabelas e dados dentro. Troque para
`mysql` e aponte para o banco que já existe.
:::

## Servir o projeto: escolha uma

Quatro formas aparecem na documentação, e a única decisão errada é tentar as
quatro no primeiro dia.

| Forma | Quando serve |
|---|---|
| `php artisan serve` | agora, e para o livro inteiro |
| Laravel Sail | quando a equipe precisa do mesmo ambiente |
| Valet | macOS, vários projetos ao mesmo tempo |
| Docker próprio | quando produção já é Docker |

Tabela: O `artisan serve` é o servidor embutido do PHP com as rotas do
projeto. Não serve para produção e serve perfeitamente para aprender.

:::pitfall
A tentação do primeiro dia é começar por Docker, "porque é assim que se faz
profissionalmente". Em geral é, e no primeiro dia o resultado é duas horas
depurando volume, permissão e rede — nenhuma das quais tem a ver com PHP.

Container resolve um problema real: fazer a sua máquina parecer com o
servidor. Esse problema aparece quando existe um servidor e existe uma
equipe. Antes disso, ele é só um problema a mais.
:::

## O que o `index.php` faz

Vale abrir o arquivo, porque ele tem doze linhas e você já conhece nove:

```php title="public/index.php" numbered
<?php

use Illuminate\Foundation\Application;
use Illuminate\Http\Request;

define('LARAVEL_START', microtime(true));

require __DIR__.'/../vendor/autoload.php';

$app = require_once __DIR__.'/../bootstrap/app.php';

$app->handleRequest(Request::capture());
```

Autoload do Composer, a aplicação montada pelo `bootstrap/app.php`, a
requisição capturada das superglobais e entregue. Depois disso vêm as
camadas, o roteador, o seu código e a resposta — o desenho do capítulo
anterior, com nomes de gente grande.

:::tree title="Onde estamos agora"
casa-amarela/
  .env              # com o MySQL do projeto, fora do Git
  .env.example      # as mesmas chaves, sem valores
  bootstrap/app.php
  public/index.php
  routes/web.php    # com GET /saude respondendo
:::

:::summary
- `composer create-project laravel/laravel` cria o esqueleto, copia o `.env`
  e gera a `APP_KEY`.
- Uma rota que devolve array vira JSON com o cabeçalho certo, sem
  conversão à mão.
- `app/` começa quase vazia de propósito; a arquitetura interna é sua.
- `storage/` e `bootstrap/cache/` precisam ser graváveis pelo usuário do
  servidor web — com `775` e o dono certo, não com `777`.
- `public/` é a única pasta que o servidor web enxerga; `.env` e `vendor/`
  ficam fora do alcance da internet.
- O `.env` guarda o que muda de máquina; ele fica fora do Git e o
  `.env.example` entra no lugar.
- `APP_KEY` cifra sessão e dados; `APP_DEBUG=true` em produção mostra código
  e configuração na tela.
- `php artisan serve` basta para aprender; Docker resolve um problema que
  ainda não existe no primeiro dia.
:::

:::checkpoint
Você cria um projeto Laravel, sobe o servidor, escreve uma rota que responde
JSON, explica o papel de cada pasta de topo e sabe dizer por que o `.env`
não entra no repositório e o que a `APP_KEY` protege.
:::

:::exercise level=1
Um colega clonou o repositório do projeto e recebeu, na primeira
requisição:

```text
No application encryption key has been specified.
```

Diga o que aconteceu, qual comando resolve e por que esse erro não pode ser
evitado versionando o `.env`.

:::answer
O `.env` não veio junto — e não deveria vir. Sem ele, não há `APP_KEY`.

```text
$ cp .env.example .env
$ php artisan key:generate
```

Versionar o `.env` "resolveria" o erro e criaria três problemas piores. A
senha do banco de produção entraria no repositório, onde fica para sempre no
histórico mesmo depois de removida. Todos os ambientes passariam a usar a
mesma chave de criptografia. E cada pessoa da equipe sobrescreveria o
endereço de banco das outras a cada `git pull`.

O `.env.example` existe exatamente para isso: ele leva as **chaves** sem os
**valores**, e o erro acima é o lembrete de que falta um passo de dez
segundos.
:::

:::exercise level=2
Acrescente à `/saude` três informações úteis para quem monitora: a versão do
PHP, se a aplicação está em modo de depuração e se o banco responde.

Cuidado com o que você expõe: a rota é pública.

:::answer
```php title="routes/web.php" numbered
Route::get('/saude', function () {
    try {
        DB::connection()->getPdo();
        $banco = 'ok';
    } catch (\Throwable $e) {
        $banco = 'falhou';
    }

    return response()->json([
        'status' => $banco === 'ok' ? 'ok' : 'degradado',
        'php' => PHP_VERSION,
        'debug' => config('app.debug'),
        'banco' => $banco,
    ], $banco === 'ok' ? 200 : 503);
});
```

O cuidado pedido no enunciado está em duas decisões.

**O `catch` não devolve a mensagem da exceção.** O rastro de uma falha de
conexão contém host, usuário e às vezes senha — e esta rota é pública.
Quem monitora precisa saber que falhou; quem investiga olha o log.

**O status muda junto.** Devolver `200` com `"status":"degradado"` obriga o
monitoramento a interpretar o corpo. O `503` é lido por qualquer ferramenta
sem configuração nenhuma.

Uma decisão discutível, deixada de propósito: expor `PHP_VERSION` numa rota
pública conta a um invasor qual versão atacar. Em produção, o comum é ou
proteger a rota, ou devolver só `status`, e deixar o detalhe para uma rota
interna.
:::

:::exercise level=3
O deploy da Casa Amarela é feito copiando a pasta do projeto para o
servidor. Na primeira tentativa, a aplicação subiu e a página quebrou com
erro de permissão em `storage/logs`.

O estagiário rodou `chmod -R 777 storage` e funcionou.

Escreva o que você diria na revisão: por que funcionou, qual é o risco
concreto, qual é a correção, e como evitar que a pasta volte a ser copiada
com dono errado no próximo deploy.

:::answer
**Por que funcionou.** `777` dá permissão de escrita a todo mundo, o que
inclui o usuário que roda o PHP. O erro some porque o problema — o dono
errado — deixou de importar.

**O risco concreto.** Qualquer processo do servidor passa a poder escrever
em `storage/`. Numa hospedagem compartilhada, isso inclui os outros sites da
máquina. E `storage/` não guarda só log: guarda sessões e as views Blade
compiladas, que são **arquivos PHP que a aplicação executa**. Permissão de
escrita ali é permissão de execução por tabela.

**A correção.** Dono certo e permissão de grupo:

```text
$ sudo chown -R www-data:www-data storage bootstrap/cache
$ sudo chmod -R 775 storage bootstrap/cache
```

**Como não repetir.** O problema de fundo não é a permissão: é o deploy por
cópia de pasta, que refaz o dono a cada vez e depende de alguém lembrar de
corrigir. Duas saídas, em ordem de esforço.

A barata: pôr os dois comandos no passo de publicação, para que rodem
sempre, sem depender de memória.

A certa: não copiar `storage/` no deploy. Ela guarda estado — log, sessão,
upload — e estado não é parte do código. O caminho comum é mantê-la fora da
pasta versionada e apontar para ela, de forma que o deploy troque só o
código e não toque em nada que a aplicação escreveu.
:::
