---
title: "O que é HTTP"
number: 1
slug: o-que-e-http
part: p1
kicker: "O aplicativo enviava os dados. O servidor recebia os dados. E o $_POST estava vazio."
goal: >-
  Ler uma troca HTTP inteira com `curl -v`, saber exatamente o que o PHP
  enxerga de uma requisição, entender por que `$_POST` fica vazio com JSON
  e escrever um endpoint cru que recebe e devolve JSON sem framework.
---

:::story Ele não manda nada
A Tainá tinha ligado uma cópia do aplicativo do Kauã no acervo, para
testar. Ele cadastrava empréstimo e recebia sempre a mesma resposta:
*"exemplar não informado"*.

— Ele não manda nada — disse Tainá. — Olha aqui, o `$_POST` chega vazio.

— Vazio como?

— Vazio. `array(0)`.

Dedé pediu para ela rodar o pedido de novo, mas pela linha de comando, com
uma opção que ele soletrou letra por letra.

```text
> POST /emprestimos HTTP/1.1
> Content-Type: application/json
> Content-Length: 34
>
{"exemplar_id":812,"leitor_id":47}
```

— Está mandando — disse Tainá.

— Está.

— Mas o `$_POST`...

— O `$_POST` não é o que o aplicativo mandou. É o que o PHP resolveu
guardar lá.
:::

## A troca inteira, em texto

HTTP é texto que vai e texto que volta. A opção `-v` do `curl` mostra as
duas metades: as linhas que começam com `>` saíram da sua máquina, as que
começam com `<` voltaram do servidor.

```text
$ curl -v -X POST http://localhost:8000/emprestimos \
       -H "Content-Type: application/json" \
       -d '{"exemplar_id":812}'
```

```text
> POST /emprestimos HTTP/1.1
> Host: localhost:8000
> User-Agent: curl/8.18.0
> Accept: */*
> Content-Type: application/json
> Content-Length: 19
>
< HTTP/1.1 201 Created
< Date: Mon, 21 Sep 2026 20:29:51 GMT
< X-Powered-By: PHP/8.4.2
< Content-Type: application/json
<
```

As duas metades têm a mesma forma: uma primeira linha diferente, uma lista
de cabeçalhos, uma linha em branco e um corpo opcional.

Na ida, a primeira linha traz verbo, caminho e versão. Na volta, traz a
versão, o número e o nome do status.

:::key
A linha em branco não é formatação: é a fronteira. Tudo antes dela são
cabeçalhos; tudo depois é corpo.

É por isso que qualquer `echo` acidental antes de um `header()` estraga a
resposta inteira — o PHP entende que o corpo começou, e os cabeçalhos que
vierem depois não têm mais para onde ir.
:::

## Os sete status que você vai usar

```text
< HTTP/1.1 201 Created
```

O número é o que o outro programa lê; o texto ao lado é cortesia para
humanos.

| Código | Quando | O corpo |
|---|---|---|
| `200` | deu certo, aqui está | o recurso |
| `201` | criei, e está aqui | o recurso criado |
| `204` | feito, nada a dizer | vazio |
| `400` | o pedido está malformado | o motivo |
| `401` | não sei quem é você | o motivo |
| `404` | não existe | o motivo |
| `422` | entendi o pedido e ele é inválido | quais campos |

Tabela: Sete cobrem a API inteira deste livro. Os outros existem e são
raros.

## O que o PHP enxerga

Todo esse texto chega ao seu programa já separado em três variáveis que
existem sozinhas, sem você declarar nada.

```php title="api.php" numbered
<?php

declare(strict_types=1);

header('Content-Type: application/json');

echo json_encode([
    'metodo' => $_SERVER['REQUEST_METHOD'],
    'caminho' => $_SERVER['REQUEST_URI'],
    'tipo' => $_SERVER['CONTENT_TYPE'] ?? '(ausente)',
    'get' => $_GET,
    'post' => $_POST,
], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
```

Rode o servidor que vem junto com o PHP e mande um formulário comum:

```text
$ php -S localhost:8000 api.php
```

```text
$ curl -X POST http://localhost:8000/emprestimos \
       -d "exemplar_id=812&leitor_id=47"
```

```text
{
    "metodo": "POST",
    "caminho": "/emprestimos",
    "tipo": "application/x-www-form-urlencoded",
    "get": [],
    "post": {
        "exemplar_id": "812",
        "leitor_id": "47"
    }
}
```

