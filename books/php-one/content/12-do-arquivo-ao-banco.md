---
title: "Do arquivo ao banco"
number: 12
slug: do-arquivo-ao-banco
part: p2
kicker: "Duas atendentes, um arquivo, um empréstimo. Deveriam ser dois."
goal: >-
  Salvar dados que sobrevivem ao fim do programa, reproduzir na sua máquina
  o defeito que um arquivo não consegue evitar, entender o que um banco de
  dados faz de diferente, e instalar um.
---

Tudo que o programa guardou até aqui — o acervo, os empréstimos, as multas —
some quando o programa termina. Cada execução começa do zero, e o único
lugar onde o acervo da Casa Amarela existe de verdade é dentro do Sistema de
2009 e na gaveta da Vera.

Este é o capítulo em que os dados passam a morar em algum lugar.

## O acervo que some

```php title="volatil.php" numbered
<?php

$acervo = [
    ['tombo' => 812, 'titulo' => 'O Cortiço'],
    ['tombo' => 907, 'titulo' => 'Vidas Secas'],
];

echo count($acervo), " exemplares\n";
```

```text
$ php volatil.php
2 exemplares
$ php volatil.php
2 exemplares
```

Sempre dois. Se o programa cadastrar um terceiro, ele existe durante a
execução e desaparece no ponto e vírgula final. A memória do processo é
devolvida ao sistema operacional, e com ela vai tudo.

:::term Persistência
A propriedade de um dado continuar existindo depois que o programa que o
criou terminou. Um dado em memória é volátil; um dado gravado em disco é
persistente. Tudo que este capítulo faz é atravessar essa fronteira.
:::

## Gravar num arquivo

O PHP lê e escreve arquivo com duas funções de nome descritivo:

```php title="salvar.php" numbered
<?php

$acervo = [
    ['tombo' => 812, 'titulo' => 'O Cortiço'],
    ['tombo' => 907, 'titulo' => 'Vidas Secas'],
];

$json = json_encode(
    $acervo,
    JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE
);

file_put_contents('acervo.json', $json);

echo "gravado\n";
```

```text
$ php salvar.php
gravado
$ cat acervo.json
[
    {
        "tombo": 812,
        "titulo": "O Cortiço"
    },
    {
        "tombo": 907,
        "titulo": "Vidas Secas"
    }
]
```

`json_encode` transforma o array em texto no formato JSON, que o capítulo
@cap:arrays apresentou. `file_put_contents` escreve esse texto num arquivo,
criando-o se não existir e **substituindo o conteúdo** se existir.

As duas constantes depois da vírgula mudam o formato da saída.
`JSON_PRETTY_PRINT` quebra linhas e indenta, o que torna o arquivo legível
por gente. `JSON_UNESCAPED_UNICODE` mantém os acentos como acentos — sem
ela, `O Cortiço` viraria `O Cortiço`, que é válido e ilegível. O `|`
entre as duas combina as opções.

Ler de volta é o caminho inverso:

```php title="carregar.php" numbered
<?php

$json = file_get_contents('acervo.json');
$acervo = json_decode($json, true);

echo count($acervo), " exemplares\n";
echo $acervo[0]['titulo'], "\n";
```

```text
$ php carregar.php
2 exemplares
O Cortiço
```

O `true` no segundo argumento do `json_decode` é importante e fácil de
esquecer: sem ele, o JSON vira objeto em vez de array, e todos os
`$acervo[0]['titulo']` do seu programa param de funcionar.

:::pitfall
`file_get_contents` devolve `false` quando o arquivo não existe, e ainda
emite um aviso. Como `false` é falso e um array vazio também é, o código que
faz `if (!$dados)` trata "arquivo não existe" e "acervo vazio" como a mesma
coisa — o defeito do relatório da Vera outra vez.

A forma honesta confere antes:

```php
if (!file_exists('acervo.json')) {
    $acervo = [];
} else {
    $acervo = json_decode(file_get_contents('acervo.json'), true);
}
```
:::

Agora o acervo sobrevive. Cadastre um exemplar, rode de novo, ele está lá.
Para um programa usado por uma pessoa de cada vez, isso resolve.

A Casa Amarela tem dois computadores.

## 10h12

:::story O exemplar que saiu uma vez
A Casa Amarela atende em dois lugares ao mesmo tempo. Tem o balcão da
entrada, onde fica a Vera, e tem o computador da sala dos fundos, onde a
Neide faz o cadastro de leitor novo e, quando a fila aperta, também
empresta.

Numa terça de manhã, às 10h12, as duas emprestaram.

