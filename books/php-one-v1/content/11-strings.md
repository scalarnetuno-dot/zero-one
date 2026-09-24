---
title: "Strings"
number: 11
slug: strings
part: p1
kicker: "Metade dos defeitos de um sistema brasileiro mora na distância entre um caractere e um byte."
goal: >-
  Escolher entre aspas simples e duplas com critério, manipular texto
  acentuado sem quebrá-lo, formatar valores para leitura humana, e tratar
  toda entrada como texto até provar o contrário.
---

:::story Os três José de Alencar
Vera chamou a Tainá no balcão com a expressão de quem vai mostrar uma coisa
que já cansou de mostrar.

— Procura Alencar aí.

Tainá digitou. Apareceram três autores:

```text
José de Alencar          412 títulos
JosÃ© de Alencar          38 títulos
JOSE DE ALENCAR           11 títulos
```

— São a mesma pessoa — disse Vera. — Faz uns seis anos.

O primeiro veio do cadastro normal. O segundo apareceu depois de uma
migração de banco em 2019, quando alguém exportou em UTF-8 e importou como
se fosse Latin-1. O terceiro veio dos quatro computadores da sala de leitura,
que têm teclado sem cedilha desde uma licitação de 2021 — os atendentes
aprenderam a digitar tudo em maiúscula e sem acento, porque "assim sempre
acha".

— E ninguém juntou?

— Juntaram uma vez. Aí voltou.
:::

Os três José de Alencar são o mesmo defeito em três roupas: um texto
gravado com uma codificação e lido com outra, um texto digitado sem acento,
e um texto com espaço a mais. Nenhum dos três dá erro. Os três partem a
busca da Vera em pedaços.

## O nome que chegou quebrado

```text
$ php -r 'echo strlen("José"), "\n";'
5
```

Quatro letras, cinco bytes. O `é` em UTF-8 ocupa dois.

Isso não é curiosidade acadêmica. É a causa direta de títulos cortados no
meio, campos de banco estourando, alinhamento de relatório errado e aquele
losango com uma interrogação dentro.

```text
$ php -r 'echo substr("José de Alencar", 0, 4), "\n";'
Jos�
```

`substr` cortou no meio do `é`. Sobrou meio caractere, que não é caractere
nenhum, e o terminal desenha o símbolo de substituição.

:::term Mojibake
O nome do fenômeno em que `José` vira `JosÃ©`: um texto codificado em UTF-8
sendo interpretado como Latin-1. Os dois bytes do `é` passam a ser lidos
como dois caracteres separados. A palavra é japonesa e significa,
literalmente, "transformação de caractere".
:::

## Um caractere pode ocupar dois bytes

O PHP tem duas famílias de funções de texto. A antiga trabalha com **bytes**.
A família `mb_` — de *multibyte* — trabalha com **caracteres**.

| Byte (evite) | Caractere (use) |
|---|---|
| `strlen` | `mb_strlen` |
| `substr` | `mb_substr` |
| `strtoupper` | `mb_strtoupper` |
| `strtolower` | `mb_strtolower` |
| `str_pad` | não tem equivalente direto |

Tabela: A extensão `mbstring` precisa estar instalada. Foi por isso que o
capítulo @cap:o-que-vamos-construir pediu para conferir a lista do `php -m`
antes de qualquer coisa.

```text
$ php -r 'echo mb_strlen("José"), "\n";'
4
$ php -r 'echo mb_substr("José de Alencar", 0, 4), "\n";'
José
$ php -r 'echo mb_strtoupper("josé"), "\n";'
JOSÉ
```

O último é o que mais pega gente desprevenida: `strtoupper("josé")` devolve
`JOSé`, com o acento em minúscula, porque a função só conhece o alfabeto
ASCII.

:::key
Regra operacional: **em texto que pode ter acento, use `mb_`**. Nome,
título, endereço, observação. As funções de byte continuam certas para o que
é garantidamente ASCII — um ISBN, um código, um hash — e são mais rápidas, o
que só importa em volume muito alto.
:::

