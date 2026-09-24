---
title: "Como organizar um projeto PHP"
number: 29
slug: como-organizar-um-projeto-php
part: p5
kicker: "Na sexta-feira, a Márcia anunciou que a parte web começava na segunda. O Dedé pediu o fim de semana para arrumar a casa antes da visita."
goal: >-
  Dar ao projeto uma estrutura de pastas em que cada coisa tem um lugar,
  tirar senha e configuração do código, montar os objetos do sistema num
  ponto só, e reconhecer, peça por peça, a estrutura que o Laravel vai
  propor no volume 2.
---

:::story Onze vezes a mesma senha
— Segunda-feira começa a web — disse a Márcia, na reunião de sexta. — A
Vera quer ver tela. O edital quer ver tela. Eu quero ver tela.

— Antes da tela — disse o Dedé —, eu queria uma tarde.

— Para quê?

Ele virou o notebook para a mesa. Um terminal, e um comando:

```text
$ grep -rl "'root', 'senha'" --include=*.php . | wc -l
11
```

— Onze arquivos com a senha do banco escrita dentro. Se a senha mudar,
são onze lugares. Se alguém publicar o repositório, são onze cópias da
senha na internet.

A Tainá olhou a pasta do projeto no próprio notebook. Tinha começado com
um arquivo, no capítulo de PDO. Agora tinha `importar.php`,
`importar2.php`, `emprestar.php`, `relatorio.php`, um `bootstrap.php`, uma
pasta `scripts/` com metade dos scripts, e a outra metade na raiz.

— Parece o Sistema — disse ela, baixinho.

— Parece o Sistema em 2010 — disse o Nonato, da mesa ao lado, sem tirar os
olhos da tela. — Em 2011 já tinha o `funcoes2_NOVO_final.php`. Arrumem
agora.
:::

## A pasta como ela está

Vinte e oito capítulos de trabalho deixaram isto:

:::tree title="O acervo, na sexta-feira"
acervo/
  composer.json, composer.lock
  vendor/
  src/                   # as classes: bem organizadas desde o 18
  bootstrap.php          # erros e log, do capítulo 28
  filtros.php            # funções soltas, do capítulo 25
  importar.php           # senha dentro
  importar2.php          # senha dentro, "o que funciona"
  emprestar.php          # senha dentro
  relatorio.php          # senha dentro
  scripts/
    importar-doacoes.php # senha dentro
    atrasados.php        # senha dentro
    ...
  var/log/
  phpstan.neon
:::

Nada aqui está errado sozinho. O problema é a soma, e ele tem três partes.

**Não há lugar certo para um arquivo novo.** Um script entra na raiz ou em
`scripts/` conforme o humor do dia. Quem chega ao projeto não sabe onde
procurar, e quem escreve não sabe onde pôr.

**Configuração e segredo estão no código.** A senha, o fuso, o prazo de
catorze dias. Mudar qualquer um exige editar PHP — e o código vai para o
Git, com tudo o que estiver escrito nele.

**Cada script monta os próprios objetos.** O `new PDO(...)` aparece onze
vezes; o `new RelogioDoSistema(...)`, quatro; o `new Registro(...)`, com
três caminhos de log diferentes.

A arrumação resolve as três, uma por seção.

## Um lugar para cada coisa

:::tree title="O acervo, na segunda-feira"
acervo/
  bin/                   # scripts de linha de comando
    importar-doacoes.php
    atrasados.php
  config/                # configuração: arrays, sem segredo
    app.php
  public/                # a única pasta que o servidor web enxerga
  src/                   # todo o código do domínio
    Acervo/ Circulacao/ Emprestimos/ Importacao/
    Leitores/ Tempo/
    Registro.php
    Servicos.php
    funcoes.php
  tests/
  var/                   # o que o programa gera: log, cache
    log/
  vendor/                # do Composer; nunca editado à mão
  bootstrap.php          # monta tudo, num lugar só
  .env                   # segredos desta máquina; fora do Git
  .env.example           # o molde do .env; no Git
  .gitignore
  composer.json, composer.lock
  phpstan.neon
:::

A regra por trás da árvore: **cada pasta responde a uma pergunta.**

| Pasta | Pergunta |
|---|---|
| `src/` | O que o sistema **sabe fazer**? |
| `config/` | Como ele está **ajustado**? |
| `bin/` | Como se **chama** pela linha de comando? |
| `public/` | Como se **chama** pelo navegador? |
| `var/` | O que ele **produziu** enquanto rodava? |
| `tests/` | Como sabemos que ele **funciona**? |

