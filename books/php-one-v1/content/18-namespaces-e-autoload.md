---
title: "Namespaces e autoload"
number: 18
slug: namespaces-e-autoload
part: p3
kicker: "A importação precisava do livro antigo e do livro novo no mesmo programa. O segundo se chamou LivroNovo2."
goal: >-
  Dar endereço ao código com `namespace`, importar nomes com `use`, declarar
  o autoload PSR-4 no Composer e nunca mais escrever `require` de classe —
  incluindo o motivo pelo qual isso quebra só no servidor.
---

:::story LivroNovo2
Tainá estava lendo o `importar.php`, que lê o dump do Sistema e grava no
banco novo.

— Por que tem um `LivroNovo2`?

— Porque já tinha um `LivroNovo`.

— E o `LivroNovo` é o quê?

— O do Sistema. Com `quantidade`.

Tainá rolou até o topo do arquivo. Três classes: `Livro`, `LivroNovo` e
`LivroNovo2`.

— E o `Livro`?

— Esse é de 2019. Não usa mais.

— Então o novo é o dois.

— O novo é o dois.

Ela anotou no caderno, na página que já tinha `funcoes2_NOVO_final.php`
escrito com a mesma letra apertada de quem está tentando não rir.
:::

## Dois nomes iguais no mesmo programa

O problema do `LivroNovo2` não é falta de imaginação. É que o PHP só aceita
um `Livro` por vez:

```php title="importar.php" numbered
<?php

require 'Livro.php';        // o do acervo novo
require 'legado/Livro.php'; // o do dump do Sistema
```

```text
Fatal error: Cannot redeclare class Livro
(previously declared in /app/Livro.php:3)
in /app/legado/Livro.php on line 3
```

Estar em pastas diferentes não resolve. Para o PHP, os dois se chamam
`Livro`, e um nome só pode apontar para uma coisa.

É o mesmo erro do `formatarData()` — e por muito tempo a saída foi a mesma:
prefixo no nome. Foi assim que o PHP dos anos 2000 produziu classes como
`Zend_Db_Table_Row_Abstract`, que é um namespace escrito à mão, com
sublinhados no lugar da barra.

## Namespace é um endereço

```php title="Livro.php" numbered
<?php

namespace CasaAmarela\Acervo;

class Livro
{
    public function __construct(
        public string $titulo,
        public int $ano,
    ) {}
}
```

Uma linha nova, e o nome da classe mudou:

```php
echo Livro::class, "\n";
```

```text
CasaAmarela\Acervo\Livro
```

`Nome::class` devolve o nome completo de uma classe, e é a forma honesta de
descobrir com o que você está lidando. O nome real dessa classe não é
`Livro`: é `CasaAmarela\Acervo\Livro`. O `Livro` é só o pedaço final.

:::term Nome completo
*Fully Qualified Class Name*, abreviado FQCN na documentação e nas
mensagens de erro. É o endereço inteiro, com as barras invertidas: primeiro
o namespace, depois o nome da classe.

Duas classes com o mesmo nome final e endereços diferentes são duas classes
diferentes, e podem conviver no mesmo programa sem se ver.
:::

A regra de sintaxe é curta: `namespace` é a primeira instrução do arquivo,
depois do `<?php`, e vale para tudo que o arquivo declara.

E a regra de leitura é mais curta ainda: **namespace não é pasta**. É um
nome com pontuação, como um endereço postal. Nada no PHP obriga
`CasaAmarela\Acervo\Livro` a morar em `src/Acervo/Livro.php`.

Você vai fazer exatamente isso mesmo assim, por um motivo que aparece
daqui a três seções.

## Dentro de um namespace, o resto do mundo some

Ponha `namespace CasaAmarela\Acervo;` no topo de um arquivo que conecta ao
banco e rode:

```php
$pdo = new PDO($dsn, 'root', 'senha');
```

```text
Fatal error: Uncaught Error: Class "CasaAmarela\Acervo\PDO" not found
```