Vera emprestou o exemplar 812 para a Dona Marlene. Neide emprestou o 344
para um rapaz que estava com pressa.

Às 10h30 o arquivo tinha um empréstimo.

— Sumiu o da Marlene — disse Vera.

— Ou sumiu o meu — disse Neide.

Sumiu o da Marlene. Dava para saber porque o do rapaz estava lá, e não
porque alguém tivesse registro de nada.

A Vera resolveu na hora, do jeito que resolve desde 1995: pegou uma ficha de
papel, escreveu 812, escreveu Marlene, escreveu a data, e colocou na gaveta.

— Enquanto o computador não decide, a gaveta decide.
:::

Esse defeito não é de programação descuidada. Ele é uma consequência direta
de como se escreve num arquivo, e dá para reproduzir na sua máquina em dois
minutos.

```php title="emprestar.php" numbered
<?php

$arquivo = 'emprestimos.json';

$emprestimos = file_exists($arquivo)
    ? json_decode(file_get_contents($arquivo), true)
    : [];

echo "li o arquivo: ", count($emprestimos), " emprestimos\n";

sleep(5);

$emprestimos[] = [
    'exemplar' => (int) $argv[1],
    'leitor' => $argv[2],
];

file_put_contents($arquivo, json_encode($emprestimos));

echo "gravei: ", count($emprestimos), " emprestimos\n";
```

Duas coisas novas. `$argv` é um array com o que veio na linha de comando:
`$argv[0]` é o nome do arquivo, `$argv[1]` é o primeiro argumento. E
`sleep(5)` faz o programa esperar cinco segundos — aqui ele só serve para
deixar visível uma janela de tempo que, na vida real, dura milissegundos.

Abra **dois terminais** e rode um em cada, com menos de cinco segundos de
diferença:

```text
Terminal 1                          Terminal 2
$ php emprestar.php 812 Marlene
li o arquivo: 0 emprestimos
                                    $ php emprestar.php 344 Rapaz
                                    li o arquivo: 0 emprestimos
gravei: 1 emprestimos
                                    gravei: 1 emprestimos
```

Os dois gravaram. Os dois disseram que deu certo. E o arquivo:

```text
$ cat emprestimos.json
[{"exemplar":344,"leitor":"Rapaz"}]
```

Um empréstimo.

## Por que some

Cada execução fez três coisas, nessa ordem: **leu** o arquivo inteiro,
**alterou** o array em memória, **gravou** o arquivo inteiro por cima.

O problema está no intervalo entre a leitura e a gravação. Nesse intervalo,
o segundo programa leu o mesmo conteúdo antigo. Quando ele gravou, escreveu
por cima do que o primeiro tinha acabado de salvar — sem saber que havia
algo por cima para escrever.

:::term Corrida
Quando o resultado de uma operação depende de qual de dois processos chega
primeiro, e nada garante a ordem. O nome vem daí: dois participantes, uma
linha de chegada, e um resultado diferente a cada execução. É a categoria de
defeito mais difícil de reproduzir, porque ela some quando você para para
observar.
:::

Nenhum dos dois programas está errado. Os dois fazem exatamente o que
qualquer pessoa escreveria. O que falta não está no código: falta alguém
**coordenar** os dois.

:::pitfall
Existe uma saída parcial no próprio PHP: `flock()`, que pede ao sistema
operacional para travar o arquivo enquanto um processo mexe nele. Ela
funciona, e resolve este caso específico.

O que ela não resolve: enquanto um processo segura a trava, todos os outros
esperam — o arquivo inteiro, não a linha que interessa. Com dois
atendentes, é imperceptível. Com vinte, a biblioteca para. E se o arquivo
estiver numa pasta de rede, a trava pode simplesmente não funcionar, em
silêncio.

Vale conhecer `flock` para consertar um script pequeno hoje. Não vale
construir um sistema em cima dela.
:::

## O que um banco faz de diferente

A corrida é o primeiro item de uma lista, e é a lista inteira que justifica
trocar de ferramenta.

| Pergunta | Arquivo | Banco de dados |
|---|---|---|
| Dois gravando ao mesmo tempo | um sobrescreve o outro | os dois gravam, em ordem |
| "Quero só os 20 atrasados" | carrega os 8.412 e filtra | traz 20 |
| "Esse tombo já existe?" | percorre tudo, toda vez | responde por índice |
| "Esse leitor pode ser apagado?" | ninguém confere | o banco recusa |
| "Grave as duas coisas ou nenhuma" | não existe | transação |
| Acesso de outra máquina | pasta compartilhada e fé | é para isso que ele serve |

