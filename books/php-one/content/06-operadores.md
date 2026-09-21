---
title: "Operadores"
number: 4
slug: operadores
part: p1
kicker: "Seu Juvenal digitou a senha errada e entrou como bibliotecária-chefe. O culpado tem dois caracteres."
goal: >-
  Comparar com segurança, tratar ausência sem escada de `if`, concatenar sem
  surpresa, e entender por que um sinal de igual a menos já abriu a porta de
  muito sistema.
---

:::story Entrei sem querer
Sexta, 10h20. Seu Juvenal ligou com aquele tom de quem descobriu uma coisa
boa.

— Ó, eu consegui entrar no sistema!

— Ótimo. A senha nova funcionou?

— Não, eu errei a senha. Mas entrei do mesmo jeito. E entrei como a Vera.

Dedé pediu para ele repetir devagar.

Seu Juvenal tinha tentado o usuário da Vera com uma senha qualquer — segundo
ele, "alguma coisa com 240". O Sistema aceitou e abriu o painel da
bibliotecária-chefe, com permissão para apagar acervo.

Ele achou que era um recurso.
:::

O Sistema não tinha sido invadido. Ele estava fazendo exatamente o que o
código mandava — e o código mandava com dois caracteres a menos do que
devia.

## Quando a linguagem completa a frase

```text
$ php -r 'var_dump(1 == "1");'
bool(true)
$ php -r 'var_dump(1 === "1");'
bool(false)
```

`==` compara **depois de converter**. `===` compara valor **e tipo**, sem
converter nada.

A comparação frouxa existe desde sempre por um motivo histórico honesto:
tudo que vem de formulário HTML é texto, e exigir conversão manual em cada
`if` seria insuportável em 1998. O preço foi uma coleção de comportamentos
surpreendentes que a linguagem passou vinte e cinco anos podando.

:::trivia
No PHP 7, `0 == "abc"` era **verdadeiro**: a string virava `0`. Qualquer
comparação frouxa entre zero e texto passava. O PHP 8 inverteu a regra —
agora o número é que vira string quando a string não é numérica — e
`0 == "abc"` virou `false`.

Foi uma das poucas quebras de compatibilidade da história do PHP que
praticamente ninguém reclamou. A proposta se chamava *Saner string to number
comparisons*, e o nome já dizia o que a comunidade achava do comportamento
anterior.
:::

## A comparação que você realmente quis fazer

| Comparação | `==` | `===` |
|---|---|---|
| `1` e `"1"` | `true` | `false` |
| `0` e `""` | `false` (desde o PHP 8) | `false` |
| `"abc"` e `0` | `false` (desde o PHP 8) | `false` |
| `null` e `false` | `true` | `false` |
| `"1e3"` e `"1000"` | `true` | `false` |
| `[1, 2]` e `[1, 2]` | `true` | `true` |

Tabela: A quarta linha causa defeito silencioso — `null == false` faz "não
informado" passar por "negado". A quinta causou o incidente da Casa Amarela.

A recomendação geral é simples: **use `===` por padrão.** Escreva `==` só
quando a conversão for exatamente o que você quer, e deixe um comentário
dizendo por quê.

## Ferramentas para a regra de empréstimo

```php title="operadores.php" numbered
<?php

$dias = 9;
$limite = 14;

var_dump($dias <=> $limite);

$assunto = $dados['assunto'] ?? 'Geral';
$dados['status'] ??= 'disponivel';

$cidade = $leitor?->endereco?->cidade;

$linha = $titulo . ' (' . $ano . ')';
```

**`<=>`, o operador nave espacial**, devolve `-1`, `0` ou `1` conforme o
lado esquerdo seja menor, igual ou maior. Parece inútil até você precisar
ordenar por dois critérios:

```php title="ordenar.php" numbered
<?php

usort($emprestimos, fn(array $a, array $b): int =>
    [$a['devolver_ate'], $a['leitor']]
    <=>
    [$b['devolver_ate'], $b['leitor']]
);
```

O `<=>` compara **arrays inteiros**, posição por posição, parando na
primeira diferença. Ordenação por vários critérios de graça, numa linha —
escrever isso com `if` aninhado leva seis linhas e erra o desempate com
facilidade.

