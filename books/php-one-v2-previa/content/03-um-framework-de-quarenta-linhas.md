---
title: "Um framework de quarenta linhas"
number: 3
slug: um-framework-de-quarenta-linhas
part: p1
kicker: "Depois de escrever o roteador, a pergunta da estagiária foi a melhor do projeto: por que não usar este e pronto?"
goal: >-
  Escrever à mão o mínimo de um framework — front controller, roteador,
  contêiner e middleware — para conseguir explicar o ciclo de uma
  requisição em qualquer framework PHP, apontando onde cada peça entra.
---

:::story Vinte minutos
A pasta `public/`, vazia no fim do volume 1, tinha dezenove arquivos
`.php` duas semanas depois, e o endereço de cada tela terminava em um deles.

— Isso vira `/emprestar.php?tombo=2117` — disse Tainá. — O aplicativo vai
consumir assim?

— Não. Vira `POST /emprestimos`.

— E como?

Dedé puxou o teclado e começou a escrever. Vinte minutos depois havia um
arquivo com quarenta e poucas linhas, e as três rotas da biblioteca
respondiam JSON.

Tainá leu o arquivo inteiro, de cima a baixo, sem interromper.

— Tá. Por que a gente não usa esse e pronto?
:::

## Um arquivo por página

O projeto da Casa Amarela cresceu do jeito mais natural do mundo: uma tela,
um arquivo. É como o PHP foi feito para funcionar, e é o motivo de a
linguagem ter conquistado a web.

Três coisas quebram quando o projeto passa de uma dúzia de arquivos.

**O endereço vira mapa do disco.** `/emprestar.php` conta a quem estiver do
lado de fora como a pasta está organizada, e amarra a URL ao nome do
arquivo. Renomear vira mudança de contrato.

**Cada arquivo repete o começo.** Conexão, autoload, cabeçalho de resposta,
conferência de credencial. Dezenove vezes, e no dia em que uma delas mudar,
dezenove lugares para lembrar.

**Não existe um lugar para o que vale para todos.** Registrar quanto tempo
cada requisição levou, recusar quem não está autenticado, devolver JSON
quando o programa quebra: cada um desses é uma linha que precisaria estar em
todos os dezenove arquivos.

## Front controller: uma porta só

A saída é antiga e tem nome: **toda requisição entra pelo mesmo arquivo**,
que decide o que fazer.

```text
antes                          depois
/emprestar.php?tombo=2117      POST /emprestimos
/listar.php                    GET  /livros
/recibo.php?id=4471            GET  /emprestimos/4471/recibo
                               ↓
                               tudo entra por index.php
```

Para o servidor entregar tudo a um arquivo só, ele precisa de uma
instrução. No Apache, é um arquivo de configuração na pasta pública:

```text title=".htaccess"
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^ index.php [L]
```

As duas últimas linhas dizem: se o caminho pedido **não** for um arquivo que
existe — uma imagem, um CSS —, mande para o `index.php`. É por isso que todo
projeto PHP moderno tem uma pasta `public/` com quase nada dentro: só o
`index.php` e os arquivos que devem mesmo ser servidos direto.

No servidor embutido do PHP, a mesma coisa se faz na linha de comando:

```text
$ php -S localhost:8000 mini.php
```

## Um roteador em vinte linhas

Com tudo entrando por uma porta, falta decidir para onde vai. Duas classes,
e a primeira tem três linhas:

```php title="mini.php" numbered
<?php

declare(strict_types=1);

final class Resposta
{
    public function __construct(
        public readonly int $status,
        public readonly array $corpo,
    ) {}
}
```

```php title="mini.php" numbered
final class Roteador
{
    public function __construct(private array $rotas) {}

    public function despachar(
        string $metodo,
        string $caminho,
    ): Resposta {
        foreach ($this->rotas as [$verbo, $padrao, $acao]) {
            if ($verbo !== $metodo) {
                continue;
            }

            $regex = '#^' . preg_replace(
                '#\{(\w+)\}#',
                '(?<$1>[^/]+)',
                $padrao,
            ) . '$#';

            if (preg_match($regex, $caminho, $achados) === 1) {
                $parametros = array_filter(
                    $achados,
                    'is_string',
                    ARRAY_FILTER_USE_KEY,
                );

                return $acao(...array_values($parametros));
            }
        }

        return new Resposta(404, ['erro' => 'Rota não encontrada']);
    }
}
```