Esta é a primeira pedra em que todo mundo tropeça, e a mensagem entrega a
causa: o PHP procurou um `PDO` **dentro do endereço atual**. Não achou, e
parou. Ele não sai procurando pelo prédio inteiro.

A barra invertida na frente diz "a partir da raiz":

```php
$pdo = new \PDO($dsn, 'root', 'senha');
```

```text
conectado
```

:::key
Para **classes**, um nome sem barra é relativo ao namespace do arquivo.

Para **funções e constantes**, não: se o PHP não encontrar a função no
namespace atual, ele procura na raiz. É por isso que `strtoupper()`,
`date()` e `count()` continuam funcionando sem nenhuma barra dentro de um
arquivo com namespace.

Essa diferença é a razão de o seu código antigo continuar rodando depois de
ganhar a primeira linha de `namespace`, e de o `new PDO` ser a única coisa
que quebra.
:::

## `use`: apelidos para o arquivo inteiro

Escrever `\CasaAmarela\Acervo\Livro` toda vez seria pior que o
`LivroNovo2`. O `use` resolve o nome uma vez, no topo:

```php title="importar.php" numbered
<?php

use CasaAmarela\Acervo\Livro;
use CasaAmarela\Legado\Livro as LivroDoSistema;

$novo = new Livro('Vidas Secas', 1938);
$velho = new LivroDoSistema('Vidas Secas', 1938, 3);
```

Três coisas para guardar.

O `use` **não carrega nada**. Ele só diz: neste arquivo, quando eu escrever
`Livro`, quero dizer `CasaAmarela\Acervo\Livro`. É um apelido local.

O `as` dá um apelido diferente, e é a saída para o caso das duas classes com
o mesmo nome final. As duas convivem no mesmo arquivo, com nomes que você
escolheu — e o nome verdadeiro de cada uma continua sendo o endereço
completo.

E o `use` vale por arquivo. Não vale para o arquivo que incluiu, não vale
para o que for incluído. Cada um declara os seus.

:::pitfall
O erro mais comum com `use` não parece um erro de `use`:

```text
Fatal error: Uncaught Error:
Class "CasaAmarela\Acervo\Emprestimo" not found
```

O nome na mensagem está certo, o arquivo existe, a classe está lá — e a
causa é que você esqueceu o `use` num arquivo de outro namespace, então o
PHP procurou no endereço errado.

Leia a mensagem pelo **começo**, não pelo fim. O pedaço da frente é o
endereço em que ele procurou, e é ele que está errado.
:::

## PSR-4: a convenção que faz o resto sozinho

Namespace não é pasta — mas se você fingir que é, uma ferramenta consegue
adivinhar onde cada classe mora, e aí ninguém precisa escrever `require` de
classe nunca mais.

Essa é a PSR-4: uma convenção publicada pelo grupo que padroniza o
ecossistema PHP, e que quase todo projeto moderno segue.

```json title="composer.json"
    "autoload": {
        "psr-4": {
            "CasaAmarela\\": "src/"
        }
    }
```

Isso diz: tudo que começa com `CasaAmarela\` mora dentro de `src/`. O resto
do endereço vira caminho, e o nome da classe vira nome de arquivo com `.php`
no fim.

| Nome completo | Arquivo |
|---|---|
| `CasaAmarela\Acervo\Livro` | `src/Acervo/Livro.php` |
| `CasaAmarela\Acervo\Exemplar` | `src/Acervo/Exemplar.php` |
| `CasaAmarela\Leitores\Leitor` | `src/Leitores/Leitor.php` |
| `CasaAmarela\Legado\Livro` | `src/Legado/Livro.php` |

Tabela: O prefixo `CasaAmarela\` é trocado pela pasta `src/`; o que sobra
vira caminho, pedaço por pedaço.

Duas regras práticas saem daí. **Um arquivo, uma classe** — o autoload
procura um arquivo por nome, e dois nomes no mesmo arquivo deixam um deles
inalcançável. E **o arquivo se chama como a classe**, com a mesma caixa.

Depois de declarar, avise o Composer:

```text
$ composer dump-autoload
```

```text
Generating autoload files
Generated autoload files containing 4 classes
```

E o `importar.php` inteiro fica assim:

```php title="importar.php" numbered
<?php