**`??` devolve o lado esquerdo se ele existe e não é nulo**; senão, o
direito. A diferença para `?:` importa e é a mesma armadilha do capítulo
@cap:variaveis-e-tipos:

:::compare left="`?:` usa truthiness" right="`??` usa existência" lang="php"
$m = $multa ?: 500;
// multa = 0 vira 500
---
$m = $multa ?? 500;
// multa = 0 continua 0
:::

**`?->` chama o método apenas se o objeto não for nulo** — a expressão
inteira vira `null` em vez de erro fatal.

:::pitfall
`?->` é conveniente e esconde uma pergunta. Se `$leitor` pode ser nulo, **por
quê**? Às vezes a resposta é legítima — o empréstimo de 2011 não tem leitor
cadastrado. Às vezes é sintoma de que falta uma guarda mais acima. Uma
cadeia de três `?->` quase sempre é o segundo caso.
:::

**Concatenação é `.`, nunca `+`.** Em PHP, `+` é sempre aritmético: `"a" +
"b"` é erro fatal desde o PHP 8. Isso incomoda quem vem de JavaScript e é,
na prática, uma vantagem — `"10" + 5` nunca vai devolver `"105"` por
acidente.

## Dois caracteres na porta

Dedé abriu o `login.php` do Sistema.

```php title="login.php (o Sistema, 2009)" numbered
<?php

$senha_enviada = md5($_POST['senha']);

if ($senha_enviada == $usuario['senha']) {
    $_SESSION['usuario'] = $usuario;
    header('Location: painel.php');
}
```

Um `==` onde deveria haver outra coisa inteiramente. E o efeito depende de
um detalhe do MD5:

```text
$ php -r 'echo md5("240610708"), "\n";'
0e462097431906509019562988736854
$ php -r 'echo md5("QNKCDZO"), "\n";'
0e830400451993494058024219903391
```

Dois hashes diferentes. E:

```text
$ php -r 'var_dump(md5("240610708") == md5("QNKCDZO"));'
bool(true)
```

As duas strings parecem notação científica: zero elevado a alguma coisa.
Zero elevado a qualquer coisa é zero. O PHP converte as duas para `0.0` e
compara os números.

O hash da senha da Vera, gravado em 2009, começava com `0e` e tinha só
dígitos depois. Qualquer senha cujo MD5 tivesse o mesmo formato entrava na
conta dela — e existem milhares de strings assim, catalogadas em listas
públicas há mais de uma década.

Seu Juvenal acertou uma por acaso.

:::story Quatro minutos
Dedé escreveu um script de vinte linhas que testava uma lista pública de
strings com hash no formato `0e`.

Em quatro minutos, tinha encontrado duas contas de atendente com hash
vulnerável.

A da Vera era uma delas.

— Desde quando? — perguntou ela.

— Desde 2009.

Vera ficou quieta por um tempo. Depois:

— E quantas pessoas sabiam disso?

— Ninguém sabia. Foi o Seu Juvenal, errando a senha.
:::

## O defeito tinha três camadas

Três erros empilhados, e vale separar porque o conserto de cada um é
diferente.

**Erro 1 — `==` entre segredos.** A comparação frouxa transformou duas
strings distintas em iguais. Um `===` teria evitado este incidente
específico.

**Erro 2 — MD5 para senha.** Mesmo com `===`, o MD5 é rápido demais: uma
placa de vídeo comum calcula bilhões por segundo, o que torna a quebra por
força bruta viável. Senhas precisam de um algoritmo lento, como o usado por
`password_hash()`.

**Erro 3 — comparação em tempo variável.** Mesmo com `===`, a comparação de
strings do PHP para no primeiro caractere diferente. Um valor que acerta os
cinco primeiros caracteres demora mensuravelmente mais que um que erra o
primeiro — e, com requisições suficientes, dá para descobrir um segredo
caractere a caractere sem nunca acertá-lo inteiro.