## Texto com intenção

```php title="aspas.php" numbered
<?php

$titulo = 'O Cortiço';

echo 'Título: $titulo', "\n";
echo "Título: $titulo", "\n";
echo "Título: {$titulo}", "\n";
```

```text
Título: $titulo
Título: O Cortiço
Título: O Cortiço
```

Aspas **simples** não interpretam nada: o que está escrito é o que sai —
inclusive `$titulo` e `\n` literais. Aspas **duplas** interpolam variáveis e
reconhecem sequências de escape.

As chaves em `{$titulo}` são opcionais no caso simples e obrigatórias assim
que a expressão cresce:

```php title="chaves.php" numbered
<?php

echo "Tombo: {$exemplar['tombo']}\n";
echo "Primeiro: {$valores[0]}\n";
echo "Multa: {$multas['total_em_centavos']}\n";
```

:::key
A recomendação prática: use `{$...}` **sempre** que interpolar, mesmo quando
puder omitir. Custa dois caracteres, elimina a categoria inteira de dúvida
sobre onde o nome da variável termina, e evita o defeito clássico de
`"$titulo_completo"` procurar uma variável chamada `$titulo_completo` quando
você queria `$titulo` seguido de `_completo`.
:::

### Heredoc

Para texto longo, existe uma forma que dispensa escapar aspas:

```php title="heredoc.php" numbered
<?php

$nome = 'Marlene';
$dias = 9;

$mensagem = <<<TEXTO
    Olá, {$nome}.

    O livro "O Cortiço" está com {$dias} dias de atraso.
    A multa acumulada é de R$ 7,20.

    Casa Amarela
    TEXTO;

echo $mensagem, "\n";
```

O identificador de fechamento define a indentação: tudo que estiver alinhado
com ele é removido de cada linha. Isso permite manter o texto recuado junto
com o código, sem que o recuo apareça na saída.

Existe também `<<<'TEXTO'`, com aspas simples — o **nowdoc** —, que não
interpola nada. É o equivalente de aspas simples para texto longo.

:::warning
Heredoc é confortável demais para montar SQL, e é exatamente aí que ele
mata. Isto é uma falha de segurança, não um estilo ruim:

```php
$sql = <<<SQL
    SELECT * FROM livro WHERE titulo LIKE '%{$termo}%'
    SQL;
```

Se `$termo` vier de um campo de busca, quem digitar `' OR 1=1 --` fecha a
aspa, acrescenta a própria condição e lê a tabela inteira. O comando deixou
de ser um comando e virou um formulário em branco para o visitante
preencher.

A forma correta manda o valor **separado** do comando, de modo que ele nunca
possa ser lido como instrução. A regra vale desde já e vale para tudo: **não
interpole dado externo dentro de SQL, de HTML nem de comando de
terminal.**
:::

## O recibo cortado no meio

```php title="recibo.php" numbered
<?php

function linhaDoRecibo(string $titulo, int $centavos): string
{
    $titulo = str_pad(substr($titulo, 0, 30), 30);
    $valor = number_format($centavos / 100, 2, ',', '.');

    return $titulo . str_pad($valor, 10, ' ', STR_PAD_LEFT);
}

echo linhaDoRecibo('Memórias Póstumas de Brás Cubas', 720), "\n";
echo linhaDoRecibo('O Cortiço', 720), "\n";
```

```text
Memórias Póstumas de Brás Cub      7,20
O Cortiço                       7,20
```

Duas coisas erradas na mesma saída.

O primeiro título foi cortado em trinta **bytes**, não trinta caracteres —
por isso ele some antes do esperado, e, com outro título, cortaria um acento
ao meio.

E o alinhamento da segunda linha está visivelmente fora. `str_pad` completou
até trinta bytes; como `Cortiço` tem um caractere de dois bytes, a coluna
ficou um caractere mais curta que a de cima. Numa impressora térmica de
balcão, isso é uma coluna desalinhada em todo recibo com acento — ou seja,
em quase todos.

## Por que o alinhamento saiu torto