Tabela: Uma pergunta por pasta. Um arquivo novo vai para a pasta cuja
pergunta ele responde.

`public/` está vazia, e fica vazia até o volume 2. Ela existe agora por um
motivo de segurança que vale a pena entender antes de ter o que pôr nela:
o servidor web entrega ao navegador **qualquer arquivo** da pasta que ele
enxerga. Se ele enxergasse a raiz do projeto, `https://.../.env` entregaria
a senha do banco, e `https://.../var/log/app.log` entregaria o log. Com o
servidor apontado para `public/`, só existe na web o que foi posto ali de
propósito.

A pasta `scripts/` virou `bin/`, o nome que a maior parte dos projetos PHP
usa para os programas de linha de comando, e os scripts da raiz foram
para lá. O `importar2.php`, "o que funciona", foi comparado com o `importar.php`
numa tarde, as diferenças foram parar no `Importador` e os dois viraram
`bin/importar-doacoes.php`. As funções de `filtros.php` foram para
`src/funcoes.php`, que o Composer passa a carregar sozinho:

```json title="composer.json"
{
    "name": "casa-amarela/acervo",
    "type": "project",
    "require": {
        "php": "^8.3"
    },
    "autoload": {
        "psr-4": {
            "CasaAmarela\\": "src/"
        },
        "files": [
            "src/funcoes.php"
        ]
    },
    "scripts": {
        "analise": "phpstan analyse",
        "importar": "php bin/importar-doacoes.php"
    }
}
```

O `psr-4` do capítulo @cap:namespaces-e-autoload carrega classes quando
alguém as usa. Função não tem essa chance — o PHP não tem como adivinhar em
que arquivo ela mora —, e o `files` resolve do jeito simples: estes
arquivos são incluídos sempre, pelo `vendor/autoload.php`. Mantenha a
lista curta.

O bloco `scripts` dá nome aos comandos que a equipe roda: `composer
analise`, `composer importar`. Ninguém precisa lembrar o caminho do
PHPStan nem do script.

## Configuração fora do código

A configuração tem duas metades, e elas moram em lugares diferentes.

**O que muda de máquina para máquina** — senha, endereço do banco, fuso do
servidor — vai para um arquivo `.env` na raiz, que **não vai para o Git**:

```text title=".env"
APP_FUSO=America/Sao_Paulo
DB_DSN="mysql:host=127.0.0.1;dbname=casa_amarela;charset=utf8mb4"
DB_USUARIO=casa_amarela
DB_SENHA=a-senha-de-verdade
PRAZO_EM_DIAS=14
```

No Git vai o `.env.example`, igual e com os segredos em branco, para quem
chegar saber o que precisa preencher. E o `.gitignore` garante que o
verdadeiro não entre por descuido:

```text title=".gitignore"
/vendor/
/var/
/.env
```

**O que o programa lê** — com nome, tipo e valor padrão — vai para
`config/`, em arquivos PHP que devolvem um array:

```php title="config/app.php" numbered
<?php

declare(strict_types=1);

use function CasaAmarela\env;

return [
    'fuso' => env('APP_FUSO', 'America/Sao_Paulo'),
    'prazo_em_dias' => (int) env('PRAZO_EM_DIAS', '14'),
    'banco' => [
        'dsn' => env('DB_DSN'),
        'usuario' => env('DB_USUARIO'),
        'senha' => env('DB_SENHA'),
    ],
];
```

O `require` de um arquivo que termina em `return` devolve o valor desse
`return` — é assim que `$config = require 'config/app.php'` recebe o
array. `use function` é o `use` do capítulo @cap:namespaces-e-autoload
para funções.

As duas funções que leem o `.env`:

```php title="src/funcoes.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela;

function carregarEnv(string $caminho): void
{
    if (!is_file($caminho)) {
        return;
    }
    $valores = parse_ini_file($caminho, false, INI_SCANNER_RAW);
    foreach ($valores as $chave => $valor) {
        $_ENV[$chave] ??= $valor;
    }
}

function env(string $chave, ?string $padrao = null): ?string
{
    return $_ENV[$chave] ?? $padrao;
}
```

