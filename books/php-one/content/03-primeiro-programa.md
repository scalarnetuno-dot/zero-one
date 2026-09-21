---
title: "O primeiro programa"
number: 2
slug: primeiro-programa
part: p1
kicker: "Duas linhas de PHP, três instalações diferentes na mesma máquina e uma tela branca que não é erro nenhum."
goal: >-
  Escrever, salvar e rodar PHP pelo terminal e pelo navegador; entender o que
  acontece entre o Enter e a saída; e encontrar a mensagem de erro que o
  servidor engoliu.
---

:::story A hospedagem do sobrinho
— Consegui a hospedagem — anunciou Seu Juvenal, com a satisfação de quem
resolveu o problema do mês.

— Onde?

— Com o sobrinho da Dona Marlene. Ele tem uma empresa.

O painel abriu numa janela de 2011, com botões em degradê e um ícone de
disquete. No canto, um campo dizia:

```text
PHP Version: 5.6.40    [Alterar]
```

Dedé clicou em **Alterar**. As opções eram 5.4, 5.6 e 7.0.

— Tem 8?

— O sobrinho disse que 8 é instável.

O PHP 8 tinha sido lançado havia seis anos. O 5.6 tinha parado de receber
correção de segurança havia nove.

— E o acesso? Tem SSH?

— Tem FTP.

Seu Juvenal entregou um papel com o usuário, a senha, e — escrito à mão, num
canto — a observação *"não mexer na pasta antiga"*.
:::

Este capítulo é sobre rodar PHP. Ele parece o capítulo mais simples do livro
e contém a armadilha que mais consome tempo de quem está começando: **o PHP
que roda no seu terminal quase nunca é o mesmo que roda no servidor.**

## O PHP que está rodando

```text
$ which php
/usr/bin/php
$ php -v
PHP 8.3.14 (cli)
```

O `(cli)` no fim é o detalhe que importa. Ele diz que este é o PHP de
**linha de comando**. Existe outro, o do servidor web, que pode ser uma
versão diferente, com um arquivo de configuração diferente e um conjunto de
extensões diferente — na mesma máquina, ao mesmo tempo.

:::term SAPI
*Server API*: o modo como o PHP é executado. `cli` é o terminal; `fpm` é o
que roda atrás do Nginx; `apache2handler` é o módulo do Apache. O mesmo
arquivo `.php` pode se comportar de formas diferentes em cada um.
:::

:::pitfall
O sintoma clássico: você instala uma extensão, `php -m` mostra que ela está
lá, e a página no navegador continua dizendo que ela não existe. São dois
PHP. A confirmação leva dez segundos — crie um arquivo com
`<?php phpinfo();`, abra **pelo navegador** e compare a versão e o caminho
do `php.ini` com o que o `php -v` disse no terminal.
:::

## Uma tag, uma saída, dois caminhos

```php title="ola.php" numbered
<?php

echo "Olá, Casa Amarela\n";
```

```text
$ php ola.php
Olá, Casa Amarela
```

Pronto. Você programou.

`<?php` abre o modo PHP. Tudo antes dela é enviado ao cliente como texto
puro — inclusive um espaço em branco, e isso vai importar daqui a três
parágrafos.

A tag de fechamento, `?>`, é **opcional no fim do arquivo**. Mais que
opcional: em arquivo que só tem PHP, ela é proibida por convenção, e a razão
é concreta:

:::compare left="O arquivo que vai dar problema" right="O jeito certo" lang="php"
<?php
function multa(): int
{
    return 80;
}
?>
---
<?php
function multa(): int
{
    return 80;
}
:::

Repare na quebra de linha depois do `?>` no lado esquerdo. Ela é enviada ao
navegador como conteúdo. Meses depois, quando alguém tentar redirecionar ou
enviar um cabeçalho HTTP, vai receber isto:

```text
Warning: Cannot modify header information - headers already
sent by (output started at /app/funcoes.php:7) in
/app/index.php on line 3
```

A mensagem é boa: diz o arquivo e a linha onde a saída começou. A causa é um
espaço em branco depois de um `?>` que não precisava existir.

:::key
Arquivo que contém apenas PHP não leva `?>`. Essa é uma das poucas regras de
estilo que a PSR-12 justifica por consequência técnica, e não por gosto.
:::

### Imprimir