:::term Superglobal
Variável que existe em qualquer lugar do programa sem ser declarada nem
recebida: `$_GET`, `$_POST`, `$_SERVER`, `$_FILES`, `$_COOKIE`.

Elas são a forma mais antiga de o PHP entregar a requisição, e a mais
frágil, porque qualquer linha de qualquer arquivo pode lê-las — e
escrevê-las.
:::

Repare nos valores: `"812"`, entre aspas. Tudo que chega por HTTP é texto,
inclusive o que parece número. A conversão é trabalho seu, e o lugar dela é
a fronteira de entrada.

## Por que o `$_POST` estava vazio

Agora o mesmo pedido, com JSON:

```text
$ curl -X POST http://localhost:8000/emprestimos \
       -H "Content-Type: application/json" \
       -d '{"exemplar_id":812,"leitor_id":47}'
```

```text
{
    "metodo": "POST",
    "caminho": "/emprestimos",
    "tipo": "application/json",
    "get": [],
    "post": []
}
```

O aplicativo do Kauã estava certo, e o `$_POST` também.

O PHP preenche o `$_POST` a partir do corpo **apenas quando o
`Content-Type` é um dos dois formatos de formulário**:
`application/x-www-form-urlencoded`, que é o do exemplo anterior, e
`multipart/form-data`, que é o de envio de arquivo. Com qualquer outro
tipo, ele não tenta adivinhar: deixa o corpo intacto e o `$_POST` vazio.

O corpo continua lá, inteiro, num lugar com nome esquisito:

```php title="api.php" numbered
$bruto = file_get_contents('php://input');

$dados = json_decode($bruto, true);

echo $dados['exemplar_id'], "\n";
```

```text
812
```

`php://input` é um fluxo de leitura com o corpo cru da requisição, do
primeiro ao último byte, sem interpretação nenhuma. `json_decode` com o
segundo argumento `true` devolve array associativo em vez de objeto.

:::pitfall
Este é, com folga, o primeiro defeito de quem escreve API em PHP: o
aplicativo manda JSON, o servidor lê `$_POST`, e a resposta é "campo
obrigatório" para um campo que foi enviado.

O sintoma engana porque **o erro está no servidor e a suspeita cai no
cliente**. Antes de acusar quem manda, rode `curl -v`: se a linha
`Content-Type` e o corpo estão lá, o problema é de quem lê.
:::

## Cabeçalhos que mudam o comportamento

A maioria dos cabeçalhos é informação. Três decidem o que acontece.

**`Content-Type`** diz em que formato o corpo **está escrito**. É ele que
acabou de decidir se o `$_POST` seria preenchido.

**`Accept`** diz o que o cliente **aceita receber**. Um cliente que manda
`Accept: application/json` está dizendo que não quer a sua página de erro em
HTML — e devolver HTML mesmo assim é o que faz um aplicativo mostrar uma
tela branca em vez da mensagem.

**`Authorization`** carrega a credencial. Sai assim, e o `$_SERVER` traduz o
nome trocando o traço por sublinhado e acrescentando o prefixo `HTTP_`:

```text
> Authorization: Bearer abc123
```

```php
$_SERVER['HTTP_AUTHORIZATION']
```

Na resposta, quem escreve cabeçalho é a função `header()`, e o status é o
`http_response_code()`:

```php
header('Content-Type: application/json');
http_response_code(201);
```

## O servidor não lembra de você

HTTP é **sem estado**: cada requisição chega sozinha, sem nenhuma memória da
anterior. O servidor não sabe quem você é, o que você acabou de fazer nem
que existe uma tela aberta do outro lado.

Isso é o mesmo modelo que o capítulo @cap:o-php-que-voce-ouviu-falar
descreveu por dentro — cada requisição começa do zero e morre no fim —
agora visto de fora, no protocolo.

A consequência prática: **tudo que o servidor precisa lembrar tem que vir
junto no pedido, ou estar guardado em algum lugar fora dele.** O navegador
resolve isso reenviando um cookie a cada requisição; o PHP usa esse cookie
para reencontrar um arquivo de sessão no disco do servidor. Uma API costuma
resolver de outro jeito, mandando a credencial no `Authorization` a cada
chamada.

Os dois são a mesma ideia: a requisição carrega a identidade, porque a
conexão não carrega nada.