O laço é simples; a única linha que merece atenção é a que monta a expressão
regular. Ela troca `{id}` por um grupo com nome que casa com qualquer coisa
que não seja barra. `/livros/{id}` vira `#^/livros/(?<id>[^/]+)$#`.

Depois do casamento, `$achados` traz os pedaços duas vezes: com índice
numérico e com o nome. O `array_filter` com `ARRAY_FILTER_USE_KEY` fica só
com os de nome — e eles viram os argumentos da função da rota.

:::term Despachar
Escolher qual código roda para uma requisição e chamá-lo. É a única coisa
que um roteador faz, e é a peça que todo framework tem no meio.

Tabela de rotas de um lado, requisição do outro, uma função no fim.
:::

A tabela de rotas é um array, e cada linha tem verbo, padrão e o que fazer:

```php title="mini.php" numbered
$acervo = [
    12 => ['titulo' => 'Dom Casmurro', 'ano' => 1899],
    31 => ['titulo' => 'Vidas Secas', 'ano' => 1938],
];

$rotas = [
    ['GET', '/livros',
        fn(): Resposta => new Resposta(200, $acervo)],

    ['GET', '/livros/{id}',
        function (string $id) use ($acervo): Resposta {
            $id = (int) $id;

            if (!isset($acervo[$id])) {
                return new Resposta(404, [
                    'erro' => "Livro {$id} não existe",
                ]);
            }

            return new Resposta(200, ['id' => $id] + $acervo[$id]);
        }],

    ['POST', '/emprestimos',
        fn(): Resposta => new Resposta(201, ['id' => 4471])],
];
```

E o front controller, que é o fim do arquivo, tem seis linhas:

```php title="mini.php" numbered
function enviar(Resposta $r): void
{
    http_response_code($r->status);
    header('Content-Type: application/json');
    echo json_encode($r->corpo, JSON_UNESCAPED_UNICODE);
}

$roteador = new Roteador($rotas);

enviar($roteador->despachar(
    $_SERVER['REQUEST_METHOD'],
    parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH),
));
```

Suba e experimente:

```text
$ php -S localhost:8000 mini.php
```

```text
$ curl -s localhost:8000/livros/31
{"id":31,"titulo":"Vidas Secas","ano":1938}

$ curl -s localhost:8000/livros/99
{"erro":"Livro 99 não existe"}

$ curl -s localhost:8000/nada
{"erro":"Rota não encontrada"}
```

:::key
Repare no que o roteador **não** é: um `switch` gigante com `$_SERVER` lá
dentro.

A diferença não é estética. Um `switch` mistura a decisão de rota com o
trabalho de cada rota, e cresce junto com as duas. Aqui a decisão está numa
classe que não sabe nada sobre livros, e o trabalho está numa tabela que não
sabe nada sobre expressões regulares.

Trocar o roteador por outro não toca em nenhuma rota. É essa separação que
faz a palavra "framework" significar alguma coisa.
:::

## O contêiner ingênuo

O projeto tem classes que dependem de outras: um serviço de empréstimo
precisa de um repositório, que precisa de uma conexão. Montar isso à mão em
cada rota é a repetição de sempre:

```php
$servico = new ServicoDeEmprestimo(
    new RepositorioDeLivros(
        new Conexao()
    )
);
```

O `Servicos` do capítulo @cap:como-organizar-um-projeto-php resolveu isso
com uma fábrica escrita à mão para cada classe — e o exercício 2 daquele
capítulo já apontava o que as fábricas têm de mecânico: ler o construtor,
pedir cada tipo, passar na ordem. Um contêiner que lê o construtor
sozinho dispensa as fábricas. Quinze linhas resolvem para sempre:

```php title="mini.php" numbered
final class Container
{
    private array $feitos = [];

    public function obter(string $classe): object
    {
        if (isset($this->feitos[$classe])) {
            return $this->feitos[$classe];
        }

        $construtor = (new ReflectionClass($classe))
            ->getConstructor();

        $argumentos = [];

        foreach ($construtor?->getParameters() ?? [] as $p) {
            $tipo = $p->getType();

            if (!$tipo instanceof ReflectionNamedType
                || $tipo->isBuiltin()) {
                throw new RuntimeException(
                    "Não sei construir \${$p->getName()}"
                );
            }

            $argumentos[] = $this->obter($tipo->getName());
        }

        return $this->feitos[$classe]
            = new $classe(...$argumentos);
    }
}
```

`ReflectionClass` é a parte do PHP que permite ao programa **olhar para o
próprio código**: quais métodos uma classe tem, quais parâmetros um método
recebe, de que tipo cada um é. O contêiner usa isso para ler a lista de
parâmetros do construtor e resolver cada um, recursivamente.

```php
$c = new Container();

$servico = $c->obter(ServicoDeEmprestimo::class);
```

```text
  (conexao criada)
```

Uma linha, e a corrente inteira foi montada. Peça de novo:

```php
$outro = $c->obter(ServicoDeEmprestimo::class);

var_dump($servico === $outro);
```

```text
bool(true)
```

Nenhuma conexão nova. O contêiner guarda o que já construiu, e é por isso
que uma única `Conexao` atende o programa inteiro sem ninguém passar o
`$pdo` de função em função.

:::pitfall
O contêiner acima é ingênuo de propósito, e o limite aparece rápido:

```text
Não sei construir $status
```

Ele só sabe resolver parâmetros que são **classes**. Um `int`, uma `string`
ou uma configuração vinda de arquivo não têm como ser adivinhados — alguém
precisa dizer o que colocar ali.

Guardar essa frase vale mais que o código: quando um framework reclamar que
não consegue resolver uma dependência, é quase sempre isto. Um parâmetro que
não é classe, ou uma interface sem ninguém ter dito qual implementação usar.
:::

## Middleware: a cebola antes de ter nome

Falta o lugar de pôr o que vale para todas as rotas. A ideia é embrulhar a
ação em camadas: cada camada recebe a requisição, faz a parte dela, chama a
de dentro e ainda vê a resposta voltando.

```php title="mini.php" numbered
$acao = fn(string $req): string => "[acao:{$req}]";

$middlewares = [
    fn(string $req, callable $proximo): string
        => 'log(' . $proximo($req) . ')',

    fn(string $req, callable $proximo): string
        => 'auth(' . $proximo($req) . ')',
];

$pipeline = array_reduce(
    array_reverse($middlewares),
    fn(callable $proximo, callable $atual): callable
        => fn(string $req): string => $atual($req, $proximo),
    $acao,
);

echo $pipeline('GET /livros'), "\n";
```

```text
log(auth([acao:GET /livros]))
```

A saída **é** o desenho. O `log` embrulha o `auth`, que embrulha a ação. A
requisição entra de fora para dentro e a resposta sai de dentro para fora,
passando pelas mesmas camadas na ordem inversa.

O `array_reduce` com a lista invertida é o que monta essa boneca. Cada passo
pega o que já foi montado — o "próximo" — e o embrulha na camada atual.

E o ganho prático aparece quando uma camada decide **não** chamar a
seguinte:

```php
fn(string $req, callable $proximo): string
    => autenticado($req) ? $proximo($req) : '401',
```

Aí a ação nunca roda. É assim que autenticação, limite de requisições e
recusa por permissão funcionam em todo framework PHP — e a partir daqui
nenhum deles precisa explicar o mecanismo para você.

## O que ainda falta

O arquivo tem umas cem linhas contando tudo, e atende três rotas. Vale
listar, sem pressa, o que ele não faz:

| Falta | O que dá errado sem isso |
|---|---|
| validação de entrada | cada rota confere na mão, e uma esquece |
| tratamento central de erro | um `TypeError` vira HTML no meio do JSON |
| camada de banco com migração | o esquema mora na cabeça de alguém |
| autenticação de verdade | não há sessão, token nem hash de senha |
| respostas padronizadas | cada rota inventa o formato do erro |
| testes com requisição falsa | só dá para testar subindo servidor |
| tarefas fora da requisição | e-mail atrasa a resposta do usuário |
| cache, log, fila | tudo vira arquivo em `/tmp` |
| documentação | o contrato existe só no código |