require 'vendor/autoload.php';

use CasaAmarela\Acervo\Livro;
use CasaAmarela\Legado\Livro as LivroDoSistema;

$novo = new Livro('Vidas Secas', 1938);
$velho = new LivroDoSistema('Vidas Secas', 1938, 3);

echo $novo->titulo, ' / ', $velho->quantidade, "\n";
```

Um `require` só, o mesmo de todos os programas do projeto. As classes
aparecem quando são usadas.

## Quem encontrou essa classe?

Autoload não é mágica, e desconfiar dele é saudável até você ver o tamanho
da coisa. São seis linhas:

```php title="carregador.php" numbered
<?php

spl_autoload_register(function (string $classe): void {
    echo "procurando: $classe\n";
});

$x = new Naoexiste();
```

```text
procurando: Naoexiste

Fatal error: Uncaught Error: Class "Naoexiste" not found
```

`spl_autoload_register` guarda uma função para ser chamada **no momento em
que o PHP encontra um nome de classe que ainda não conhece**. A função
recebe o nome completo e tem uma única obrigação: se souber onde está,
carregar o arquivo. Se não carregar, o PHP segue para a próxima função
registrada e, se acabarem, dá o erro.

Um carregador PSR-4 mínimo cabe em oito linhas:

```php title="carregador.php" numbered
<?php