## Um endpoint cru

Junte tudo. Sem framework, sem biblioteca, sessenta linhas de nada:

```php title="api.php" numbered
<?php

declare(strict_types=1);

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['erro' => 'Use POST']);
    exit;
}

$tipo = $_SERVER['CONTENT_TYPE'] ?? '';

if (!str_starts_with($tipo, 'application/json')) {
    http_response_code(415);
    echo json_encode(['erro' => 'Envie application/json']);
    exit;
}

$dados = json_decode(file_get_contents('php://input'), true);

if (!is_array($dados)) {
    http_response_code(400);
    echo json_encode(['erro' => 'JSON inválido']);
    exit;
}

$faltando = [];

foreach (['exemplar_id', 'leitor_id'] as $campo) {
    if (!isset($dados[$campo])) {
        $faltando[] = $campo;
    }
}

if ($faltando !== []) {
    http_response_code(422);
    echo json_encode([
        'erro' => 'Campos obrigatórios',
        'campos' => $faltando,
    ]);
    exit;
}

http_response_code(201);

echo json_encode([
    'id' => 4471,
    'exemplar_id' => (int) $dados['exemplar_id'],
    'leitor_id' => (int) $dados['leitor_id'],
]);
```

:::http title="A troca que esse arquivo atende"
POST /emprestimos
Content-Type: application/json

{"exemplar_id": 812, "leitor_id": 47}
---
201 Created
Content-Type: application/json

{
  "id": 4471,
  "exemplar_id": 812,
  "leitor_id": 47
}
:::

Duas coisas para reparar antes de seguir.

A primeira: o `405` e o `415` existem porque o arquivo responde a **um**
caminho e **um** verbo. Um programa que atende vários precisa decidir qual
código roda, e essa decisão tem nome — é a única coisa que falta aqui para
isso virar um sistema.

A segunda: os `(int)` na resposta. O que chegou era texto; o que sai é
número. A fronteira converte, e é por isso que ela é o único lugar do
programa que precisa saber que HTTP existe.

:::note Na sua carreira
"O cliente não está mandando" e "o servidor não está recebendo" são a mesma
discussão vista de dois lados, e ela consome tardes inteiras porque cada
lado olha só para o próprio log.

O que encerra em dois minutos é uma troca de `curl -v`: quem acusa cola a
saída inteira, com a linha da requisição, os cabeçalhos e o corpo. A partir
daí não há mais opinião — ou o `Content-Length` é zero, ou não é.

Aprenda a ler essa saída antes de precisar dela numa reunião com o time do
aplicativo. É a diferença entre participar da conversa e esperar a
conclusão.
:::

:::summary
- Requisição e resposta são texto com a mesma forma: primeira linha,
  cabeçalhos, linha em branco, corpo.
- A linha em branco é a fronteira; `echo` antes de `header()` a antecipa e
  estraga a resposta.
- Sete status cobrem a API inteira: `200`, `201`, `204`, `400`, `401`,
  `404` e `422`.
- `$_GET`, `$_POST` e `$_SERVER` são superglobais, e tudo que chega por elas
  é texto.
- O `$_POST` só é preenchido com `x-www-form-urlencoded` e
  `multipart/form-data`; com JSON, o corpo está em `php://input`.
- `Content-Type` diz como o corpo está escrito; `Accept`, o que o cliente
  aceita receber; `Authorization` carrega a credencial.
- HTTP é sem estado: a identidade viaja em cada requisição, porque a
  conexão não guarda nada.
- `header()` escreve cabeçalho e `http_response_code()` define o status.
:::

:::checkpoint
Você lê uma troca inteira em `curl -v` e explica cada linha, sabe dizer sem
testar se um `$_POST` vai chegar preenchido, lê o corpo cru de uma
requisição JSON e escreve um endpoint que devolve o status certo para pedido
malformado, campo faltando e sucesso.
:::

:::exercise level=1
Para cada situação, diga qual status a resposta deve ter:

1. O empréstimo foi registrado com sucesso.
2. O leitor 913 não existe no cadastro.
3. O corpo chegou com `leitor_id` mas sem `exemplar_id`.
4. O cliente mandou o corpo em XML.
5. A devolução foi registrada e não há nada para devolver no corpo.

