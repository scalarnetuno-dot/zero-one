---
title: "Arrays"
number: 8
slug: arrays
part: p1
kicker: "A estrutura mais usada do PHP é também a mais mal usada — e uma linha dela já derrubou o aplicativo de alguém."
goal: >-
  Entender o que um array PHP realmente é, escolher entre lista e mapa,
  dominar as funções que resolvem quase tudo, e reconhecer o momento em que
  o array virou um objeto disfarçado.
---

:::story A gente não mudou nada
Segunda-feira, 8h50. A Tainá abriu o chat da Casa Amarela e havia catorze
mensagens da Vera, todas antes das oito da manhã.

O aplicativo do leitor não mostrava mais a lista do acervo. Tela vazia, sem
erro, sem nada.

— A gente não mudou nada no fim de semana — disse Dedé.

Tecnicamente verdade. Na sexta ele tinha acrescentado um filtro para esconder
os exemplares em restauro. Três linhas. A API continuava respondendo `200`, o
JSON continuava chegando, o campo continuava com o nome certo.

Só que na sexta o JSON era assim:

```json
[{"tombo": 812}, {"tombo": 907}]
```

E na segunda era assim:

```json
{"0": {"tombo": 812}, "2": {"tombo": 907}}
```

O aplicativo esperava uma lista. Recebeu um objeto. Não quebrou — só não
achou nada para percorrer, e desenhou a tela vazia com muita competência.
:::

Três linhas, nenhum erro, e o aplicativo de mil e duzentos leitores parou. A
cabem numa frase: **em
PHP, lista e dicionário são o mesmo tipo — e o JSON não perdoa isso.**

## Uma palavra para duas estruturas

Em quase toda linguagem existem duas estruturas separadas. Python tem `list`
e `dict`. JavaScript tem `Array` e `Object`. Java tem `List` e `Map`.

PHP tem `array`. Um só, para os dois usos.

```php title="dois_usos.php" numbered
<?php

$tombos = [812, 907, 344];

$exemplar = [
    'tombo' => 812,
    'status' => 'disponivel',
];

var_dump($tombos, $exemplar);
```

```text
array(3) {
  [0]=> int(812)
  [1]=> int(907)
  [2]=> int(344)
}
array(2) {
  ["tombo"]=> int(812)
  ["status"]=> string(11) "disponivel"
}
```

Repare no primeiro: as chaves `0`, `1`, `2` existem. Elas sempre existiram —
você é que não as escreveu. Uma "lista" em PHP é um mapa cujas chaves por
acaso são os inteiros começando em zero, em ordem.

:::term Array em PHP
Um **mapa ordenado**: pares chave→valor que mantêm a ordem de inserção. A
chave é `int` ou `string`. Não existe estrutura de lista separada — o que
chamamos de lista é uma convenção sobre as chaves, não um tipo diferente.
:::

:::history
Essa decisão é de 1997, quando o PHP 3 estava sendo escrito por Andi Gutmans
e Zeev Suraski. Ter uma estrutura só simplificava o interpretador e a vida
de quem escrevia, numa época em que a maior parte do PHP do mundo processava
formulários — onde tudo chega como pares nome→valor.

Funcionou por vinte anos. O que ninguém previu, em 1997, é que essa mesma
estrutura seria serializada para um formato, o JSON, que **distingue** os
dois casos. O defeito da história de abertura tem a idade da linguagem.
:::

## A lista que virou objeto

O `json_encode` toma a decisão sozinho, e o critério é rígido:

```php title="a_regra.php" numbered
<?php

echo json_encode([1, 2, 3]), "\n";
echo json_encode([0 => 1, 1 => 2, 2 => 3]), "\n";
echo json_encode([0 => 1, 2 => 3]), "\n";
echo json_encode([1 => 1, 2 => 2]), "\n";
```

```text
[1,2,3]
[1,2,3]
{"0":1,"2":3}
{"1":1,"2":2}
```

A regra: vira array JSON **apenas** se as chaves forem exatamente `0, 1, 2,
…, n-1`, nessa ordem, sem buraco. Qualquer outra coisa vira objeto.

Existe uma função que responde isso desde o PHP 8.1:

```text
$ php -r 'var_dump(array_is_list([1, 2, 3]));'
bool(true)
$ php -r 'var_dump(array_is_list([0 => 1, 2 => 3]));'
bool(false)
```

## Arrumar o acervo na memória

```php title="funcoes.php" numbered
<?php

$exemplares = [
    ['tombo' => 812, 'livro_id' => 3, 'status' => 'disponivel'],
    ['tombo' => 907, 'livro_id' => 3, 'status' => 'restauro'],
    ['tombo' => 344, 'livro_id' => 7, 'status' => 'disponivel'],
];

$tombos = array_column($exemplares, 'tombo');

$porTombo = array_column($exemplares, null, 'tombo');

$livros = array_unique(array_column($exemplares, 'livro_id'));

$livres = array_filter(
    $exemplares,
    fn(array $e): bool => $e['status'] === 'disponivel'
);

$total = count($livres);
```