spl_autoload_register(function (string $classe): void {
    $prefixo = 'CasaAmarela\\';

    if (!str_starts_with($classe, $prefixo)) {
        return;
    }

    $resto = substr($classe, strlen($prefixo));
    $relativo = str_replace('\\', '/', $resto);
    $caminho = __DIR__ . '/src/' . $relativo . '.php';

    if (is_file($caminho)) {
        require $caminho;
    }
});
```

É isto que o `vendor/autoload.php` faz, com mais cuidado e para todos os
prefixos ao mesmo tempo — o seu e o de cada biblioteca instalada.

:::trivia
A sigla PSR é de *PHP Standard Recommendation*, numeradas pelo PHP-FIG, um
grupo formado por mantenedores de projetos grandes que cansaram de
bibliotecas incompatíveis.

A PSR-0 veio antes e ainda aceitava sublinhado no nome da classe como
separador de pasta, herança da época do `Zend_Db_Table`. A PSR-4 largou
isso. Foi a última vez que o ecossistema precisou combinar onde os arquivos
ficam.
:::

## `dump-autoload`, e quando ele é necessário

O Composer gera a lista de prefixos uma vez e guarda. Você precisa
regenerar quando **muda o mapa**, não quando muda o código:

| O que você fez | Precisa de `dump-autoload` |
|---|---|
| criou `src/Acervo/Autor.php` | não |
| editou uma classe | não |
| mudou o bloco `autoload` do `composer.json` | sim |
| instalou um pacote | não — o `require` já faz |

Tabela: No dia a dia, quase nunca. O comando existe para o dia em que você
mexeu no mapa.

Existe uma variação que aparece nos guias de deploy:

```text
$ composer dump-autoload --optimize
```

Em vez de adivinhar o caminho a cada classe nova, o Composer varre as pastas
e monta uma lista pronta de nome para arquivo. Fica mais rápido, porque
troca uma consulta ao disco por uma consulta à memória.

O custo é o outro lado da mesma moeda: classe criada depois da varredura não
está na lista. Numa máquina de desenvolvimento, isso é uma armadilha
gratuita. Em produção, onde o código não muda entre um deploy e outro, é
ganho puro.

## Funciona no meu Windows

Falta a pedra que só aparece no servidor.

:::pitfall
`CasaAmarela\Acervo\Livro` procura por `src/Acervo/Livro.php`. Se o arquivo
se chamar `livro.php`, com `l` minúsculo:

- no **Windows** e no **macOS**, o sistema de arquivos ignora a caixa das
  letras e entrega o arquivo assim mesmo. Funciona;
- no **Linux**, `livro.php` e `Livro.php` são dois arquivos diferentes. Um
  deles não existe.

O resultado é o defeito que mais consome uma tarde de sexta: tudo funciona
na máquina de quem escreveu, e a tela quebra no servidor com
`Class not found` apontando um nome que está visivelmente correto.

A regra que evita: o arquivo se chama exatamente como a classe, e a pasta
exatamente como o pedaço do namespace. Quando o Git já registrou o nome
errado, renomear só a caixa exige dois passos —
`git mv livro.php Livro.php.tmp` e depois `git mv Livro.php.tmp Livro.php` —
porque o Git, na sua máquina, também acha que os dois nomes são o mesmo.
:::

## A estrutura que o projeto passa a ter

As classes saem da raiz e vão para `src/`, divididas por **assunto do
domínio** — acervo, leitores, legado —, não por tipo técnico. Uma pasta
chamada `Classes/` ou `Helpers/` só empurra a pergunta "onde isso mora?"
para dentro dela.

:::tree title="Onde estamos agora"
acervo/
  composer.json    # com o bloco autoload
  composer.lock
  vendor/
  .gitignore
  src/
    Acervo/
      Livro.php      # CasaAmarela\Acervo\Livro
      Exemplar.php   # CasaAmarela\Acervo\Exemplar
    Leitores/
      Leitor.php     # CasaAmarela\Leitores\Leitor
    Legado/
      Livro.php      # CasaAmarela\Legado\Livro
  conexao.php
  importar.php
  listar.php
  emprestar.php
  recibo.php
:::

:::note Na sua carreira
Num projeto legado você vai encontrar os dois mundos no mesmo repositório:
uma pasta moderna com PSR-4 e uma pasta antiga cheia de `require`. A
tentação é propor "migrar tudo" numa sprint.

A migração que costuma passar é outra: registre o autoload para o código
novo, escreva tudo que for novo lá dentro, e mova um arquivo antigo cada vez
que precisar mexer nele de qualquer jeito. Em seis meses a pasta antiga
encolheu sem que ninguém tenha aberto um chamado chamado "refatoração".

Serve para quase toda dívida técnica: a proposta que sobrevive à reunião de
prioridades não é a que pede uma semana, é a que pede meia hora por vez e
mostra número depois.
:::

:::summary
- Duas classes com o mesmo nome não convivem; pasta diferente não ajuda.
- `namespace` dá endereço à classe. O nome real passa a ser o endereço
  inteiro, e `Nome::class` mostra qual é.
- Dentro de um namespace, nome de classe sem barra é relativo — por isso
  `new \PDO`. Função e constante caem na raiz sozinhas.
- `use` cria um apelido para o arquivo; `use ... as` resolve o conflito de
  nomes finais iguais.
- PSR-4 troca um prefixo de namespace por uma pasta: um arquivo por classe,
  com o mesmo nome e a mesma caixa.
- `spl_autoload_register` é o gancho que o PHP chama ao encontrar um nome
  desconhecido; o `vendor/autoload.php` é isso, feito direito.
- `dump-autoload` só quando o mapa muda; `--optimize` em produção, nunca na
  sua máquina.
- Caixa errada no nome do arquivo funciona no Windows e quebra no Linux.
:::

:::checkpoint
Você declara namespaces, importa classes com `use`, sabe por que `new PDO`
quebra dentro de um namespace, configura o `autoload` PSR-4 no
`composer.json` e consegue criar uma classe nova que é encontrada sem
nenhum `require`.
:::

:::exercise level=1
Para cada nome completo, diga em qual arquivo ele mora, considerando o
mapeamento `"CasaAmarela\\": "src/"`:

1. `CasaAmarela\Emprestimos\Emprestimo`
2. `CasaAmarela\Acervo\Busca\Filtro`
3. `CasaAmarela\Multa`

E depois o contrário: que nome completo tem a classe declarada em
`src/Relatorios/Mensal.php`?

:::answer
1. `src/Emprestimos/Emprestimo.php`
2. `src/Acervo/Busca/Filtro.php`
3. `src/Multa.php`

O prefixo `CasaAmarela\` some e vira `src/`; cada barra restante vira uma
pasta; o último pedaço vira o arquivo.

No sentido contrário, `src/Relatorios/Mensal.php` corresponde a
`CasaAmarela\Relatorios\Mensal` — e o arquivo precisa declarar
`namespace CasaAmarela\Relatorios;` no topo. Se ele declarar outra coisa, o
autoload carrega o arquivo e o PHP continua dizendo que a classe não existe,
porque carregar o arquivo certo e encontrar o nome certo são duas condições,
não uma.
:::

:::exercise level=2
Mova as classes do capítulo anterior para `src/`, seguindo a tabela da seção
de PSR-4, e faça o `listar.php` funcionar com um único `require`.

Depois apague, de propósito, a linha `use` do `listar.php` e leia a
mensagem. Diga qual pedaço dela aponta a causa.

:::answer
O `composer.json` ganha:

```json title="composer.json"
    "autoload": {
        "psr-4": {
            "CasaAmarela\\": "src/"
        }
    }