Tabela: Cada linha é um problema que alguém já teve. O banco não é mais
sofisticado por esporte — ele é a soma de quarenta anos de gente resolvendo
essas seis linhas.

:::term SGBD
*Sistema Gerenciador de Banco de Dados*: um programa que fica rodando o
tempo todo, guarda os dados em disco e atende pedidos de outros programas.
Ele é quem coordena quem escreve, quem lê e em que ordem — o coordenador que
faltava aos dois terminais da seção anterior.

MySQL, PostgreSQL, SQLite e SQL Server são SGBDs. Este livro usa o MySQL,
porque é o que a Casa Amarela já tem rodando desde 2009.
:::

O ponto importante é que o banco é **outro programa**. Ele não é uma
biblioteca que o seu PHP carrega: é um processo separado, que pode estar em
outra máquina, e com o qual o seu programa conversa. É por isso que ele
consegue coordenar dois PHPs — ele está fora dos dois.

## Instalar e entrar

| Sistema | Como instalar |
|---|---|
| Ubuntu / Debian | `sudo apt install mysql-server` |
| macOS | `brew install mysql` e `brew services start mysql` |
| Windows | instalador oficial em `dev.mysql.com/downloads`, ou WSL2 |
| Qualquer um, com Docker | `docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=senha mysql:8` |

Tabela: A linha do Docker sobe um MySQL isolado que some quando você mandar,
sem instalar nada na máquina. Se você já usa Docker, é o caminho mais
limpo.

Depois de instalado, existe um programa cliente que conversa com ele pelo
terminal:

```text
$ mysql -u root -p
Enter password:
Welcome to the MySQL monitor.  Commands end with ; or \g.

mysql>
```

O `-u root` diz com qual usuário entrar; o `-p` pede a senha. O `mysql>` no
fim é o **prompt do banco**: daqui para frente, o que você digitar não é
comando de terminal, é comando de banco de dados.

:::warning
Em instalação nova, o usuário `root` costuma ter senha vazia ou usar a senha
do seu usuário do sistema. Isso é conveniente e é para desenvolvimento
apenas. Um MySQL com root sem senha exposto na rede é encontrado por
varredura automática em questão de horas.

Na sua máquina, sem exposição externa, tudo bem. No servidor da Casa
Amarela, não.
:::

Primeiro comando:

```text
mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
4 rows in set (0.01 sec)
```

`SHOW DATABASES` lista os bancos que existem nesse servidor. Os quatro que
apareceram são do próprio MySQL — ele usa banco de dados para guardar
informação sobre os bancos de dados, o que é circular e funciona.

Repare no ponto e vírgula. No cliente do MySQL, ele é **obrigatório**: é o
que diz "acabei de escrever, pode executar". Esquecer o `;` é o erro número
um de quem está começando, e o sintoma é o prompt mudar para `->` e ficar
esperando você terminar a frase.

Agora o banco da Casa Amarela:

```text
mysql> CREATE DATABASE casa_amarela
    -> CHARACTER SET utf8mb4
    -> COLLATE utf8mb4_unicode_ci;
Query OK, 1 row affected (0.02 sec)

mysql> USE casa_amarela;
Database changed

mysql> SHOW TABLES;
Empty set (0.00 sec)
```

Três comandos e uma lição em cada um.

`CREATE DATABASE` cria o banco. Repare no `->` das linhas 2 e 3: é o prompt
de continuação, porque o comando só terminou no `;` da terceira linha.

O `CHARACTER SET utf8mb4` diz em que codificação o banco vai guardar texto.
Essa escolha é a mesma do capítulo @cap:strings, agora do outro lado: sem
ela, você pode acabar com um banco em `latin1` e com o segundo José de
Alencar nascendo sozinho.

:::trivia
O nome `utf8mb4` existe porque o MySQL passou dez anos chamando de `utf8`
uma codificação que **não** era UTF-8 completo: ela suportava no máximo três
bytes por caractere, o que cobre acento e não cobre emoji nem alguns
ideogramas. Quando arrumaram, já havia banco demais no mundo usando o nome
errado para poder consertá-lo.

A saída foi criar `utf8mb4` — "UTF-8, de verdade, até quatro bytes" — e
deixar o `utf8` antigo como sinônimo do errado. Hoje `utf8` é apelido de
`utf8mb4` nas versões novas, mas escrever `utf8mb4` explicitamente continua
sendo o certo.
:::

`USE casa_amarela` escolhe em qual banco os próximos comandos vão trabalhar.
Sem isso, o MySQL não sabe de qual banco você está falando.