`parse_ini_file` lê um arquivo `chave=valor` e devolve um array;
`INI_SCANNER_RAW` pede que ele não tente interpretar os valores, e o `??=`
não sobrescreve um valor que já estava definido. É uma versão pequena do
que as bibliotecas de `.env` fazem com mais cuidado.

:::key
**Segredo no `.env`, fora do Git. Forma no `config/`, dentro do Git.** O
código do sistema nunca lê o `.env` direto: lê `$config['banco']['dsn']`.
Assim existe um único lugar que sabe de onde cada valor vem, e um único
lugar para dar um padrão a ele.
:::

:::pitfall
Se uma senha já foi para o Git uma vez, tirá-la do arquivo não a tira do
histórico: qualquer um com uma cópia do repositório encontra o commit
antigo. Depois de mover a senha para o `.env`, **troque a senha**. Na Casa
Amarela, foi a primeira tarefa de segunda-feira, antes de qualquer tela.
:::

## Montar tudo num lugar só

O `bootstrap.php` do capítulo @cap:erros-e-debug configurava erros. Agora
ele monta também os objetos que o sistema usa, e os entrega prontos:

```php title="bootstrap.php" numbered
<?php

declare(strict_types=1);

use CasaAmarela\Registro;
use CasaAmarela\Servicos;
use CasaAmarela\Tempo\Relogio;
use CasaAmarela\Tempo\RelogioDoSistema;

use function CasaAmarela\carregarEnv;

require __DIR__ . '/vendor/autoload.php';

carregarEnv(__DIR__ . '/.env');
$config = require __DIR__ . '/config/app.php';

// ...error_reporting e os dois tratadores do capítulo 28...

$servicos = new Servicos();

$servicos->registrar(PDO::class, fn() => new PDO(
    $config['banco']['dsn'],
    $config['banco']['usuario'],
    $config['banco']['senha'],
    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION],
));

$servicos->registrar(Relogio::class, fn() => new RelogioDoSistema(
    new DateTimeZone($config['fuso']),
));

$servicos->registrar(Registro::class, fn() => new Registro(
    __DIR__ . '/var/log/app.log',
));

return $servicos;
```

E `Servicos` é uma classe de vinte linhas que guarda closures — as do
capítulo @cap:funcoes-anonimas-e-closures — e só as chama quando alguém
pede:

```php title="src/Servicos.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela;

use Closure;
use RuntimeException;

final class Servicos
{
    /** @var array<string, Closure> */
    private array $fabricas = [];

    /** @var array<string, object> */
    private array $prontos = [];

    public function registrar(string $nome, Closure $fabrica): void
    {
        $this->fabricas[$nome] = $fabrica;
    }

    public function get(string $nome): object
    {
        if (!isset($this->fabricas[$nome])) {
            throw new RuntimeException("desconhecido: {$nome}");
        }
        $fabrica = $this->fabricas[$nome];
        return $this->prontos[$nome] ??= $fabrica($this);
    }
}
```

Três ideias em pouco código.

**Uma fábrica por serviço.** Cada closure sabe criar um objeto. Registrar
não cria nada: o `new PDO` só roda quando alguém pede o PDO. Um script que
só lê um CSV nunca abre conexão com o banco.

**Criado uma vez.** O `??=` guarda o objeto pronto na primeira chamada e
devolve o mesmo nas seguintes. Uma conexão por execução, não uma por
pedido.

**O nome é a classe.** `PDO::class` é o texto `'PDO'`;
`Relogio::class`, o nome completo da interface. Quem pede o `Relogio` não
sabe — nem precisa saber — que recebe um `RelogioDoSistema`. No teste, o
mesmo nome devolve um `RelogioParado`.

O script, depois da arrumação:

```php title="bin/importar-doacoes.php" numbered
<?php

declare(strict_types=1);

use CasaAmarela\Importacao\Importador;

$servicos = require __DIR__ . '/../bootstrap.php';

$importador = $servicos->get(Importador::class);
$importador->importar(__DIR__ . '/../var/doacoes.csv');
```

Nenhuma senha, nenhum `new PDO`, nenhum caminho de log. O script diz o que
faz; o `bootstrap.php` sabe como.

:::term Raiz de composição
O ponto único do programa em que os objetos são criados e ligados uns aos
outros. Fora dele, as classes recebem o que precisam pelo construtor e não
sabem de onde veio.