Tabela: Cada linha dessa tabela é um trabalho de dias, e nenhuma delas é
específica da Casa Amarela — é exatamente a mesma lista em qualquer projeto
web do mundo.

## O que você acabou de entender

As quatro peças deste capítulo não são uma simplificação didática de um
framework. São a **forma** de todos eles.

```text
requisição
   ↓
front controller        index.php
   ↓
middlewares             camada, camada, camada
   ↓
roteador                qual função roda
   ↓
contêiner               monta o que a função precisa
   ↓
sua função              a única parte que é sua
   ↓
resposta                volta pelas camadas
```

Quando um framework falar em *kernel*, *pipeline*, *service provider* ou
*route model binding*, o vocabulário vai ser novo e o desenho não. Ele vai
ser este, com mais cuidado, mais casos tratados e mais anos de correção em
cima.

:::note Na sua carreira
Você vai ouvir, em algum momento, que "framework é para quem não sabe fazer
na mão". A resposta não é discordar — é concordar e continuar a frase.

Fazer na mão levou vinte minutos e produziu cem linhas que atendem três
rotas e não tratam erro, não validam, não autenticam e não têm um teste.
Completar a tabela da seção anterior é um ano de trabalho, e o resultado
seria um framework pior e com um mantenedor só.

O que este capítulo comprou não foi independência: foi a capacidade de
**ler** o framework. Quando algo der errado três camadas abaixo do seu
código, você vai saber que camadas são essas — e essa é a diferença entre
abrir um chamado e abrir o arquivo.
:::

:::tree title="Onde estamos agora"
acervo/
  mini.php          # front controller, roteador, contêiner, middleware
  src/
    Acervo/
    Circulacao/
    Emprestimos/
    Leitores/
  composer.json
  phpstan.neon
:::

:::summary
- Um arquivo por página amarra a URL ao disco, repete o começo em todo
  arquivo e não deixa lugar para o que vale para todos.
- Front controller faz tudo entrar por `index.php`; o servidor precisa de
  uma regra de reescrita para isso.
- Roteador é uma tabela de rotas, um casamento de padrão e uma chamada —
  e não sabe nada sobre o domínio.
- `{id}` no padrão vira grupo com nome na expressão, e o grupo vira
  argumento.
- Contêiner usa reflexão para ler os parâmetros do construtor e montar a
  corrente de dependências, guardando o que já construiu.
- Contêiner ingênuo só resolve parâmetro que é classe; o resto alguém
  precisa declarar.
- Middleware embrulha a ação em camadas; a camada que não chama a próxima
  interrompe a requisição.
- O que falta no arquivo de cem linhas é, item por item, o que um framework
  entrega.
:::

:::checkpoint
Você explica o ciclo de uma requisição em qualquer framework PHP apontando
onde entram front controller, middleware, roteador e contêiner; escreve um
roteador com parâmetro de caminho; e sabe dizer por que um contêiner não
consegue resolver certa dependência.
:::

:::exercise level=1
Acrescente ao `mini.php` a rota `DELETE /livros/{id}`, que devolve `204` sem
corpo quando o livro existe e `404` quando não existe.

Depois explique por que o `enviar()` precisa de um ajuste.

:::answer
```php
    ['DELETE', '/livros/{id}',
        function (string $id) use ($acervo): Resposta {
            $id = (int) $id;

            if (!isset($acervo[$id])) {
                return new Resposta(404, [
                    'erro' => "Livro {$id} não existe",
                ]);
            }

            return new Resposta(204, []);
        }],
```

O `enviar()` precisa de ajuste porque, como está, ele sempre imprime o corpo
— e `json_encode([])` produz `[]`, dois caracteres. Uma resposta `204` com
dois bytes de corpo contraria o próprio status, e alguns clientes tratam
isso como resposta malformada.