`SHOW TABLES` lista as tabelas. Está vazio, porque ainda não existe nenhuma.

## Tabela, linha, coluna

Falta o vocabulário, e ele já está na gaveta da Vera.

A gaveta tem um maço de fichas do mesmo tipo: todas com os mesmos campos
impressos — tombo, título, autor, estado —, cada uma preenchida com valores
diferentes.

| Na gaveta | No banco |
|---|---|
| o maço de fichas de exemplar | uma **tabela** chamada `exemplares` |
| uma ficha | uma **linha** (ou registro) |
| o campo "tombo" impresso na ficha | uma **coluna** chamada `tombo` |
| o que está escrito no campo | o **valor** daquela linha naquela coluna |
| a gaveta inteira | o **banco de dados** `casa_amarela` |

Tabela: A metáfora não é aproximada: o modelo relacional foi desenhado em
1970 por Edgar Codd pensando exatamente nisso.

Duas diferenças entre a ficha e a tabela, e as duas são vantagens do papel
que o banco troca de propósito.

Na ficha, a Vera pode escrever qualquer coisa em qualquer campo — inclusive
"não sei" no campo de data. Numa tabela, cada coluna tem um **tipo**
declarado, e o banco recusa o que não encaixa.

E na gaveta, se duas fichas tiverem o mesmo tombo, ninguém percebe. Numa
tabela, dá para pedir que o banco impeça.

:::key
Essa é a troca que o capítulo inteiro propõe: você abre mão da liberdade de
escrever qualquer coisa em qualquer lugar, e ganha um programa que recusa
dado inválido na porta, em vez de descobri-lo dois anos depois num
relatório que não fecha.

O nome disso é **esquema** — a descrição de quais tabelas existem, quais
colunas cada uma tem e o que cabe em cada coluna.
:::

:::note Na sua carreira
"Por que não guardar em arquivo?" é uma pergunta legítima, e a resposta
honesta é: às vezes guarde.

Configuração, log, cache de resultado, importação de planilha, arquivo que
uma pessoa por vez edita — tudo isso vive bem em arquivo, e colocar banco no
meio é trabalho a mais sem ganho nenhum.

A pergunta que separa os dois casos tem três partes: **duas pessoas escrevem
ao mesmo tempo? você precisa buscar sem carregar tudo? alguma regra precisa
ser garantida mesmo quando o programa tiver defeito?** Um "sim" em qualquer
uma delas já pede banco.

Saber justificar a escolha nessa linguagem — e não em "banco é mais
profissional" — é o que diferencia uma decisão de arquitetura de um hábito.
:::

:::summary
- Dado em memória é volátil; ele só existe enquanto o programa roda.
- `json_encode` + `file_put_contents` grava; `file_get_contents` +
	`json_decode` com `true` lê de volta como array.
- Ler, alterar e gravar o arquivo inteiro produz corrida: quem grava por
	último apaga o trabalho do outro, sem erro nenhum.
- `flock` resolve o caso pequeno e não resolve a lista.
- Um SGBD é outro programa, que coordena quem escreve porque está fora de
	todos eles.
- Tabela é o maço de fichas, linha é a ficha, coluna é o campo impresso.
- Esquema é a descrição do que cabe onde — a liberdade que você troca por
	garantia.
:::

:::checkpoint
Você grava e lê dados em arquivo, consegue reproduzir a corrida em dois
terminais e explicar por que ela acontece, tem um MySQL rodando, e criou o
banco `casa_amarela` com a codificação certa.
:::

:::exercise level=1
Escreva dois programas: um que acrescente um exemplar ao `acervo.json` e
outro que liste o que está gravado. Rode o primeiro três vezes e confira com
o segundo.

:::answer
```php title="cadastrar.php"
<?php

$arquivo = 'acervo.json';

$acervo = file_exists($arquivo)
    ? json_decode(file_get_contents($arquivo), true)
    : [];

$acervo[] = [
    'tombo' => (int) $argv[1],
    'titulo' => $argv[2],
];

file_put_contents(
    $arquivo,
    json_encode($acervo, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)
);

echo "acervo com ", count($acervo), " exemplares\n";
```

```php title="listar.php"
<?php

$acervo = json_decode(file_get_contents('acervo.json'), true);

foreach ($acervo as $e) {
    echo $e['tombo'], ' - ', $e['titulo'], "\n";
}
```

```text
$ php cadastrar.php 812 "O Cortiço"
acervo com 1 exemplares
$ php cadastrar.php 907 "Vidas Secas"
acervo com 2 exemplares
$ php listar.php
812 - O Cortiço
907 - Vidas Secas
```