:::key
Em comparação de segredo — senha, token, assinatura — não use `==` nem
`===`. Use `hash_equals()`, que percorre o comprimento inteiro sempre,
independentemente de onde está a diferença:

```php
if (hash_equals($esperado, $enviado)) {
```

A ordem dos argumentos importa: o valor **conhecido** vem primeiro. E, para
senha especificamente, nem isso — a resposta é `password_verify()`, do
capítulo @cap:autenticacao, que já faz a comparação em tempo constante e
ainda trata do algoritmo.
:::

## Uma entrada que merece desconfiança

```php title="login.php (a versão que sobrevive)" numbered
<?php

$usuario = buscarUsuarioPorEmail($_POST['email'] ?? '');

if ($usuario === null) {
    password_hash('dummy', PASSWORD_DEFAULT);
    recusar();
}

if (!password_verify($_POST['senha'] ?? '', $usuario->senhaHash)) {
    recusar();
}

entrar($usuario);
```

Quatro decisões nesse trecho, e três delas não são sobre operadores:

O `?? ''` garante que a ausência do campo não vire aviso de índice
indefinido — a aplicação direta do operador que acabamos de ver.

`password_verify` resolve os três erros de uma vez: algoritmo adequado,
comparação em tempo constante, e nenhuma decisão sua sobre hash.

O `password_hash('dummy', ...)` no caminho do usuário inexistente parece
desperdício e é proposital: sem ele, a resposta para um e-mail que não existe
volta em microssegundos e a de uma senha errada volta em centenas de
milissegundos. A diferença de tempo entrega quem tem conta no sistema.

E `recusar()` devolve **a mesma mensagem** nos dois casos. Dizer "usuário
não encontrado" entrega a lista de quem é cliente.

:::note Na sua carreira
Encontrar uma falha de segurança num sistema que não é seu é uma situação
socialmente desconfortável, e a forma de comunicar muda o resultado.

O que funciona: escrever por escrito, para a pessoa responsável, com **o
impacto em linguagem de negócio** primeiro e o detalhe técnico depois. "É
possível entrar na conta da bibliotecária-chefe sem saber a senha, e apagar
o acervo" comunica melhor que "há uma comparação frouxa de hash MD5".

O que não funciona: demonstrar publicamente. Entrar na conta de alguém para
provar o ponto, mesmo com boa intenção, transfere o problema para você — e a
conversa deixa de ser sobre a falha e passa a ser sobre o seu acesso.

E há uma regra prática que vale para a vida inteira: **registre a data**. Se
o conserto demorar seis meses e algo acontecer, a diferença entre "eu avisei"
e "eu avisei em 14 de março, neste e-mail" é enorme.
:::

## Precedência

A ordem completa tem vinte níveis e não vale decorar. Vale conhecer os
quatro pontos em que as pessoas erram:

| Expressão | Lida como | Surpresa |
|---|---|---|
| `!$a === $b` | `(!$a) === $b` | `!` vem antes de `===` |
| `$a . $b + $c` | erro no PHP 8 | antes era `($a.$b)+$c` |
| `$a ?? $b ? $c : $d` | erro de sintaxe | `??` e `?:` não se misturam |
| `$a = $b or $c` | `($a = $b) or $c` | `or` é mais fraco que `=` |

Tabela: A última linha é a razão de `and` e `or` em palavras existirem além
de `&&` e `||` — e a razão de não usá-los.

:::key
Parêntese não tem custo em execução e não tem custo de leitura. Se duas
pessoas na revisão precisarem discutir a ordem de avaliação, o parêntese já
deveria estar lá.
:::

`&&` e `||` também curto-circuitam — o lado direito só é avaliado se
necessário —, e isso vira proteção:

```php
if ($emprestimo !== null && $emprestimo->estaAtrasado()) {
```

Se `$emprestimo` for nulo, o método nunca é chamado. A ordem dos dois lados
é o que separa o código que roda do que quebra.

:::summary
- `==` converte antes de comparar; `===` compara valor e tipo. Use `===`.
- Comparação de segredo usa `hash_equals`; senha usa `password_verify`.
- Resposta de login não distingue e-mail inexistente de senha errada — nem
  na mensagem, nem no tempo.