`Servicos` é um **contêiner**: o objeto que guarda as fábricas e entrega os
serviços prontos. O deste capítulo precisa que alguém registre cada
fábrica à mão.
:::

## Do acervo ao Laravel

Esta estrutura não foi inventada para a Casa Amarela. É, com poucas
diferenças de nome, a que quase todo projeto PHP moderno usa — e a que o
Laravel cria quando você digita o primeiro comando do volume 2.

| Aqui, no volume 1 | No Laravel, no volume 2 |
|---|---|
| `src/`, namespace `CasaAmarela\` | `app/`, namespace `App\` |
| `config/app.php` devolvendo array | `config/`, um arquivo por assunto |
| `.env` e `.env.example` | `.env` e `.env.example` |
| `env()` só dentro de `config/` | `env()` só dentro de `config/` |
| `bin/importar-doacoes.php` | comando do Artisan |
| `bootstrap.php` | `bootstrap/app.php` |
| `Servicos` com fábricas à mão | o contêiner, que monta sozinho |
| `var/log/` | `storage/logs/` |
| `public/`, vazia | `public/index.php`, a porta da web |
| `Registro` com contexto | `Log`, da PSR-3 |
| `Relogio` injetado | `now()`, congelável nos testes |

Tabela: O mapa da mudança. O que muda é o nome; o motivo de cada pasta é o
deste capítulo.

A linha do contêiner é a que o volume 2 abre primeiro. O `Servicos` precisa
que cada fábrica seja escrita; o contêiner do Laravel lê o construtor da
classe, vê que ela pede um `PDO` e um `Registro`, e monta os dois sozinho.
O capítulo 3 do volume 2 escreve essa versão à mão, em quarenta linhas,
antes de abrir o framework.

:::note Na sua carreira
Todo projeto começa como um script, e ninguém acorda decidindo que vai
virar o `funcoes2_NOVO_final.php`. Ele vira aos poucos, um arquivo na raiz
por vez, cada um com um bom motivo no dia em que foi criado.

A arrumação deste capítulo levou uma tarde porque o projeto tinha trinta
arquivos. Com trezentos, levaria um mês, e nenhuma empresa dá um mês para
isso. Organize quando dói pouco: a hora certa é quando você pensa "isto
aqui já está ficando bagunçado".
:::

## O que ainda falta

Na segunda-feira de manhã, a Tainá abriu o caderno na página que já tinha
`funcoes2_NOVO_final.php` e escreveu embaixo:

```text
v1 - o que eu sei fazer
  tipos, arrays, funções, strings
  SQL à mão, JOIN, índice, transação, PDO
  Composer, namespaces, classes, interfaces
  exceções, tipagem estrita, enums, objetos de valor
  referências, closures, geradores
  arquivos grandes, datas com fuso, erros que avisam
  um projeto com lugar para cada coisa

v2 - o que eu não sei
  o que chega do navegador até o PHP?