| Função | Responde |
|---|---|
| `array_column` | "me dê só essa coluna" |
| `array_column` com 3º argumento | "indexe por essa chave" |
| `array_filter` | "quais passam nesse critério" |
| `array_map` | "transforme cada um assim" |
| `array_unique` | "sem repetição" |
| `in_array` / `array_key_exists` | "isso está aí?" |
| `usort` | "ordene por esse critério" |

Tabela: `array_column($lista, null, 'id')` é o idioma mais útil da tabela:
transforma uma lista num mapa indexado, e mata o N+1 do capítulo
@cap:repeticoes na memória.

:::practice
Rode `print_r(array_column($exemplares, null, 'tombo'))` e olhe a saída. O
array deixou de ter chaves 0, 1, 2 e passou a ter 812, 907, 344. Guarde essa
imagem: é exatamente essa transformação que permite trocar uma busca linear
por um acesso direto.
:::

## Três linhas e uma tela vazia

Aqui está o que o Dedé escreveu na sexta:

```php title="o_filtro_da_sexta.php" numbered
<?php

$exemplares = buscarExemplares($livroId);

$exemplares = array_filter(
    $exemplares,
    fn(array $e): bool => $e['status'] !== 'restauro'
);

echo json_encode(['exemplares' => $exemplares]);
```

`array_filter` **preserva as chaves originais**. Se o item do meio foi
removido, o que sobra tem chaves `0` e `2` — e o `json_encode` olha para
isso, não encontra a sequência, e produz um objeto.

```text
{"exemplares":{"0":{"tombo":812},"2":{"tombo":344}}}
```

O servidor respondeu `200`. O JSON era válido. Nenhum log registrou nada.

## O índice que ficou para trás

Porque o defeito estava numa **conversão implícita entre duas linguagens**,
e não dentro de nenhuma das duas.

Do lado do PHP, tudo certo: `array_filter` fez exatamente o que documenta
fazer há vinte anos. Do lado do JavaScript, tudo certo também: ele recebeu um
objeto e tratou como objeto.

O erro aconteceu na fronteira — e fronteiras são onde moram os defeitos que
ninguém consegue reproduzir, porque cada lado, testado sozinho, está certo.

:::key
Esse é o padrão mais importante deste capítulo, e ele vale além de PHP:
**quando o dado atravessa uma fronteira, alguém precisa garantir a forma.**
No capítulo @cap:api-resources isso vira uma camada dedicada, cujo trabalho
único é decidir o formato do que sai — exatamente para que nenhuma função
interna possa mudar o contrato por acidente.
:::

## Faça o formato ser uma escolha

**O conserto imediato** tem uma palavra:

```php
$exemplares = array_values(array_filter($exemplares, $criterio));
```

`array_values` descarta as chaves e renumera a partir de zero. A regra
prática: **toda vez que o resultado de `array_filter` for virar JSON, ou
for tratado como lista, passe por `array_values`.**

**O conserto estrutural** é um teste que prende o contrato:

```php title="tests/AcervoTest.php" numbered
<?php

test('exemplares saem como lista, nunca como objeto', function () {
    $resposta = $this->getJson('/livros/3/exemplares');

    expect($resposta->json('exemplares'))->toBeList();
});
```

Esse teste falha no dia em que alguém acrescentar outro `array_filter` no
caminho — que é exatamente o que vai acontecer, porque o Dedé não foi
descuidado. Ele usou uma função normal do jeito documentado.

**E o conserto definitivo** é o do capítulo @cap:classes-e-objetos: quando
`Exemplar` for uma classe e a resposta for montada por um objeto que conhece
o formato, `array_filter` deixa de ter acesso ao contrato público.

:::note Na sua carreira
"A gente não mudou nada" é quase sempre falso e quase nunca mentira. A
pessoa mudou algo que, segundo o modelo mental dela, não podia causar aquilo.

A habilidade que se desenvolve com o tempo não é lembrar de todos os efeitos
colaterais — é **estreitar a busca rápido**. Neste caso: o app mudou? Não. A
API mudou? Sim, na sexta. O que mudou na sexta? Três linhas. O que essas três
linhas tocam? A forma da resposta.

Quatro perguntas, dois minutos. É isso que separa uma investigação de meia
hora de uma manhã inteira — e é treinável.
:::

## Array não é banco de dados

Existe um ponto em que o array para de ser a ferramenta certa, e ele chega
antes do que as pessoas esperam:

```php title="o_limite.php" numbered
<?php

$emprestimos = carregarTodosOsEmprestimos();

$doLeitor = array_filter(
    $emprestimos,
    fn(array $e): bool => $e['leitor_id'] === 47
);
```

Isso traz oito mil registros da memória — ou do banco — para descartar 7.993.
Funciona com trinta. Com oito mil, é o mesmo erro do capítulo
@cap:repeticoes, com outra roupa: **o filtro está na camada errada**.

| O array é bom para | O banco é melhor para |
|---|---|
| dezenas de itens já carregados | milhares de registros |
| transformar o que você já tem | escolher o que trazer |
| agrupar para exibir | somar, contar, ordenar em volume |

Tabela: A pergunta que decide: eu **já tenho** esses dados na mão por outro
motivo, ou estou carregando tudo só para filtrar?

## Cópia por valor

```php title="copia.php" numbered
<?php

$a = ['tombo' => 812];
$b = $a;

$b['tombo'] = 907;

echo $a['tombo'], "\n";
```

```text
812
```

Em PHP, atribuir um array **copia**. Isso é diferente de objeto, que é
atribuído por referência, e é diferente de Python e JavaScript, onde a lista
seria compartilhada.

A cópia é preguiçosa por dentro — o PHP só duplica de verdade quando um dos
dois muda —, então o custo é menor do que parece. Mas ele existe:

:::pitfall
Passar um array de cem mil itens para uma função que o modifica dispara uma
cópia inteira na memória. Em laço, isso multiplica. Quando o array é grande e
a função precisa mesmo alterá-lo, o `&$array` por referência resolve — e
traz de volta todos os problemas de ação à distância que o capítulo
@cap:funcoes descreveu. Quase sempre, a resposta melhor é devolver um array
novo e deixar o antigo ser descartado.
:::

## Quatro níveis de profundidade

```php
$dados['livro'][3]['exemplares'][0]['emprestimo']['leitor']['nome']
```

Essa linha existe no Sistema. Ela funciona. E ela tem quatro problemas que
nenhuma ferramenta consegue apontar: o editor não sugere nada, um erro de
digitação em qualquer nível dá aviso e `null`, não há como saber quais
chaves existem sem rodar, e a estrutura inteira é um contrato que não está
escrito em lugar nenhum.

:::key
Quando o array tem três ou mais níveis e o formato é **conhecido e fixo**,
ele está pedindo uma classe. O capítulo @cap:classes-e-objetos faz essa
troca, e o ganho não é estético: é o editor completando `->titulo`, o
PHPStan acusando `->titluo`, e a estrutura virando documentação executável.
:::

## Desempacotamento e spread

```php title="desempacotar.php" numbered
<?php

[$primeiro, $segundo] = [812, 907];

['tombo' => $t, 'status' => $s] = $exemplar;

foreach ($exemplares as ['tombo' => $tombo]) {
    echo $tombo, "\n";
}

$todos = [...$disponiveis, ...$reservados];
```

O desempacotamento por chave, na segunda linha, é o mais útil do conjunto:
ele extrai só o que interessa e documenta, na própria linha, o que a função
usa do array.

O `...` junta arrays e, desde o PHP 8.1, funciona também com chaves de
texto — com a regra de que o último repetido vence.

:::summary
- Array em PHP é um mapa ordenado; lista é uma convenção sobre as chaves.
- Vira array JSON só com chaves `0..n-1` sem buraco; o resto vira objeto.
- `array_filter` preserva chaves — use `array_values` antes de serializar.
- `array_column($lista, null, 'id')` indexa e mata busca linear.
- Filtrar em PHP o que o banco poderia filtrar é o erro da camada errada.
- Array é copiado por valor; objeto, não.
- Três níveis de profundidade é o sinal de que falta uma classe.
:::

:::checkpoint
Você escolhe a função de array certa em vez de escrever laço, sabe quando o
resultado precisa de `array_values`, e reconhece quando o array deixou de
ser a ferramenta adequada.
:::

:::exercise level=1
Dada a lista de exemplares, produza um array com os tombos dos que estão
disponíveis, garantindo que ele vire uma lista JSON.

:::answer
```php
<?php

$tombos = array_values(
    array_column(
        array_filter(
            $exemplares,
            fn(array $e): bool => $e['status'] === 'disponivel'
        ),
        'tombo'
    )
);
```
Três funções aninhadas já está no limite do legível. Em código de produção,
eu quebraria em duas variáveis com nome — concisão é uma qualidade, mas
clareza vem antes dela.
:::

:::exercise level=2
Monte um array que mapeie `livro_id` para a quantidade de exemplares
disponíveis daquele livro.