Repare nas aspas em `"O Cortiço"` na linha de comando: sem elas, o terminal
quebraria o título em dois argumentos no espaço, e `$argv[2]` seria só `O`.
:::

:::exercise level=2
Reproduza a corrida da seção "10h12" na sua máquina, com os dois terminais.
Depois use `flock` para impedi-la, e explique o que você passou a pagar em
troca.

:::answer
```php title="emprestar_com_trava.php"
<?php

$arquivo = 'emprestimos.json';

$f = fopen($arquivo, 'c+');
flock($f, LOCK_EX);

$conteudo = stream_get_contents($f);
$emprestimos = $conteudo === '' ? [] : json_decode($conteudo, true);

echo "li: ", count($emprestimos), " emprestimos\n";
sleep(5);

$emprestimos[] = ['exemplar' => (int) $argv[1], 'leitor' => $argv[2]];

ftruncate($f, 0);
rewind($f);
fwrite($f, json_encode($emprestimos));

flock($f, LOCK_UN);
fclose($f);

echo "gravei: ", count($emprestimos), " emprestimos\n";
```

```text
Terminal 1                          Terminal 2
$ php emprestar_com_trava.php 812 Marlene
li: 0 emprestimos
                                    $ php ... 344 Rapaz
                                    (parado, esperando)
gravei: 1 emprestimos
                                    li: 1 emprestimos
                                    gravei: 2 emprestimos
```

Dois empréstimos. O defeito sumiu.

`fopen` com `'c+'` abre para leitura e escrita sem apagar o conteúdo.
`flock($f, LOCK_EX)` pede a trava exclusiva e **fica esperando** se outro
processo já a tiver. `ftruncate` e `rewind` esvaziam o arquivo antes de
reescrevê-lo, porque a trava não é sobre o conteúdo.

**O que você passou a pagar:** o Terminal 2 ficou cinco segundos parado,
sem fazer nada, esperando um arquivo. Com dois atendentes isso é invisível.
Com vinte, cada um espera a soma de todos os anteriores — e a operação
inteira, mesmo a de quem só queria consultar, entra na mesma fila.

Além disso, o programa passou de sete linhas a quinze, e três delas
(`ftruncate`, `rewind`, `flock` de liberação) são as que alguém vai esquecer
na próxima alteração.
:::

:::exercise level=3
A Casa Amarela quer saber quantos empréstimos de livros infantis houve em
fevereiro. Os dados estão num `emprestimos.json` com 8.412 registros e num
`livros.json` com 4.000.

Escreva o programa que responde isso lendo os arquivos. Depois liste o que
essa solução não consegue fazer, e o que cada item da sua lista exigiria.

:::answer
```php
<?php

$json = file_get_contents('emprestimos.json');
$emprestimos = json_decode($json, true);

$livros = json_decode(file_get_contents('livros.json'), true);

$livro_por_id = array_column($livros, null, 'id');

$total = 0;

foreach ($emprestimos as $e) {
    if (!str_starts_with($e['retirado_em'], '2027-02')) {
        continue;
    }

    $livro = $livro_por_id[$e['livro_id']] ?? null;

    if ($livro !== null && $livro['assunto'] === 'infantil') {
        $total++;
    }
}

echo $total, "\n";
```

Funciona, e é a indexação do capítulo @cap:repeticoes aplicada a dados
persistidos. Quatro coisas que ela não consegue fazer:

**Não consegue responder sem carregar tudo.** Para contar os empréstimos de
um mês, os dois arquivos inteiros foram lidos do disco e transformados em
array na memória — 12.412 registros para chegar a um número. Um banco lê só
o que o filtro alcança, e com índice nem isso.

**Não consegue rodar enquanto alguém grava.** Se um empréstimo for
registrado no meio da leitura, o programa pode ler um JSON pela metade e
`json_decode` devolver `null`. Isso exige a coordenação da seção anterior.

**Não consegue garantir que `livro_id` aponta para um livro que existe.** O
`?? null` está ali justamente porque pode não apontar. Um banco recusa a
gravação de um empréstimo com livro inexistente — é a chave estrangeira.

**Não consegue responder a pergunta seguinte sem um programa novo.** "E em
março?" exige editar o código. "E por assunto?" exige outro programa. Em
SQL, as três perguntas são três linhas diferentes, escritas na hora, sem
editar nada.

A quarta é a mais subestimada das quatro. O custo real do arquivo não é o
desempenho: é que **cada pergunta nova vira uma tarefa de programação**, e a
Vera não vai abrir chamado para descobrir uma coisa que ela queria saber
agora.
:::