Porque **alinhamento é uma operação visual sobre caracteres**, e as duas
funções usadas contam bytes. As duas coisas coincidem em inglês e divergem em
português, o que faz o defeito passar por qualquer teste escrito com
`"Test"` e `"Example"`.

E há uma segunda camada: mesmo `mb_str_pad` — que só existe a partir do PHP
8.3 — não resolve o caso geral, porque alguns caracteres ocupam **duas
colunas** na tela mesmo sendo um caractere só. Emoji e ideogramas fazem isso.
Para alinhamento perfeito existe `mb_strwidth`.

## Normalize na entrada, escape na saída

```php title="recibo_correto.php" numbered
<?php

function linhaDoRecibo(string $titulo, int $centavos): string
{
    if (mb_strlen($titulo) > 30) {
        $titulo = mb_substr($titulo, 0, 29) . '…';
    }

    $valor = number_format($centavos / 100, 2, ',', '.');

    return sprintf('%-30s %9s', $titulo, $valor);
}
```

```text
Memórias Póstumas de Brás Cub…      7,20
O Cortiço                          7,20
```

Três mudanças. O corte usa `mb_substr` e deixa um caractere de reticências,
que sinaliza a truncagem para quem lê. O alinhamento usa `sprintf` com
largura declarada, o que é mais legível que dois `str_pad` encadeados. E
`%-30s` alinha à esquerda, `%9s` à direita — o formato do recibo fica
declarado numa linha só, em vez de espalhado em três.

:::anatomy title="O mini-idioma do `sprintf`"
lang: text
code: |
  sprintf('%-30s %9s %05d %.2f %%', $t, $v, $n, $f)
notes:
  - { line: 1, text: "`%s` é texto, `%d` inteiro, `%f` decimal." }
  - { line: 1, text: "O número é a largura mínima: `%9s` reserva nove colunas." }
  - { line: 1, text: "O `-` alinha à esquerda; sem ele, alinha à direita." }
  - { line: 1, text: "`%05d` completa com zeros: útil para tombo e código." }
  - { line: 1, text: "`%%` imprime um `%` literal." }
:::

Para dinheiro, porém, `sprintf` não basta. `number_format` é quem conhece
separador de milhar e de decimal:

```php
echo number_format(123456.7, 2, ',', '.');   // 123.456,70
```

:::pitfall
`number_format` devolve **string**, e arredonda. Formatar é a última coisa
que acontece com um valor, na saída — nunca no meio do cálculo. Somar
`"123.456,70"` com outro valor formatado é o tipo de erro que produz um
total plausível e errado.
:::

## Buscar, trocar e normalizar

```php title="busca.php" numbered
<?php

$titulo = '  O   Cortiço  ';

$limpo = trim($titulo);
$limpo = preg_replace('/\s+/u', ' ', $limpo);

var_dump($limpo);
var_dump(str_contains($limpo, 'Cort'));
var_dump(str_starts_with($limpo, 'O '));
var_dump(str_ends_with($limpo, 'ço'));
```

```text
string(10) "O Cortiço"
bool(true)
bool(true)
bool(true)
```

`str_contains`, `str_starts_with` e `str_ends_with` chegaram no PHP 8 e
substituíram o idioma antigo `strpos($a, $b) !== false`, que era correto e
confundia todo mundo por causa da posição zero.

O `preg_replace('/\s+/u', ' ', ...)` colapsa espaços repetidos. O
modificador `u` no fim da expressão é obrigatório quando o texto tem acento
— sem ele, a expressão trabalha byte a byte e pode partir um caractere.

E a normalização que resolveria os três José de Alencar:

```php title="normalizar.php" numbered
<?php

function chaveDeBusca(string $texto): string
{
    $texto = mb_strtolower(trim($texto));
    $texto = preg_replace('/\s+/u', ' ', $texto);

    return transliterator_transliterate(
        'Any-Latin; Latin-ASCII; Lower()',
        $texto
    );
}

var_dump(chaveDeBusca('JOSÉ  DE ALENCAR'));
var_dump(chaveDeBusca('José de Alencar'));
```

