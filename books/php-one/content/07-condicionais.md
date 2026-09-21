---
title: "Condicionais"
number: 7
slug: condicionais
part: p1
kicker: "Onze regras de empréstimo, quarenta segundos de fala, zero linhas escritas em trinta e um anos."
goal: >-
  Escrever decisões legíveis com `if`, `elseif` e `match`, transformar
  aninhamento em escada, e reconhecer o momento em que a escada está pedindo
  outra coisa.
---

:::story As onze condições
— Quando é que uma pessoa pode levar um livro? — perguntou Tainá, com o
caderno aberto.

Vera respondeu sem parar de etiquetar:

— Se ela for sócia. Se não tiver livro atrasado. Se não dever multa acima de
cinco reais. Se não estiver com três livros já. Se o exemplar não for da
referência. Se não for o último exemplar do título, aí só sai com
autorização. Se for menor de doze, o responsável assina. Se o livro chegou
essa semana, fica uma semana em exposição. Se for período de prova, o prazo
cai para sete dias. Se for da coleção do Seu Juvenal, não sai de jeito
nenhum, mas isso ninguém escreveu.

Pausa.

— E se for a Dona Marlene, sai. Porque ela sempre devolve.

Tainá contou os riscos no caderno. Eram onze.

— A senhora sabe tudo isso de cor?

— Faço isso há trinta e um anos.

— E onde está escrito?

Vera parou de etiquetar pela primeira vez.

— Em lugar nenhum.

Na reunião de terça, Márcia perguntou quantos dias custava a tela de
empréstimo. Tainá disse onze regras. Márcia ouviu "onze" e escreveu "2
dias" na planilha, porque a pergunta dela era sobre dias.
:::

## A regra que mora na cabeça de alguém

Isso não é particularidade de biblioteca. Em toda empresa existe pelo menos
uma regra que:

- é aplicada dezenas de vezes por dia;
- tem exceções que ninguém listou;
- mora na cabeça de uma ou duas pessoas;
- e some quando essas pessoas saem de férias.

O sistema costuma implementar a versão simplificada — a que alguém
conseguiu descrever numa reunião de uma hora — e o restante continua sendo
resolvido no balcão, por quem sabe.

:::note Na sua carreira
Extrair requisito de quem não sabe que tem requisito é uma habilidade
específica, e quase nunca é ensinada.

O que **não** funciona: "me manda a regra de empréstimo por escrito". A
pessoa vai escrever as três condições óbvias e esquecer as oito que aplica
no automático.

O que funciona:

1. **Peça para ela narrar um caso concreto**, do começo ao fim, com nome e
	 data. O concreto puxa os detalhes que a abstração esconde.
2. **Pergunte pelas exceções em vez das regras**: "já aconteceu de você
	 deixar levar mesmo com livro atrasado?". Aí vem a Dona Marlene.
3. **Leia a regra de volta, em voz alta**, e espere a correção. A pessoa vai
	 te corrigir num detalhe que não teria lembrado sozinha.
4. **Mostre o código rodando.** Nada extrai requisito como ver o sistema
	 recusar alguém que ela deixaria passar.

Os passos 3 e 4 valem mais que os dois primeiros, e são os que a maioria dos
times pula porque parecem retrabalho.
:::

## Toda decisão deixa dois caminhos

```php title="emprestimo.php" numbered
<?php

$disponivel = true;

if ($disponivel) {
    echo "Pode emprestar\n";
} else {
    echo "Exemplar indisponivel\n";
}
```

```text
Pode emprestar
```

Parênteses obrigatórios em volta da condição, chaves delimitando o bloco.
Quem vem do Python estranha as chaves; quem vem do Java se sente em casa.

Quando você omite o `else`, o caminho do "não" continua existindo — ele
apenas não faz nada. Ter consciência disso é o que separa o programa correto
do programa que só parece correto.

:::diagram type="flowchart" caption="Toda decisão tem dois caminhos, mesmo quando você escreve só um."
nodes:
  - { id: ini, type: start,    text: "Início" }
  - { id: d1,  type: decision, text: "disponível?" }
  - { id: sim, type: process,  text: "empresta" }
  - { id: nao, type: process,  text: "(nada)" }
  - { id: fim, type: start,    text: "Fim" }