```php title="saida.php" numbered
<?php

$titulo = "O Cortiço";
$exemplares = 3;

echo "Temos ", $exemplares, " exemplares de ", $titulo, "\n";
echo "Temos {$exemplares} exemplares de {$titulo}\n";
printf("Temos %d exemplares de %s\n", $exemplares, $titulo);
```

```text
Temos 3 exemplares de O Cortiço
Temos 3 exemplares de O Cortiço
Temos 3 exemplares de O Cortiço
```

Três formas, o mesmo resultado. `echo` aceita vários argumentos separados
por vírgula, e com aspas duplas interpola variáveis — o capítulo
@cap:strings trata das diferenças entre aspas com o cuidado que elas
merecem.

E existe `var_dump`, que não é saída para o usuário; é para você:

```text
$ php -r 'var_dump(3, "3", 3.0, true, null);'
int(3)
string(1) "3"
float(3)
bool(true)
NULL
```

Guarde essa ferramenta. No capítulo @cap:variaveis-e-tipos ela vai explicar
comportamentos que nenhuma outra explicaria.

## Do terminal para o navegador

PHP nasceu para a web, e a segunda forma de rodá-lo é por HTTP:

```text
$ php -S localhost:8000
[Thu Nov 21 10:02:11 2026] PHP 8.3.14 Development Server
(http://localhost:8000) started
```

Abra <http://localhost:8000/ola.php>. A mesma frase aparece, agora dentro de
uma página.

:::diagram type="flowchart" caption="Dois caminhos, o mesmo arquivo: muda quem chama e para onde vai a saída."
nodes:
  - { id: arq, type: io,      text: "ola.php" }
  - { id: cli, type: process, text: "php ola.php (CLI)" }
  - { id: web, type: process, text: "php -S (servidor)" }
  - { id: t,   type: io,      text: "terminal" }
  - { id: n,   type: io,      text: "navegador" }
edges:
  - { from: arq, to: cli }
  - { from: arq, to: web }
  - { from: cli, to: t }
  - { from: web, to: n }
:::

:::warning
O nome é literal: **Development Server**. Ele atende uma requisição por vez,
não tem reescrita de URL decente e não foi feito para carga. Para aprender e
investigar, basta. Produção é outra conversa — certamente não é a hospedagem
do sobrinho da Dona Marlene.
:::

## O arquivo certo, no servidor errado

:::story Dois servidores
Tainá editou o arquivo, salvou, recarregou. Nada mudou.

Salvou de novo. Recarregou de novo. Nada.

Acrescentou um `echo "TESTE"` gigante no topo, com trinta exclamações.
Recarregou. Nada.

Apagou o arquivo inteiro. Recarregou. A página continuou lá, funcionando
perfeitamente, exibindo um conteúdo que tecnicamente não existia mais.

Foi nesse ponto que ela chamou o Dedé, já em dúvida sobre a natureza da
realidade.

Ele pediu a URL e abriu o histórico do terminal dela. Havia dois `php -S`
rodando: um na porta 8000, aberto naquela manhã, e outro na 8080, esquecido
aberto havia duas semanas, servindo uma cópia antiga da pasta.

O navegador estava na 8080.

— O arquivo certo, no servidor errado — disse ele. — Vai acontecer de novo.
Quando acontecer, a primeira pergunta não é "o que eu escrevi errado". É "o
que está rodando".
:::

A segunda parte do desastre aconteceu meia hora depois, quando a Tainá
finalmente acertou a porta e recebeu isto:

```text
(sem uma linha sequer — código-fonte vazio)
```

Página em branco. Sem erro, sem texto, sem nada.

## Ler o erro inteiro

Duas causas diferentes, e as duas são clássicas.

**A primeira foi o erro de sintaxe.** Ela tinha escrito:

```php title="quebrado.php" numbered
<?php

$titulo = "O Cortiço"
echo $titulo;
```

```text
PHP Parse error:  syntax error, unexpected token "echo",
expecting "," or ";" in /app/quebrado.php on line 4
```

O erro aponta a **linha 4**, e o problema está na 3: falta um ponto e
vírgula. Isso não é defeito da mensagem — é como todo analisador funciona.
Ele só percebe que algo está faltando quando encontra o que não esperava, e
isso acontece na linha seguinte.

:::key
Erro de sintaxe aponta onde o analisador **percebeu**, não onde você
**errou**. Regra prática: leia a linha apontada e a anterior. Em noventa por
cento dos casos o problema está na anterior — ponto e vírgula, parêntese ou
chave.
:::