```text
string(15) "jose de alencar"
string(15) "jose de alencar"
```

`transliterator_transliterate` vem da extensão `intl` e remove acentos de
forma correta — bem mais confiável que as tabelas de `str_replace` que
circulam na internet, que esquecem metade dos casos.

:::key
A chave de busca é **guardada ao lado** do texto original, nunca no lugar
dele. A Casa Amarela mostra "José de Alencar" e procura por "jose de
alencar".

Dois campos, dois trabalhos: um serve para a pessoa ler, o outro serve para
o programa comparar. Tentar fazer as duas coisas com um campo só é
exatamente o que produziu os três cadastros.
:::

:::note Na sua carreira
Sistema em português tem uma classe de defeitos que sistema em inglês não
tem, e ela quase nunca aparece em tutorial. Acento, cedilha, ç maiúsculo,
ordenação alfabética que coloca "Ávila" depois de "Zanetti", CPF com
zero à esquerda virando número, CEP idem.

Isso é conhecimento de mercado local e vale mais do que parece numa
entrevista. Quando alguém perguntar "que problema difícil você já
resolveu?", "três cadastros do mesmo autor por causa de codificação" é uma
resposta muito melhor que um algoritmo de árvore binária — porque é real, é
específica, e mostra que você já lidou com dado sujo de verdade.
:::

## Tudo que entra é texto

```php
$_GET['pagina'];      // string "2"
$_POST['dias'];       // string "9"
file_get_contents();  // string
fgetcsv();            // array de strings
```

Formulário, query string, arquivo, corpo de requisição, variável de
ambiente: tudo chega como texto. O `"2"` que parece número é `string`, e vai
se comportar como string em todo lugar que não converter.

Converter na **borda** — logo na entrada, uma vez, num lugar só — é o que
faz o resto do programa trabalhar com tipos de verdade:

```php
$pagina = (int) ($_GET['pagina'] ?? 1);
$dias = (int) ($_POST['dias'] ?? 0);
```

Depois dessas duas linhas, `$pagina` e `$dias` são números em todo o resto
do programa, e nenhuma função adiante precisa desconfiar. Sem elas, o `"2"`
viaja como texto até encontrar o primeiro `===` e responder errado.

:::summary
- Aspas simples são literais; duplas interpolam. Use `{$var}` sempre.
- Heredoc para texto longo — e nunca para montar SQL.
- `strlen` conta bytes; `mb_strlen` conta caracteres.
- Em texto que pode ter acento, use a família `mb_`.
- `sprintf` declara o formato numa linha; `number_format` formata dinheiro.
- Formatar é a última operação, na saída, nunca no meio do cálculo.
- Guarde a chave de busca normalizada **ao lado** do texto original.
- Tudo que entra é texto; converta na borda.
:::

:::milestone
Fim da Parte 1. Você tem tipos, decisões, laços, funções, arrays e texto —
o PHP inteiro que um programa precisa antes de virar projeto. A partir do
próximo capítulo, um arquivo deixa de ser suficiente.
:::

:::exercise level=1
Escreva uma função que formate centavos como moeda brasileira, devolvendo
`R$ 1.234,56`.

:::answer
```php
<?php

function reais(int $centavos): string
{
    return 'R$ ' . number_format($centavos / 100, 2, ',', '.');
}

echo reais(123456), "\n";
```
```text
R$ 1.234,56
```
:::

:::exercise level=2
Escreva `resumo(string $texto, int $limite): string`, que corte o texto no
limite de **caracteres** sem partir uma palavra, acrescentando `…`. Se
couber inteiro, devolva como está.