:::answer
1. `201` — criou um recurso novo.
2. `404` — o recurso pedido não existe.
3. `422` — o pedido está bem formado e o conteúdo é inválido. Não é `400`:
   o JSON estava correto, a regra é que não foi cumprida.
4. `415` — o formato do corpo não é aceito. Também não é `400`, e a
   diferença importa para o cliente saber se deve corrigir o dado ou o
   cabeçalho.
5. `204` — feito, sem corpo. Devolver `200` com `{}` funciona e obriga o
   cliente a interpretar um corpo vazio de propósito.

O par que mais confunde é o 3 e o 4 contra o `400`. Uma régua que resolve:
`400` é "não consegui nem entender o pedido"; `415` é "entendi o formato e
não aceito"; `422` é "entendi tudo e o conteúdo está errado".
:::

:::exercise level=2
Acrescente ao `api.php` o tratamento do verbo `GET` em `/emprestimos/{id}`,
devolvendo `200` com o empréstimo ou `404` se o número não existir.

Use estes dados fixos no lugar do banco:

```php
$emprestimos = [
    4471 => ['exemplar_id' => 812, 'leitor_id' => 47],
];
```

:::answer
```php title="api.php" numbered
<?php

declare(strict_types=1);

header('Content-Type: application/json');

$emprestimos = [
    4471 => ['exemplar_id' => 812, 'leitor_id' => 47],
];

$caminho = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

if ($_SERVER['REQUEST_METHOD'] === 'GET'
    && preg_match('#^/emprestimos/(\d+)$#', $caminho, $partes)) {

    $id = (int) $partes[1];

    if (!isset($emprestimos[$id])) {
        http_response_code(404);
        echo json_encode(['erro' => "Empréstimo {$id} não existe"]);
        exit;
    }

    echo json_encode(['id' => $id] + $emprestimos[$id]);
    exit;
}

http_response_code(404);
echo json_encode(['erro' => 'Rota não encontrada']);
```

Três detalhes que decidem se isso funciona.

`parse_url(..., PHP_URL_PATH)` separa o caminho da consulta. Sem ele,
`/emprestimos/4471?formato=curto` não casaria com a expressão, e o cliente
receberia `404` por ter mandado um parâmetro a mais.

A expressão exige `\d+` e ancora nas duas pontas. Sem as âncoras,
`/velhos/emprestimos/4471/extra` também casaria.

E o `(int)` na conversão do número: `$partes[1]` é texto, como tudo que vem
da URL, e `$emprestimos` tem chaves inteiras. `isset($emprestimos['4471'])`
com string funciona por conversão automática de chave — funciona por
acidente, e acidente não é desenho.
:::

:::exercise level=3
Um aplicativo relata que a API do acervo "às vezes devolve HTML". O time da
API garante que devolve JSON sempre.

Os dois estão certos. Levante três situações em que uma API PHP devolve HTML
sem que ninguém tenha escrito HTML, e diga como evitar cada uma.

:::answer
**Um: erro fatal com `display_errors` ligado.** Um `TypeError` não tratado
faz o PHP imprimir a mensagem e a pilha. Se o servidor estiver configurado
para formatar isso em HTML, o cliente recebe uma página no meio do que devia
ser JSON — muitas vezes **depois** de um pedaço do JSON já ter sido enviado.

Evita-se com `display_errors` desligado no servidor e um tratador de
exceções registrado que responda em JSON com status `500`.

**Dois: o servidor web respondendo antes do PHP.** `404` de rota inexistente,
`413` de corpo grande demais, `502` quando o PHP não respondeu — nenhuma
dessas passa pelo seu código, e o padrão do servidor é uma página HTML.

Evita-se configurando as páginas de erro do servidor para o formato da API,
e é o tipo de coisa que só aparece quando alguém testa o caminho ruim.

**Três: saída antes do `header()`.** Uma linha em branco depois do `?>` num
arquivo incluído, um `echo` de depuração esquecido, um aviso impresso. O PHP
manda os cabeçalhos padrão, que incluem `Content-Type: text/html`, e o seu
`header()` chega tarde:

```text
Warning: Cannot modify header information - headers already sent
```

Evita-se não fechando o `?>` em arquivo que só tem PHP — e é por isso que
essa regra existe.

O que as três têm em comum vale mais que as três: **o caminho de erro da sua
API precisa ser testado como o caminho de sucesso**. Quase todo time testa o
`201` e descobre o formato do `500` em produção.
:::