Um `Parse error` tem uma característica que assusta na primeira vez: ele
impede o arquivo **inteiro** de rodar. Não há saída parcial, nem as linhas
antes do erro. O PHP analisa o arquivo todo antes de executar qualquer
coisa.

**A segunda causa foi o motivo de a Tainá não ter visto essa mensagem.**

```text
$ php -i | grep -E "display_errors|error_log"
display_errors => Off => Off
error_log => no value => no value
```

Com `display_errors` desligado e nenhum `error_log` configurado, a mensagem
foi para a saída de erro do servidor — que, num PHP-FPM, é
`/var/log/php8.3-fpm.log`, e não onde ela estava olhando.

A informação existiu. Foi produzida, escrita e arquivada em outro lugar.

## O erro no lugar certo

**Em desenvolvimento, ligue tudo:**

```text title="php.ini — só em desenvolvimento"
display_errors = On
display_startup_errors = On
error_reporting = E_ALL
```

**Em produção, o contrário — e não é opcional:**

```text title="php.ini — produção"
display_errors = Off
error_log = /var/log/php/erros.log
error_reporting = E_ALL
```

:::warning
`display_errors = On` em produção é falha de segurança. A mensagem de erro
do PHP entrega caminho absoluto de arquivo, nome de função, às vezes trecho
de SQL e valor de variável. É informação de graça para quem estiver
sondando o site.

Repare que `error_reporting` continua `E_ALL` nos dois. A diferença não é
**registrar menos** — é **mostrar para quem**. Em produção, o log fica para
a equipe e a mensagem pública fica curta.
:::

**E existe uma checagem que não custa nada:**

```text
$ php -l quebrado.php
PHP Parse error: syntax error, unexpected token "echo" ...
Errors parsing quebrado.php

$ php -l ola.php
No syntax errors detected in ola.php
```

`php -l` confere a sintaxe sem executar. É a verificação mais barata que
existe, e no capítulo @cap:git-ci-e-deploy ela vira o primeiro passo da
esteira — falha em segundos, antes de subir banco ou rodar teste.

### A tabela da tela branca

A tela branca é o erro mais assustador porque parece ausência de informação.
Ela quase sempre é uma destas quatro coisas:

| Causa | Como confirmar |
|---|---|
| Erro de sintaxe com `display_errors` off | `php -l arquivo.php` |
| Erro fatal em execução | ler o log do PHP ou do servidor |
| Memória ou tempo esgotados | procurar `Allowed memory size` no log |
| Saída vazia mesmo, sem erro | `var_dump` antes do ponto suspeito |

Tabela: Nenhuma delas é resolvida recarregando a página, que é exatamente o
que todo mundo faz nos primeiros cinco minutos.

:::practice
Crie um arquivo que chame uma função inexistente — `descontar()`, por
exemplo — e rode pelos dois caminhos: `php arquivo.php` e pelo navegador com
`php -S`. Compare o que aparece em cada um. Essa diferença é a mesma que vai
existir entre a sua máquina e o servidor, e vê-la uma vez economiza horas
depois.
:::

:::note Na sua carreira
Antes de aceitar mexer num sistema que você não conhece — freelance,
projeto novo, empresa nova —, quatro perguntas valem mais que qualquer
leitura de código:

1. **Qual versão de PHP roda em produção?** Define o que você pode usar.
2. **Como eu subo uma alteração?** Se a resposta for "FTP", o livro inteiro
   do capítulo @cap:git-ci-e-deploy virou urgente.
3. **Onde ficam os logs?** Se ninguém souber, você vai depurar às cegas.
4. **Existe um ambiente igual ao de produção onde eu possa errar?** Se não
   existir, o ambiente de testes é a produção — e alguém precisa saber disso
   por escrito, antes do primeiro incidente.

Fazer essas quatro perguntas não é desconfiança. É o equivalente a um
eletricista perguntar onde fica o disjuntor.
:::

:::summary
- Existem dois PHP na sua máquina: o de terminal e o do servidor.
- Arquivo só com PHP não leva `?>` — espaço depois dele vira saída.
- `echo` imprime; `var_dump` explica.
- `php -S` sobe um servidor de desenvolvimento, e só para isso.
- Erro de sintaxe aponta onde o analisador percebeu: leia a linha anterior.
- Página em branco é erro escondido, não ausência de erro.
- `display_errors` ligado em desenvolvimento, desligado em produção, com
  `error_reporting` em `E_ALL` nos dois.