:::answer
```php
<?php

function resumo(string $texto, int $limite): string
{
    $texto = trim($texto);

    if (mb_strlen($texto) <= $limite) {
        return $texto;
    }

    $corte = mb_substr($texto, 0, $limite);
    $ultimoEspaco = mb_strrpos($corte, ' ');

    if ($ultimoEspaco !== false) {
        $corte = mb_substr($corte, 0, $ultimoEspaco);
    }

    return rtrim($corte) . '…';
}
```
O `!== false` em vez de `if ($ultimoEspaco)` é obrigatório: `mb_strrpos`
devolve `0` quando o espaço está na primeira posição, e zero é falso. Um
título que comece com uma palavra de uma letra só perderia o corte — e é
por isso que as funções de posição do PHP têm fama de confundir.
:::

:::exercise level=3
A Casa Amarela quer unificar os três "José de Alencar" sem perder nada.
Descreva o procedimento, incluindo o que você faria **antes** de alterar
qualquer registro.

:::answer
**Antes de tudo: backup, e um backup restaurado.** Não o arquivo gerado —
a restauração testada num banco separado. Uma unificação errada é
irreversível, e "temos backup" é uma frase que só significa alguma coisa
depois que alguém restaurou um.

**Passo 1 — medir, sem alterar nada.** Rode a normalização sobre a lista
inteira de autores, em memória, e agrupe pela chave gerada:

```php
$por_chave = [];

foreach ($autores as $autor) {
    $chave = chaveDeBusca($autor['nome']);
    $por_chave[$chave][] = $autor['nome'];
}

foreach ($por_chave as $chave => $nomes) {
    if (count($nomes) > 1) {
        echo $chave, ': ', implode(' | ', $nomes), "\n";
    }
}
```

`implode` junta os itens de um array num texto, separados pelo que você
passar. O resultado responde quantos casos existem de verdade — e a resposta
costuma ser desconfortável. Podem ser três José de Alencar e mais duzentos
que ninguém notou.

**Passo 2 — escolher o registro canônico, com regra escrita.** A regra que
eu usaria: vence o nome com acentuação correta e maior número de títulos
ligados. Ela precisa estar escrita porque alguém vai auditar, e porque casos
ambíguos vão aparecer.

**Passo 3 — repontar as referências, numa transação.** Todos os títulos dos
registros duplicados passam a apontar para o canônico, e os duplicados são
**desativados**, não apagados. Preservar permite desfazer e permite
responder "por que o título X mudou de autor em novembro".

**Passo 4 — impedir a volta.** Este é o passo que faltou da outra vez, e é a
razão de a Vera ter dito "aí voltou". Sem ele, a unificação é um mutirão que
se repete a cada dois anos:

- coluna `chave` gerada pela normalização, com restrição `UNIQUE`;
- normalização acontecendo na **borda** de entrada, em um lugar só;
- e o cadastro sugerindo o autor existente quando a chave bate — o que
  resolve o problema social, não só o técnico. O atendente do teclado sem
  cedilha continua digitando sem cedilha, e o sistema o leva ao registro
  certo.

**O que eu não faria:** corrigir o mojibake com `str_replace('Ã©', 'é')`. Isso
resolve os casos que você viu e deixa os que você não viu, e cria um
segundo formato errado quando alguém reexecuta em texto já corrigido. A
conversão certa é `mb_convert_encoding` na importação — e, se o dado já está
gravado errado, uma migração única que identifica exatamente os registros
afetados antes de tocá-los.
:::

:::story Quatrocentos e sessenta e um
Um mês depois, com a chave de busca no ar, Vera testou.

Digitou "alencar". Vieram 461 títulos, de um autor só.

Digitou "ALENCAR". Mesma coisa.

Digitou "  alencar  ", com espaço dos dois lados, olhando para a Tainá.

Mesma coisa.

— Agora digita errado — disse Tainá.

Vera digitou "alencr".

Nada.

— Esse não acha.

— Mas eu sei quem eu quero.

— O sistema não sabe.

Vera anotou no caderno, na seção "para perguntar depois", que já tinha
quatro linhas.

Na sexta, Márcia leu a seção inteira em voz alta na reunião de status,
demorando no fim de cada item.

— São quatro. A gente entrega duas até março.

— E as outras duas?

— Ficam escritas. Escrito é melhor do que na cabeça da Vera.
:::