```

Todos os programas deste volume rodaram no terminal, chamados por alguém
que digitava `php` e um nome de arquivo. A Vera não vai digitar `php`. Ela
vai abrir o navegador, clicar num botão, e o navegador vai mandar um texto
para o servidor — um texto com um formato que tem nome, regras e trinta
anos de história.

O `$_GET` e o `$_POST` que você viu de passagem no começo do livro são o
que o PHP entende desse texto. Quase sempre, é o suficiente. Na primeira
semana do volume 2, não vai ser — e a Tainá vai passar uma manhã olhando um
`$_POST` vazio, com o aplicativo jurando que mandou tudo.

:::tree title="Onde estamos agora"
acervo/
  bin/          config/       public/ (vazia)
  src/          tests/        var/
  bootstrap.php               # config, erros, serviços
  .env (fora do Git)          .env.example
  composer.json               # psr-4, files, scripts
:::

:::milestone
Fim da Parte 5. O projeto tem uma pasta para cada pergunta, nenhum segredo
no código e um único lugar onde os objetos nascem. Referências, closures,
geradores, datas e erros deixaram de ser surpresa — e cada um deles volta
no volume 2 com outro nome.

Fim do volume 1. A linguagem está inteira na mesa: tipos, funções, SQL,
PDO, Composer, classes, exceções, tipagem estrita, enums, closures,
arquivos, datas e erros, dentro de um projeto que qualquer pessoa da
equipe sabe navegar. O volume 2 começa pelo que acontece entre o navegador
e o PHP — e só depois disso abre o Laravel, que vai parecer, em cada
pasta, uma versão maior do que está nesta árvore.
:::

:::summary
- Cada pasta responde a uma pergunta: `src/` faz, `config/` ajusta, `bin/`
  e `public/` são as portas, `var/` guarda o produzido, `tests/` confere.
- O servidor web enxerga só `public/`. Todo o resto fica fora da web.
- `autoload.files` carrega funções soltas; `scripts` dá nome aos comandos.
- Segredo no `.env`, fora do Git; forma no `config/`. Senha que já foi
  para o Git precisa ser trocada.
- O `bootstrap.php` é a raiz de composição: cria e liga os objetos, e os
  scripts só pedem.
- Um contêiner guarda fábricas e entrega serviços prontos, criados uma vez.
:::

:::checkpoint
Você organiza um projeto PHP em pastas com propósito, tira configuração e
segredo do código, monta os objetos num único ponto com um contêiner
simples, e sabe apontar, na estrutura de um projeto Laravel, o equivalente
de cada pasta deste capítulo.
:::

:::exercise level=1
Diga em que pasta do acervo cada arquivo deve ficar:

1. `Leitor.php`, a classe do leitor;
2. `recalcular-multas.php`, rodado uma vez por mês pelo agendador;
3. `relatorio-2026-03.csv`, gerado por esse script;
4. `biblioteca.php`, com os dias da semana em que a Casa Amarela abre;
5. o logotipo da biblioteca, que vai aparecer na tela.

:::answer
1. `src/Leitores/` — é o que o sistema sabe fazer.
2. `bin/` — é uma porta de linha de comando.
3. `var/` — foi produzido pelo programa, e não vai para o Git.
4. `config/` — é ajuste, e não segredo. Vai para o Git.
5. `public/` — é a única pasta que o navegador alcança. O logotipo é
   feito para ser visto.
:::

:::exercise level=2
Registre no `bootstrap.php` uma fábrica para o `Importador`, que recebe
um `PDO` e um `Registro` pelo construtor. Use o `$servicos` que a closure
recebe como argumento.

:::answer
```php
$servicos->registrar(
    Importador::class,
    fn(Servicos $s) => new Importador(
        $s->get(PDO::class),
        $s->get(Registro::class),
    ),
);
```

O `get` de `Servicos` chama cada fábrica passando o próprio contêiner —
o `$fabrica($this)` da linha do `??=`. É assim que uma fábrica pede outros
serviços sem conhecer as fábricas deles.

Repare no que essa fábrica tem de mecânico: ler o construtor, pedir cada
tipo ao contêiner, passar na ordem. Um programa conseguiria fazer isso
sozinho, lendo a assinatura do construtor. É exatamente o que o contêiner
do capítulo 3 do volume 2 faz.
:::

:::exercise level=3
O Cléber precisa rodar o acervo na máquina dele pela primeira vez. Ele
clona o repositório e roda `php bin/importar-doacoes.php`. Liste, na
ordem, os erros que ele vai encontrar e o que resolve cada um. Depois,
escreva as instruções que você poria num `README.md` para que o próximo
não encontre nenhum deles.

:::answer
Na ordem:

1. `Failed opening required '.../vendor/autoload.php'` — o `vendor/` não
   vai para o Git. Resolve com `composer install`.
2. Um erro do PDO por DSN vazio — o `.env` também não vai. O `env()`
   devolve `null`, e o `new PDO` recebe nada. Resolve com
   `cp .env.example .env` e os valores preenchidos.
3. Um erro de acesso negado ou de banco inexistente — o `.env` aponta
   para um banco que ainda não existe na máquina dele. Resolve criando o
   banco e rodando o SQL das tabelas.
4. Possivelmente, um erro ao gravar em `var/log/` — a pasta também está
   fora do Git. Resolve com `mkdir -p var/log`, ou com o `bootstrap.php`
   criando a pasta se ela faltar.

O `README.md`:

```text
Para rodar
1. composer install
2. cp .env.example .env    e preencha DB_*
3. mysql -u root -p < sql/esquema.sql
4. mkdir -p var/log
5. composer importar
```

Cinco linhas. O teste de um bom `README` é entregá-lo a alguém que nunca
viu o projeto e não ajudar. O Laravel automatiza boa parte disso — o
volume 2 mostra quanto —, mas o `README` continua sendo seu.
:::