```

Cada classe ganha o namespace no topo:

```php title="src/Acervo/Livro.php" numbered
<?php

namespace CasaAmarela\Acervo;

class Livro
{
    public function __construct(
        public string $titulo,
        public int $ano,
    ) {}
}
```

E o programa:

```php title="listar.php" numbered
<?php

require 'vendor/autoload.php';
require 'conexao.php';

use CasaAmarela\Acervo\Livro;

$linhas = $pdo->query('SELECT titulo, ano FROM livros')->fetchAll();

foreach ($linhas as $linha) {
    $livro = new Livro($linha['titulo'], (int) $linha['ano']);
    echo $livro->titulo, "\n";
}
```

Sem o `use`, a mensagem é:

```text
Fatal error: Uncaught Error: Class "Livro" not found
```

O pedaço que aponta a causa é o nome entre aspas: veio **sem endereço**.
Como o `listar.php` não tem `namespace`, o PHP procurou `Livro` na raiz, e
não existe classe nenhuma chamada só `Livro` — a que você escreveu se chama
`CasaAmarela\Acervo\Livro`.
:::

:::exercise level=3
Uma equipe relata o seguinte: a tela de recibo funciona na máquina de todos
os três desenvolvedores e quebra em produção, sempre, com
`Class "CasaAmarela\Recibos\Gerador" not found`. O arquivo
`src/Recibos/Gerador.php` está no repositório e tem o namespace certo.

Levante pelo menos três causas possíveis e diga, para cada uma, uma
conferência que a confirma ou descarta em menos de um minuto.

:::answer
**Caixa do nome.** O arquivo pode estar como `src/recibos/Gerador.php` ou
`src/Recibos/gerador.php` no repositório, e as três máquinas serem Windows
ou macOS. Confere com `git ls-files src/Recibos` — que mostra o nome como o
Git guardou, não como o disco local mostra.

**Autoload otimizado com lista velha.** Se o deploy roda
`dump-autoload --optimize` antes de copiar o arquivo novo, a lista pronta
não tem a classe. Confere procurando o nome dentro de
`vendor/composer/autoload_classmap.php` no servidor.

**Arquivo fora do pacote publicado.** Um `.gitignore` largo demais — uma
linha `recibos/` pensada para PDFs gerados, por exemplo — pode estar
excluindo a pasta inteira. Confere com `git check-ignore -v src/Recibos` na
máquina de quem escreveu.

Uma quarta, menos comum e que vale a conferência porque custa cinco
segundos: o bloco `autoload` do `composer.json` foi alterado e não foi
comitado. `git status` na máquina de quem mexeu responde.

O que essas quatro têm em comum, e é por isso que a pergunta é útil: nenhuma
delas é um defeito no código da classe. Quando o erro só acontece em um
ambiente, o suspeito é o que difere entre os ambientes — sistema de
arquivos, passo de build e o que foi de fato enviado.
:::