edges:
  - { from: ini, to: d1 }
  - { from: d1,  to: sim, label: "sim" }
  - { from: d1,  to: nao, label: "não" }
  - { from: sim, to: fim }
  - { from: nao, to: fim }
:::

Um `if` sem `else` num cálculo de multa significa que a variável do
resultado fica com o valor que já tinha — e se ela não tinha nenhum, o
programa segue com uma variável indefinida e um aviso que ninguém leu.

### As chaves não são opcionais

O PHP permite omitir as chaves quando o bloco tem uma linha só. Permitir
isso já custou muito dinheiro ao mundo:

:::compare left="O que parece" right="O que o PHP lê" lang="php"
if ($ok)
    liberar();
    registrar();
---
if ($ok) {
    liberar();
}
registrar();
:::

`registrar()` roda sempre, porque a indentação não significa nada para o
interpretador. Ela só significa alguma coisa para você.

:::key
**Use chaves sempre**, inclusive em bloco de uma linha só. É a regra de
estilo mais fácil de justificar numa revisão de código, e qualquer
formatador automático vai colocá-las por você.
:::

Existe ainda uma sintaxe alternativa, com `:` e `endif`:

```php
<?php if ($disponivel): ?>
    <span>Disponível</span>
<?php else: ?>
    <span>Emprestado</span>
<?php endif; ?>
```

Ela existe para ser usada **dentro de HTML**, onde uma chave solta no meio
da marcação fica difícil de encontrar. Em código PHP puro, não use.

## A escada de `elseif`

```php title="situacao.php" numbered
<?php

$dias_de_atraso = 9;

if ($dias_de_atraso <= 0) {
    $situacao = 'em dia';
} elseif ($dias_de_atraso <= 7) {
    $situacao = 'atrasado';
} elseif ($dias_de_atraso <= 30) {
    $situacao = 'notificado';
} else {
    $situacao = 'suspenso';
}

echo $situacao, "\n";
```

```text
notificado
```

A ordem é o que faz a escada funcionar: o **primeiro** teste verdadeiro
vence, e os seguintes nem chegam a ser avaliados. Nove é menor que 30, mas
também é menor que... não, não é menor que 7. Ele caiu no terceiro degrau
porque os dois primeiros responderam não.

Inverta a ordem e veja o estrago:

```php title="situacao_invertida.php" numbered
<?php

$dias_de_atraso = 9;

if ($dias_de_atraso <= 30) {
    $situacao = 'notificado';
} elseif ($dias_de_atraso <= 7) {
    $situacao = 'atrasado';
} elseif ($dias_de_atraso <= 0) {
    $situacao = 'em dia';
} else {
    $situacao = 'suspenso';
}

echo $situacao, "\n";
```

```text
notificado
```

A saída é igual, por acaso. Mas troque `$dias_de_atraso` por `0` e a versão
invertida continua dizendo `notificado`, porque zero também é menor que 30 e
o primeiro degrau engole todos os outros. Os dois últimos `elseif` viraram
código inalcançável — código que existe, é lido em toda revisão e nunca
roda.

:::key
Escada de `elseif` vai do caso **mais restritivo** ao **mais geral**. Se
você conseguir trocar dois degraus de lugar sem mudar o resultado, ou eles
não se sobrepõem — e aí a ordem não importa mesmo — ou um deles nunca roda.
:::

Repare na grafia: `elseif`, junto. Existe também `else if`, separado, que
funciona em código PHP puro e **quebra** na sintaxe alternativa com `endif`.
Use sempre a forma junta.

## Aninhar custa caro

Aninhar `if` dentro de `if` é a forma mais natural de escrever a segunda
condição e a mais cara de manter a partir da terceira:

:::compare left="Aninhado" right="Em escada" lang="php"
if ($socio) {
    if ($atrasados === 0) {
        if ($multa <= 500) {
            $pode = true;
        }
    }
}
---
if (!$socio) {
    $pode = false;
} elseif ($atrasados > 0) {
    $pode = false;
} elseif ($multa > 500) {
    $pode = false;
} else {
    $pode = true;
}
:::

Os dois fazem a mesma coisa. A diferença é que o lado esquerdo cresce para a
direita a cada regra nova: com onze regras, a atribuição final fica a
quarenta e quatro espaços da margem, e quem lê precisa manter onze condições
na cabeça ao mesmo tempo para saber como chegou ali.