```php
function enviar(Resposta $r): void
{
    http_response_code($r->status);

    if ($r->status === 204) {
        return;
    }

    header('Content-Type: application/json');
    echo json_encode($r->corpo, JSON_UNESCAPED_UNICODE);
}
```

Repare onde a correção mora: no envio, não na rota. Se cada rota precisasse
lembrar de não imprimir nada, uma delas esqueceria — e é a mesma razão que
justifica o front controller existir.
:::

:::exercise level=2
O roteador atual casa `{id}` com qualquer coisa que não seja barra. Isso faz
`GET /livros/abc` entrar na rota e chegar em `(int) 'abc'`, que é `0`.

Acrescente ao padrão a possibilidade de exigir um formato, para que
`/livros/{id:\d+}` só case com dígitos — e `/livros/abc` devolva `404` sem
nunca chamar a função.

:::answer
A troca é na linha que monta a expressão:

```php
$regex = '#^' . preg_replace_callback(
    '#\{(\w+)(?::([^}]+))?\}#',
    fn(array $p): string
        => '(?<' . $p[1] . '>' . ($p[2] ?? '[^/]+') . ')',
    $padrao,
) . '$#';
```

O padrão agora reconhece duas formas: `{id}`, sem restrição, e `{id:\d+}`,
com. O `preg_replace_callback` é necessário porque a substituição passou a
depender do que foi encontrado — com o `preg_replace` simples não havia como
escolher entre o formato informado e o padrão.

A rota vira:

```php
['GET', '/livros/{id:\d+}', ...]
```

E `/livros/abc` não casa com nenhuma rota, caindo no `404` do fim do laço.

Vale reparar no que isso é: a primeira **validação** do mini framework, e
ela acontece antes da função da rota existir. É por isso que todo framework
oferece algo parecido — a alternativa é toda rota começar com um `if` que
confere o formato do próprio endereço.
:::

:::exercise level=3
Junte as peças: faça o `mini.php` usar o contêiner e uma cadeia de dois
middlewares de verdade.

O primeiro middleware mede quanto tempo a requisição levou e acrescenta o
cabeçalho `X-Tempo`. O segundo recusa com `401` qualquer requisição sem o
cabeçalho `Authorization`, **exceto** `GET`.

Escreva o código e diga em que ordem os dois devem ficar na lista, e por
quê.

:::answer
```php title="mini.php" numbered
$medirTempo = function (array $req, callable $proximo): Resposta {
    $comeco = hrtime(true);

    $resposta = $proximo($req);

    $ms = (hrtime(true) - $comeco) / 1_000_000;
    header(sprintf('X-Tempo: %.1fms', $ms));

    return $resposta;
};

$exigirCredencial = function (array $req, callable $seg): Resposta {
    if ($req['metodo'] !== 'GET'
        && !isset($_SERVER['HTTP_AUTHORIZATION'])) {
        return new Resposta(401, ['erro' => 'Credencial ausente']);
    }

    return $seg($req);
};

$acao = fn(array $req): Resposta => $roteador->despachar(
    $req['metodo'],
    $req['caminho'],
);

$pipeline = array_reduce(
    array_reverse([$medirTempo, $exigirCredencial]),
    fn(callable $proximo, callable $atual): callable
        => fn(array $req): Resposta => $atual($req, $proximo),
    $acao,
);

enviar($pipeline([
    'metodo' => $_SERVER['REQUEST_METHOD'],
    'caminho' => parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH),
]));
```

**A ordem é medição primeiro, credencial depois**, e o motivo é o que cada
uma faz com a resposta.

O middleware de tempo precisa ser a camada mais de fora para medir **tudo**,
inclusive o tempo gasto recusando alguém. Se ele estivesse por dentro, as
requisições rejeitadas com `401` sairiam sem `X-Tempo` — e são justamente as
que você vai querer medir no dia em que alguém estiver martelando a API.

O de credencial precisa estar por fora da ação e por dentro da medição: ele
interrompe, e interromper cedo é o ponto. Uma requisição sem credencial não
deve chegar ao roteador, muito menos ao banco.

A régua geral, que serve para qualquer cadeia: **o que observa fica por
fora; o que recusa fica logo em seguida; o que trabalha fica no meio.**
:::