:::

:::exercise level=1
Escreva um arquivo que imprima o nome da biblioteca e a quantidade de
títulos do acervo, usando interpolação de variável.

:::answer
```php
<?php

$nome = "Casa Amarela";
$titulos = 4000;

echo "{$nome}: {$titulos} títulos no acervo\n";
```
:::

:::exercise level=2
Reproduza a tela branca de propósito: desligue `display_errors`, crie um
arquivo com erro de sintaxe e abra pelo navegador. Depois encontre a
mensagem sem ligar `display_errors` de volta.

:::answer
```text
$ php -S localhost:8000 -d display_errors=0
```
Abra o arquivo quebrado: página em branco. Agora, sem mexer na
configuração:

```text
$ php -l quebrado.php
PHP Parse error: syntax error ... on line 4
```

O `-d` do `php -S` sobrescreve uma diretiva só para aquela execução, o que é
prático para reproduzir o comportamento de produção sem editar o `php.ini`.

E vale notar que o servidor embutido escreve os erros no próprio terminal em
que foi iniciado — então, neste caso, a informação estava na janela ao lado
o tempo todo. Em servidor de verdade, ela estaria no arquivo de log.
:::

:::exercise level=2
Crie dois arquivos: um `funcoes.php` que termina com `?>` seguido de uma
linha em branco, e um `index.php` que faz `require 'funcoes.php'` e depois
chama `header('Location: /painel')`. Rode e leia o erro.

:::answer
```text
Warning: Cannot modify header information - headers already
sent by (output started at /app/funcoes.php:6) in
/app/index.php on line 4
```
A mensagem entrega o culpado com arquivo e linha: `funcoes.php:6` é a linha
em branco depois do `?>`. Apague as duas últimas linhas do arquivo e o
redirecionamento volta a funcionar.

Vale reproduzir isso uma vez porque a mensagem é assustadora e a causa é
ridícula — e porque, em sistema legado com quarenta `include`, encontrar
qual arquivo tem o espaço sobrando é exatamente esse número no fim da
primeira linha.
:::

:::exercise level=3
O arquivo abaixo funciona no seu terminal e devolve página em branco na
hospedagem da Casa Amarela. Liste quatro hipóteses, em ordem do que você
verificaria primeiro, e diga como confirma cada uma.

```php
<?php
require 'config.php';
$conexao = conectar();
echo "ok";
```

:::answer
**1. Versão diferente de PHP.** Seu terminal roda 8.3; a hospedagem roda
5.6. Qualquer sintaxe posterior ao PHP 5.6 — tipo de retorno, `??`, arrow
function — é erro de sintaxe lá e código válido aqui. Confirmo com um
`phpinfo()` servido **pelo mesmo caminho da aplicação**, não pelo terminal.

**2. `display_errors` desligado escondendo um erro fatal.** É a hipótese
mais provável, porque o sintoma é exatamente esse. Confirmo lendo o log; se
não souber onde ele está, o `phpinfo()` da hipótese 1 já responde.

**3. `config.php` não encontrado.** `require` com caminho relativo depende
do diretório de trabalho, que no servidor não é o mesmo do terminal. Um
`require` que falha é erro fatal — e, com `display_errors` off, é página em
branco. Confirmo com `var_dump(getcwd())`, e conserto trocando por
`require __DIR__ . '/config.php'`.

**4. Extensão ausente.** `conectar()` provavelmente usa PDO ou mysqli. Se a
extensão não estiver compilada no SAPI do servidor, a função não existe.
Confirmo procurando a extensão na saída do `phpinfo()`.

**A ordem importa, e é a parte que vale do exercício.** As duas primeiras
hipóteses são checagens de trinta segundos que revelam as outras duas — o
`phpinfo()` responde versão, `display_errors`, caminho do log e extensões de
uma vez só. Investigar o código antes de olhar essa página é o erro de
método mais comum de quem está começando: a informação já existe, alguém só
precisa lê-la.
:::

:::story A piada final
Duas semanas depois, o sobrinho da Dona Marlene respondeu ao chamado sobre o
PHP 8.

> *"Não recomendamos. Nossa infraestrutura é otimizada para 5.6, que é a
> versão mais estável do mercado."*

Dedé encaminhou a mensagem para a Vera, sem comentário.

A resposta dela veio em quatro minutos:

> *"Ele também acha que o Sistema tá ótimo."*
:::