:::key
Indentação profunda não é problema estético. É um relatório de quantas
condições o leitor precisa segurar simultaneamente para entender a linha que
está lendo. Três níveis é o limite em que a maioria das pessoas ainda
acompanha.
:::

## A décima segunda regra

Dedé escreveu as onze regras da Vera como uma escada. Levou uma tarde e
ficou com oitenta e três linhas, das quais estas são as seis primeiras:

```php title="pode_emprestar.php" numbered
<?php

if (!$socio) {
    $pode = false;
} elseif ($atrasados > 0) {
    $pode = false;
} elseif ($multa_em_centavos > 500) {
    $pode = false;
} elseif ($emprestimos_abertos >= 3) {
    $pode = false;
} elseif ($eh_referencia) {
    $pode = false;
} else {
    $pode = true;
}
```

Funcionou. Passou uma semana em produção sem uma reclamação.

Na terça seguinte, a Vera avisou que em janeiro o limite sobe de três para
cinco livros, porque é período de férias escolares.

Dedé abriu o arquivo. A regra do limite estava no quarto degrau — o que ele
descobriu contando. Para acrescentar "exceto em janeiro", precisava decidir
se a exceção entrava dentro daquela condição ou virava um degrau novo, e
garantir que a ordem continuasse correta em relação aos outros dez.

Ele acrescentou um `&&` no quarto degrau:

```php
} elseif ($emprestimos_abertos >= 3 && !$ferias) {
```

Duas semanas depois, alguém notou que leitores suspensos estavam levando
cinco livros em janeiro.

O problema não foi a linha estar errada — ela estava certa para a pergunta
que fazia. O problema é que a escada não tem nomes. Onze condições anônimas,
distinguidas por posição, e um `&&` acrescentado no meio de uma delas é
invisível numa revisão: a linha continua com o mesmo formato e nenhuma outra
linha mudou.

:::art caption="A regra de negócio mais completa da empresa costuma morar na cabeça de uma pessoa só."
Charge editorial minimalista em fundo branco: uma bibliotecária mais velha
atrás de um balcão de madeira, etiquetando livros sem olhar, enquanto fala.
Saindo da fala dela, um fluxograma enorme se desenha no ar, com dezenas de
losangos de decisão e setas que se cruzam, ocupando metade do quadro. De pé
na frente do balcão, uma estagiária com um caderno pequeno demais,
escrevendo rápido. Poucos elementos, humor seco, estética de revista de
tecnologia.
:::

## Dar nome à decisão

A correção não é um `elseif` melhor. É separar a decisão do limite da
decisão de emprestar:

```php title="pode_emprestar.php (corrigido)" numbered
<?php

$mes = 1;
$suspenso = true;

if ($suspenso) {
    $limite = 0;
} elseif ($mes === 1) {
    $limite = 5;
} else {
    $limite = 3;
}

echo "Limite deste leitor: ", $limite, "\n";
```

```text
Limite deste leitor: 0
```

Agora existe uma variável chamada `$limite`, com uma escada própria de três
degraus que responde uma pergunta só. O degrau do empréstimo passa a ser
`$emprestimos_abertos >= $limite`, e a regra de janeiro tem um lugar óbvio
para morar.

O leitor suspenso, que na versão anterior estava escondido num `&&` no meio
de uma condição de limite, agora é o primeiro degrau e devolve zero.

## `match` não é `switch`

O PHP tem `switch` desde sempre, com dois defeitos clássicos: ele compara
com `==`, e ele **escorrega** — esquecer um `break` faz a execução continuar
no caso seguinte, sem aviso.

Desde o PHP 8 existe `match`, que resolve os dois:

```php title="match.php" numbered
<?php

$status = 'transito';

$rotulo = match ($status) {
    'disponivel' => 'Livre',
    'emprestado' => 'Com leitor',
    'reservado', 'transito' => 'Indisponivel',
    default => 'Desconhecido',
};

echo $rotulo, "\n";
```

```text
Indisponivel
```

Leia a estrutura: `match` recebe um valor, compara com cada opção à esquerda
da seta e **devolve** o que estiver à direita da primeira que bater. Duas
opções podem compartilhar o mesmo resultado, separadas por vírgula. O
`default` pega o que sobrou.