:::answer
```php
<?php

$contagem = [];

foreach ($exemplares as $exemplar) {
    if ($exemplar['status'] !== 'disponivel') {
        continue;
    }

    $id = $exemplar['livro_id'];
    $contagem[$id] = ($contagem[$id] ?? 0) + 1;
}
```
`($contagem[$id] ?? 0) + 1` é o idioma para "some ao que já existe,
começando do zero na primeira vez". Sem o `??`, a primeira ocorrência de
cada livro geraria um aviso de índice indefinido — e o resultado continuaria
certo, o que é a pior combinação possível.

Repare também que esse array **não** é uma lista: as chaves são ids de
livro. Se ele for para o JSON, vai virar objeto — e aqui isso está correto,
porque é um mapa mesmo.
:::

:::exercise level=1
Escreva uma função que garanta que um array vire lista JSON, e teste com um
array filtrado e com um mapa de contagens.

:::answer
```php
<?php

function comoLista(array $a): array
{
    return array_is_list($a) ? $a : array_values($a);
}

$filtrado = array_filter([1, 2, 3], fn($n) => $n !== 2);
var_dump(array_is_list($filtrado));
var_dump(array_is_list(comoLista($filtrado)));
```
```text
bool(false)
bool(true)
```
Cuidado com o segundo caso do enunciado: aplicar essa função a um **mapa de
contagens** destrói a informação, porque as chaves eram os dados. A função
resolve o caso da lista filtrada e é perigosa se aplicada sem pensar — o que
é um bom lembrete de que utilitário genérico também precisa de critério de
uso.
:::

:::exercise level=3
O endpoint abaixo devolve o acervo para o aplicativo. Ele passou por três
pessoas em dois anos. Aponte os problemas e descreva o que você mudaria —
inclusive o que mudaria **fora** desta função.

```php
function acervo() {
    $livros = carregarTodosOsLivros();
    $saida = [];
    foreach ($livros as $l) {
        if ($l['ativo']) {
            $l['exemplares'] = carregarExemplares($l['id']);
            $l['disponiveis'] = count(array_filter(
                $l['exemplares'],
                fn($e) => $e['status'] === 'disponivel'
            ));
            $saida[$l['id']] = $l;
        }
    }
    return json_encode($saida);
}
```

:::answer
**1. N+1.** `carregarExemplares` dentro do laço: uma consulta por livro,
quatro mil livros. É o capítulo @cap:repeticoes de novo.

**2. Filtro em PHP.** `if ($l['ativo'])` descarta registros que o banco
nunca deveria ter enviado.

**3. `$saida[$l['id']]` produz um objeto JSON**, não uma lista — e desta vez
de propósito, aparentemente. Mas o aplicativo, que espera lista em todo o
resto da API, recebe um formato diferente **só aqui**. Inconsistência de
contrato é pior que formato errado: ela obriga quem consome a tratar cada
endpoint como um caso especial.

**4. `$l` inteiro vai para a resposta.** Toda coluna nova na tabela `livro`
— inclusive `custo_de_aquisicao` ou `observacao_interna` — passa a aparecer
no aplicativo público, sem ninguém decidir isso. É o vazamento que o
capítulo @cap:api-resources existe para impedir.

**5. A função faz quatro coisas:** busca, filtra, calcula e serializa. Ela
devolve `string`, não dados — então quem quiser reusar a lógica para gerar
um CSV precisa decodificar o próprio JSON.

**O que eu mudaria fora da função** é a parte que a pergunta quer:

O cálculo de `disponiveis` não pertence a PHP. É um `COUNT` com `GROUP BY`
que o banco faz em milissegundos sobre quatro mil livros — capítulo
@cap:banco-de-dados-e-sql. A decisão de quais campos saem pertence a uma
camada de saída — capítulo @cap:api-resources. E a lista completa do acervo
não deveria existir como endpoint: quatro mil livros numa resposta é uma
decisão de paginação que ninguém tomou — capítulo
@cap:paginacao-filtros-e-buscas.

Essa é a leitura que vale treinar: metade dos problemas de uma função ruim
não se resolve **dentro** dela. Reescrever essa função inteira, mantendo o
endpoint como está, produz um código bonito que continua carregando o acervo
inteiro na memória a cada abertura do aplicativo.
:::

:::story A piada final
Quarta-feira, retrospectiva. Cléber pediu para alguém explicar o incidente
de segunda "em linguagem de negócio".

Dedé pensou um pouco.

— O aplicativo esperava uma fila e recebeu uma gaveta.

Cléber anotou. No relatório que foi para a diretoria, o incidente ficou
registrado como: *"divergência de expectativa estrutural entre camadas"*.

Na retrospectiva seguinte, o Dr. Aurélio citou a frase como exemplo de
comunicação clara.
:::