- `<=>` ordena, inclusive arrays inteiros, com vários critérios de graça.
- `??` olha existência; `?:` olha truthiness — e zero separa os dois.
- `+` é sempre aritmético; concatenação é `.`.
- `&&` e `||` curto-circuitam, e a ordem dos lados é proteção.
:::

:::exercise level=1
Escreva uma expressão que pegue o assunto de um livro vindo de um array,
usando `"Geral"` quando o campo não existir — sem substituir um assunto
vazio informado de propósito.

:::answer
```php
$assunto = $dados['assunto'] ?? 'Geral';
```
`??` olha existência, então `''` informado permanece `''`. Com `?:`, a
string vazia viraria `"Geral"` — que é outro comportamento, e às vezes é o
desejado. A escolha entre os dois é uma decisão, não um detalhe.
:::

:::exercise level=2
Ordene uma lista de empréstimos por data de devolução crescente e, em caso
de empate, por nome do leitor. Depois inverta só a data, mantendo o nome
crescente.

:::answer
```php
usort($e, fn($a, $b) =>
    [$a['devolver_ate'], $a['leitor']]
    <=> [$b['devolver_ate'], $b['leitor']]
);

usort($e, fn($a, $b) =>
    [$b['devolver_ate'], $a['leitor']]
    <=> [$a['devolver_ate'], $b['leitor']]
);
```
Na segunda, repare que só a posição de `devolver_ate` foi trocada entre os
lados: inverter um critério é trocar `$a` por `$b` naquela posição, e não
negar o resultado inteiro — negar inverteria também o desempate.
:::

:::exercise level=3
O trecho abaixo valida um token de recuperação de senha, enviado por
e-mail. Ele tem três falhas de naturezas diferentes. Aponte as três e
reescreva.

```php
if ($_GET['token'] == $usuario['token_recuperacao']) {
    redefinirSenha($usuario, $_POST['nova_senha']);
}
```

:::answer
**Falha 1 — comparação frouxa.** É o incidente deste capítulo. Se o token
guardado tiver formato numérico ou `0e`, tokens diferentes comparam iguais.
E se `token_recuperacao` for `null` — porque nenhuma recuperação foi pedida
—, um token ausente convertido pode passar.

**Falha 2 — ataque de tempo.** Mesmo com `===`, a comparação para no
primeiro caractere diferente, e o tempo de resposta entrega o token
caractere a caractere.

**Falha 3 — o token não expira e não é consumido.** O código não verifica
data de validade nem invalida o token depois do uso. Um token que vazou num
e-mail encaminhado em 2023 continua funcionando hoje, quantas vezes quiser.

```php
$token = $_GET['token'] ?? '';
$guardado = $usuario->tokenRecuperacao;

if ($guardado === null || $usuario->tokenExpiraEm < time()) {
    recusar();
}

if ($token === '' || !hash_equals($guardado, $token)) {
    recusar();
}

redefinirSenha($usuario, $_POST['nova_senha'] ?? '');
$usuario->limparTokenRecuperacao();
```

E há uma quarta coisa, que não é falha de operador e é a mais grave de
todas: **o token viaja em `$_GET`**. Query string aparece no log do
servidor, no histórico do navegador, e no cabeçalho `Referer` enviado para
qualquer recurso de terceiro carregado naquela página — um script de
analytics, uma fonte, um pixel. O token de recuperação da senha de alguém
sai da sua aplicação para um servidor que você não controla.

A forma correta é `POST` com o token no corpo, e é assim que o capítulo
@cap:autenticacao vai construí-lo.
:::

:::story A piada final
Na segunda, Seu Juvenal voltou ao assunto na reunião da associação.

— Uma coisa boa: eu descobri que o sistema tem uma falha grave.

A Vera, sem levantar os olhos:

— O senhor descobriu errando a senha.

— Descobrir é descobrir.

Ele não estava totalmente errado, e essa é a parte incômoda. Quinze anos de
produção, nenhum teste, nenhuma auditoria — e a vulnerabilidade foi
encontrada por um senhor de setenta e dois anos digitando errado.
:::