| | `switch` | `match` |
|---|---|---|
| Comparação | `==` | `===` |
| Escorrega sem `break` | sim | não |
| Devolve valor | não | sim |
| Caso não previsto | ignora em silêncio | erro na hora |

Tabela: Não há caso em que o `switch` seja melhor, exceto quando um braço
precisa executar várias instruções.

A última linha merece atenção. Um `match` sem `default` que receba um valor
não previsto não ignora: ele quebra, com uma mensagem clara.

```text
$ php -r '$x = "novo"; echo match($x) { "a" => 1, "b" => 2 };'
PHP Fatal error: Uncaught UnhandledMatchError:
Unhandled match case "novo"
```

Isso parece hostil e é a melhor parte. Quando alguém acrescentar um status
novo ao sistema e esquecer de tratar, você descobre imediatamente, e não
três semanas depois por causa de uma tela em branco.

O `match` também funciona sem receber valor nenhum, comparando com `true`.
Aí ele vira uma escada que devolve valor:

```php title="match_condicional.php" numbered
<?php

$suspenso = false;
$mes = 1;

$limite = match (true) {
    $suspenso => 0,
    $mes === 1 => 5,
    default => 3,
};

echo "Limite: ", $limite, "\n";
```

```text
Limite: 5
```

São as mesmas três regras de antes, em cinco linhas em vez de sete, e com
uma diferença que importa mais do que o tamanho: `$limite` é atribuída **uma
vez só**, num lugar só. Na versão com `if`, ela era atribuída em três
lugares, e acrescentar um quarto degrau significava lembrar de atribuir de
novo.

## O que conta como verdadeiro

Vale repetir a lista, porque é dentro de um `if` que ela cobra:

| Falso | Verdadeiro |
|---|---|
| `false`, `null` | `true` |
| `0`, `0.0` | qualquer outro número |
| `""` e `"0"` | qualquer outro texto, inclusive `"0.0"` |
| `[]` | lista com qualquer item |

Tabela: `"0.0"` é verdadeiro e `"0"` é falso. É o item mais arbitrário da
lista, e a razão de o capítulo @cap:conversao-automatica insistir em
comparar explicitamente.

:::summary
- Chaves sempre; a sintaxe com `endif` é só para dentro de HTML.
- Todo `if` sem `else` deixa um caminho implícito — saiba qual é.
- A escada de `elseif` vai do caso mais restritivo ao mais geral; fora dessa
	ordem, degraus viram código inalcançável.
- Aninhamento profundo é um relatório de quantas condições o leitor precisa
	segurar ao mesmo tempo.
- Escada anônima esconde mudança: separe a decisão e dê nome a ela.
- `match` compara com `===`, não escorrega, devolve valor e quebra no caso
	não previsto.
- `match (true)` é uma escada que atribui a variável num lugar só.
:::

:::milestone
O programa agora decide. As onze regras da Vera ainda estão numa escada, mas
pela primeira vez em trinta e um anos elas existem em algum lugar além da
cabeça dela.
:::

:::exercise level=1
Escreva uma condição que imprima `"Devolver hoje"`, `"Em dia"` ou
`"Atrasado"` conforme os dias restantes para a devolução. Faça de duas
formas, com `if` e com `match (true)`.

:::answer
```php
<?php

$dias_restantes = 0;

if ($dias_restantes < 0) {
    $situacao = 'Atrasado';
} elseif ($dias_restantes === 0) {
    $situacao = 'Devolver hoje';
} else {
    $situacao = 'Em dia';
}

$situacao = match (true) {
    $dias_restantes < 0 => 'Atrasado',
    $dias_restantes === 0 => 'Devolver hoje',
    default => 'Em dia',
};

echo $situacao, "\n";
```

A ordem é o que faz as duas funcionarem: `< 0` precisa vir antes de
`=== 0`, porque um número negativo não é igual a zero e cairia no
`default` — anunciando "Em dia" para quem está atrasado.
:::

:::exercise level=2
Reescreva o trecho aninhado abaixo como escada, mantendo as mensagens.
Depois diga qual das duas versões você preferiria receber para acrescentar
uma quarta regra.

```php
if ($exemplar_existe) {
    if ($status === 'disponivel') {
        if ($emprestimos_abertos < 3) {
            $resposta = "Emprestado";
        } else {
            $resposta = "Limite atingido";
        }
    } else {
        $resposta = "Indisponivel";
    }
} else {
    $resposta = "Exemplar nao encontrado";
}
```

:::answer
```php
if (!$exemplar_existe) {
    $resposta = "Exemplar nao encontrado";
} elseif ($status !== 'disponivel') {
    $resposta = "Indisponivel";
} elseif ($emprestimos_abertos >= 3) {
    $resposta = "Limite atingido";
} else {
    $resposta = "Emprestado";
}
```

Repare que cada condição foi **invertida**: `if ($existe)` com o erro no
`else` virou `if (!$existe)` com o erro dentro. É o que permite achatar o
aninhamento.

A escada é a versão que eu preferiria receber, por um motivo mecânico: para
acrescentar a quarta regra, basta um degrau novo no lugar certo. Na versão
aninhada, é preciso abrir mais um nível de chaves no meio, reindentar tudo
que está dentro, e a alteração aparece na revisão como doze linhas
modificadas em vez de quatro.

E repare também no que as duas versões têm em comum, que é o defeito que
sobra: `$resposta` é um texto, então quem for usar esse resultado vai ter
que comparar frases para saber o que aconteceu.
:::

:::exercise level=3
A Vera avisou que, em janeiro, o limite sobe de três para cinco livros — mas
não vale para leitor suspenso. Em julho vale a mesma coisa. Implemente o
cálculo do limite de duas formas: com `&&` dentro da escada do empréstimo, e
com uma variável `$limite` própria. Depois diga qual você deixaria no
projeto e o que a escolha custa.

:::answer
**Forma 1 — dentro da escada do empréstimo:**

```php
} elseif ($emprestimos_abertos >= (
    ($mes === 1 || $mes === 7) && !$suspenso ? 5 : 3
)) {
    $pode = false;
```

Funciona e cabe numa linha. Tem três problemas.

A regra de férias ficou escondida dentro de uma condição cujo assunto é
outro. Um ternário apareceu dentro de uma comparação dentro de um `elseif`,
o que dá três níveis de raciocínio numa linha. E as duas condições que foram
juntadas com `&&` não têm relação nenhuma uma com a outra: uma é sobre o
calendário, a outra é sobre o leitor.

**Forma 2 — com nome:**

```php
<?php

$mes = 7;
$suspenso = false;

$ferias = ($mes === 1 || $mes === 7);

$limite = match (true) {
    $suspenso => 0,
    $ferias => 5,
    default => 3,
};

echo "Limite: ", $limite, "\n";
```

```text
Limite: 5
```

Eu deixaria a segunda, por dois motivos concretos.

**A regra ganhou nome.** Quando a Vera disser em outubro que a semana da
criança também conta, a pessoa que for mexer procura por `$ferias`,
encontra uma linha, e altera uma linha.

**O leitor suspenso ficou explícito**, no primeiro degrau, devolvendo zero.
Na forma 1 ele estava dentro de um ternário dentro de uma comparação — que é
exatamente onde o defeito real da história deste capítulo se escondeu.

**O que isso custa:** duas variáveis a mais e uma indireção a mais para quem
lê o fluxo principal. Em um programa de trinta linhas, esse custo é real e
pode não compensar. A pergunta honesta não é qual versão é mais elegante,
é: **quantas vezes essa regra vai mudar?** Esta já mudou duas vezes em duas
semanas.
:::

:::story Põe uma exceção aí
Na quinta, Tainá mostrou para a Vera a tela nova recusando um empréstimo,
com a mensagem *"Leitor com pendência: 1 livro atrasado"*.

Vera leu, concordou com a cabeça e olhou para a fila.

— A Dona Marlene tá com um atrasado.

— Então o sistema vai recusar.

Vera olhou para a tela. Olhou para a Dona Marlene. Olhou para a tela de
novo.

— Põe uma exceção aí.

Tainá anotou no caderno, na seção "para perguntar depois", logo abaixo de
*"e se o livro tiver dois autores?"*:

> *"regra nº 12: a Dona Marlene"*
:::
