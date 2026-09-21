---
title: "O primeiro programa"
number: 3
slug: primeiro-programa
part: p1
kicker: "Duas linhas de PHP, três instalações diferentes na mesma máquina e uma tela branca que não é erro nenhum."
goal: >-
  Escrever, salvar e rodar PHP pelo terminal e pelo navegador; comentar
  código; imprimir de quatro formas diferentes; e encontrar a mensagem de
  erro que o servidor engoliu.
---

:::story A hospedagem do sobrinho
— Consegui a hospedagem — anunciou Seu Juvenal, com a satisfação de quem
resolveu o problema do mês antes das dez da manhã.

— A Vertexo ia contratar um servidor — disse Márcia.

— Mas esse é de graça. Sobrinho da Dona Marlene. Ele tem uma empresa.

O painel abriu numa janela de 2011, com botões em degradê e um ícone de
disquete no menu. No canto, um campo:

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

Seu Juvenal entregou um papel dobrado com o usuário, a senha e — escrito à
mão, num canto, com caneta de outra cor — a observação *"não mexer na pasta
antiga"*.

Márcia guardou o papel na pasta do projeto.

— Isso é risco pra março?

— Isso é risco pra hoje.
:::

Rodar PHP parece a parte mais simples do trabalho, e é onde mora a armadilha
que mais consome tempo de quem está começando: **o PHP que roda no seu
terminal quase nunca é o mesmo que roda no servidor.**

## Dois PHP na mesma máquina

```text
$ which php
/usr/bin/php
$ php -v
PHP 8.3.14 (cli)
```

O `(cli)` no fim da primeira linha é o detalhe que importa. Ele diz que este
é o PHP de **linha de comando** — o que responde quando você digita `php`
num terminal.

Existe outro, o que atende o navegador. Pode ser uma versão diferente, com
um arquivo de configuração diferente e um conjunto de extensões diferente,
na mesma máquina, ao mesmo tempo.

:::term SAPI
*Server API*: o modo como o PHP foi acoplado a quem o chama. `cli` é o
terminal. `fpm` é o processo que fica esperando o Nginx mandar serviço.
`apache2handler` é o PHP embutido dentro do Apache. O mesmo arquivo `.php`
pode se comportar de forma diferente em cada um, porque cada um lê o seu
próprio `php.ini`.
:::

:::pitfall
O sintoma clássico: você instala uma extensão, `php -m` mostra que ela está
lá, e a página no navegador continua dizendo que ela não existe.

São dois PHP. A confirmação leva dez segundos — crie um arquivo com
`<?php phpinfo();` dentro, abra **pelo navegador** e compare a versão e o
caminho do `php.ini` com o que o `php -v` disse no terminal. Depois apague o
arquivo: `phpinfo()` mostra a configuração inteira do servidor, e não é
informação para deixar pública.
:::

## Uma tag, uma saída

```php title="ola.php" numbered
<?php

echo "Olá, Casa Amarela\n";
```

```text
$ php ola.php
Olá, Casa Amarela
```

Pronto. Você programou.

Vale destrinchar as três linhas, porque cada uma tem uma decisão dentro.

**`<?php`** abre o modo PHP. Tudo que estiver antes dessa tag — inclusive um
espaço em branco ou uma linha vazia — é enviado direto para quem pediu a
página, sem passar pelo interpretador. Isso parece irrelevante e vai
importar daqui a dois parágrafos.

**`echo`** imprime. Não é função, é uma construção da linguagem, e por isso
funciona sem parênteses.

**`"\n"`** é uma quebra de linha. Dentro de aspas duplas, a barra invertida
liga o modo "o próximo caractere é especial": `\n` vira quebra de linha,
`\t` vira tabulação. Dentro de aspas simples isso não acontece — `'\n'` são
dois caracteres, uma barra e um ene.

E o **ponto e vírgula** no fim encerra a instrução. Esquecer um é o erro
número um de quem está começando, e a mensagem que ele produz tem uma
peculiaridade que vale conhecer antes de encontrá-la.

## Comentar

Três formas, e você vai usar duas:

```php title="comentarios.php" numbered
<?php

// uma linha, a forma padrão

# uma linha também, herdada do shell, hoje rara

/*
   várias linhas
   para quando a explicação não cabe numa
*/

echo "Casa Amarela\n"; // comentário no fim da linha também vale
```

O `//` é o que se usa. O `#` funciona e aparece em código antigo. O bloco
`/* */` serve para explicações longas — e tem uma variante com dois
asteriscos na abertura, `/** */`, que ferramentas de análise leem como
documentação.

:::key
Comentário que explica **o que** a linha faz é ruído: a linha já diz.
Comentário que explica **por que** a decisão foi aquela é a coisa mais
valiosa que se pode deixar num arquivo.

`// soma 1 ao contador` não ajuda ninguém. `// a Vera pediu que domingo não
conte como atraso; a biblioteca não abre` ainda vai estar prestando serviço
daqui a cinco anos.
:::

## A tag que você não vai fechar

A tag de fechamento, `?>`, é **opcional no fim do arquivo**. Mais que
opcional: em arquivo que só tem PHP, ela é evitada por convenção, e a razão
é concreta.

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

Repare na quebra de linha depois do `?>` no lado esquerdo. Ela está fora do
modo PHP, então é conteúdo — e é enviada ao navegador como se fosse parte da
página.

Meses depois, quando alguém tentar redirecionar o usuário ou enviar
qualquer outra informação de cabeçalho, vai receber isto:

```text
Warning: Cannot modify header information - headers already
sent by (output started at /app/funcoes.php:7) in
/app/index.php on line 3
```

A mensagem é generosa: diz o arquivo e a linha exata onde a saída começou. A
causa é um espaço em branco depois de um `?>` que não precisava existir.

:::key
Arquivo que contém apenas PHP não leva `?>`. É uma das poucas regras de
estilo que se justifica por consequência técnica, e não por gosto.
:::

## Quatro formas de imprimir

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

A primeira linha usa `echo` com vários pedaços separados por vírgula. Eles
saem grudados, na ordem.

A segunda usa **interpolação**: dentro de aspas duplas, o PHP troca o nome
da variável pelo valor dela. As chaves em `{$titulo}` não são obrigatórias
quando o nome termina claramente, mas são obrigatórias quando não termina —
e usá-las sempre poupa a decisão.

A terceira usa `printf`, que recebe um molde e os valores para encaixar
nele. O `%d` diz "aqui entra um número inteiro" e o `%s` diz "aqui entra um
texto". Os valores vêm depois, na ordem dos marcadores. É mais trabalho para
uma frase curta e é o que você vai querer quando precisar alinhar colunas ou
controlar casas decimais.

Existe ainda `print`, que faz quase o mesmo que `echo` e aceita um valor só.
A diferença prática é irrelevante; use `echo`.

E existe uma quarta, que não é saída para o usuário — é para você:

```text
$ php -r 'var_dump(3, "3", 3.0, true, null);'
int(3)
string(1) "3"
float(3)
bool(true)
NULL
```

`var_dump` imprime o **tipo** junto com o valor. Repare na diferença entre
`int(3)` e `string(1) "3"`: para o `echo`, os dois sairiam como `3`, e você
nunca saberia qual é qual. Essa é a ferramenta que responde em vez de você
adivinhar, e ela vai aparecer em quase toda página daqui para frente.

## Do terminal para o navegador

PHP nasceu para a web, e a segunda forma de rodá-lo é por HTTP. Não é
preciso instalar Apache nem Nginx: o próprio PHP traz um servidor pequeno.

```text
$ php -S localhost:8000
[Thu Nov 21 10:02:11 2026] PHP 8.3.14 Development Server
(http://localhost:8000) started
```

O comando fica rodando e ocupa o terminal — é assim mesmo. Ele serve os
arquivos da pasta em que você estava quando o iniciou. Abra
<http://localhost:8000/ola.php> e a mesma frase aparece, agora dentro de uma
página. Para encerrar, `Ctrl+C`.

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
O nome que ele imprime é literal: **Development Server**. Atende uma
requisição por vez, não tem reescrita de URL decente e não aguenta carga
nenhuma. Para aprender e investigar, basta. Produção é outra conversa — e
certamente não é a hospedagem do sobrinho da Dona Marlene.
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

— Vai acontecer de novo — disse ele. — Quando acontecer, a primeira pergunta
não é "o que eu escrevi errado". É "o que está rodando".

Tainá anotou no caderno. Era a segunda linha da lista.
:::

Meia hora depois, com a porta certa, veio o segundo problema: página em
branco. Sem erro, sem texto, sem nada. Código-fonte vazio.

## O erro aponta onde ele percebeu

Ela tinha escrito isto:

```php title="quebrado.php" numbered
<?php

$titulo = "O Cortiço"
echo $titulo;
```

Rodando pelo terminal, a mensagem aparece:

```text
PHP Parse error:  syntax error, unexpected token "echo",
expecting "," or ";" in /app/quebrado.php on line 4
```

O erro aponta a **linha 4**, e o problema está na **3**: falta um ponto e
vírgula. Isso não é defeito da mensagem. O analisador estava lendo a linha 3
e ela ainda podia continuar — nada impede uma expressão de ocupar várias
linhas. Ele só descobriu que faltava alguma coisa quando encontrou, na linha
seguinte, uma palavra que não pode aparecer ali.

:::key
Erro de sintaxe aponta onde o analisador **percebeu**, não onde você
**errou**. Regra prática: leia a linha apontada e a anterior. Em nove de
cada dez casos o problema está na anterior — ponto e vírgula, parêntese ou
chave.
:::

Um `Parse error` tem uma característica que assusta na primeira vez: ele
impede o arquivo **inteiro** de rodar. Não sai nada, nem as linhas anteriores
ao erro, porque o PHP analisa o arquivo todo antes de executar a primeira
instrução.

## Onde foi parar a mensagem

Mas a Tainá não viu mensagem nenhuma. Viu página em branco.

```text
$ php -i | grep -E "display_errors|error_log"
display_errors => Off => Off
error_log => no value => no value
```

`display_errors` desligado quer dizer "não mostre erros para quem pediu a
página". `error_log` sem valor quer dizer "e não os escreva em arquivo
nenhum". Juntas, as duas configurações fazem a mensagem ir para a saída de
erro do processo do servidor — que, num PHP-FPM, termina em
`/var/log/php8.3-fpm.log`, e não onde ela estava olhando.

A informação existiu. Foi produzida, formatada e arquivada em outro lugar.

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
de consulta ao banco e valor de variável. É informação de graça para quem
estiver sondando o site.

Repare que `error_reporting` continua `E_ALL` nos dois casos. A diferença
não é **registrar menos** — é **mostrar para quem**. Em produção o detalhe
fica no log, para a equipe, e o visitante vê uma página curta.
:::

E existe uma checagem que não custa nada:

```text
$ php -l quebrado.php
PHP Parse error: syntax error, unexpected token "echo" ...
Errors parsing quebrado.php

$ php -l ola.php
No syntax errors detected in ola.php
```

O `-l` vem de *lint*: confere a sintaxe sem executar o arquivo. É a
verificação mais barata que existe e roda em milissegundos.

### A tela branca, em quatro hipóteses

A tela branca assusta porque parece ausência de informação. Ela quase sempre
é uma destas quatro coisas:

| Causa | Como confirmar |
|---|---|
| Erro de sintaxe com `display_errors` off | `php -l arquivo.php` |
| Erro fatal em execução | ler o log do PHP ou do servidor |
| Memória ou tempo esgotados | procurar `Allowed memory size` no log |
| Saída vazia mesmo, sem erro | `var_dump` antes do ponto suspeito |

Tabela: Nenhuma delas é resolvida recarregando a página, que é exatamente o
que todo mundo faz nos primeiros cinco minutos.

:::practice
Crie um arquivo que chame uma função que não existe — `descontar()`, por
exemplo — e rode pelos dois caminhos: `php arquivo.php` e pelo navegador com
`php -S`. Compare o que aparece em cada um.

Essa diferença é a mesma que vai existir entre a sua máquina e o servidor de
produção, e vê-la uma vez economiza horas depois.
:::

:::note Na sua carreira
Antes de aceitar mexer num sistema que você não conhece — freelance,
projeto novo, empresa nova —, quatro perguntas valem mais do que qualquer
leitura de código:

1. **Qual versão de PHP roda em produção?** Define o que você pode usar.
2. **Como eu subo uma alteração?** Se a resposta for "FTP", você acabou de
	 descobrir o maior risco do projeto, e ele não é técnico: é que qualquer
	 pessoa com aquele papel pode publicar qualquer coisa, e ninguém vai saber
	 quem foi.
3. **Onde ficam os logs?** Se ninguém souber, você vai depurar às cegas.
4. **Existe um ambiente igual ao de produção onde eu possa errar?** Se não
	 existir, o ambiente de testes é a produção — e alguém precisa saber disso
	 por escrito, antes do primeiro incidente, não depois.

Fazer essas perguntas não é desconfiança. É o equivalente a um eletricista
perguntar onde fica o disjuntor.
:::

:::summary
- Existem dois PHP na sua máquina: o do terminal e o do servidor. Cada um lê
	o seu próprio `php.ini`.
- Arquivo só com PHP não leva `?>` — espaço depois dele vira saída, e quebra
	cabeçalho meses depois.
- Comentário bom explica por que, não o quê.
- `echo` imprime; interpolação troca variável por valor dentro de aspas
	duplas; `printf` encaixa valores num molde; `var_dump` mostra o tipo.
- `php -S` sobe um servidor de desenvolvimento, e só serve para isso.
- Erro de sintaxe aponta onde o analisador percebeu: leia a linha anterior.
- Página em branco é erro escondido, não ausência de erro.
:::

:::exercise level=1
Escreva um arquivo que imprima o nome da biblioteca, a quantidade de títulos
do acervo e o horário de funcionamento, usando interpolação de variável.
Depois troque a interpolação por `printf` e compare as duas versões.

:::answer
```php
<?php

$nome = "Casa Amarela";
$titulos = 4000;
$horario = "9h às 18h";

echo "{$nome}: {$titulos} títulos, {$horario}\n";
printf("%s: %d títulos, %s\n", $nome, $titulos, $horario);
```

```text
Casa Amarela: 4000 títulos, 9h às 18h
Casa Amarela: 4000 títulos, 9h às 18h
```

Para uma frase curta, a interpolação é mais legível. O `printf` começa a
ganhar quando o formato importa — casas decimais, largura de coluna,
alinhamento.
:::

:::exercise level=2
Reproduza a tela branca de propósito: crie um arquivo com erro de sintaxe e
sirva-o com os erros desligados. Depois encontre a mensagem sem ligar os
erros de volta.

:::answer
```text
$ php -S localhost:8000 -d display_errors=0
```

Abra o arquivo quebrado no navegador: página em branco. Agora, sem mexer em
configuração nenhuma:

```text
$ php -l quebrado.php
PHP Parse error: syntax error ... on line 4
```

O `-d` sobrescreve uma diretiva só para aquela execução, o que é prático
para reproduzir o comportamento de produção sem editar o `php.ini`.

Repare também que o servidor embutido escreve os erros no próprio terminal
em que foi iniciado — neste caso, a informação estava na janela ao lado o
tempo todo. Em servidor de verdade, estaria num arquivo de log.
:::

:::exercise level=2
Crie dois arquivos: um `funcoes.php` que termina com `?>` seguido de uma
linha em branco, e um `index.php` que faz `require 'funcoes.php'` e depois
chama `header('Location: /painel')`. O `require` insere o conteúdo de um
arquivo dentro do outro; `header` envia uma informação de cabeçalho HTTP —
aqui, um redirecionamento. Rode e leia o erro.

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
ridícula — e porque, num sistema legado com quarenta `include`, descobrir
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
5.6. Qualquer sintaxe posterior ao 5.6 é erro de sintaxe lá e código válido
aqui. Confirmo com um `phpinfo()` servido **pelo mesmo caminho da
aplicação**, não pelo terminal.

**2. Erros desligados escondendo um erro fatal.** É a hipótese mais
provável, porque o sintoma é exatamente esse. Confirmo lendo o log; se
ninguém souber onde ele fica, o `phpinfo()` da hipótese 1 já responde.

**3. `config.php` não encontrado.** O `require` com caminho relativo depende
do diretório de trabalho, que no servidor não é o mesmo do terminal. Um
`require` que falha é erro fatal — e, com os erros desligados, é página em
branco. Confirmo com `var_dump(getcwd())`, que imprime o diretório atual, e
conserto trocando por `require __DIR__ . '/config.php'`, onde `__DIR__` é a
pasta do próprio arquivo.

**4. Extensão ausente.** A função `conectar()` provavelmente fala com um
banco de dados. Se a extensão correspondente não estiver compilada no PHP do
servidor, a função não existe. Confirmo procurando a extensão na saída do
`phpinfo()`.

A ordem é a parte que vale do exercício. As duas primeiras hipóteses são
checagens de trinta segundos que revelam as outras duas: o `phpinfo()`
responde versão, erros, caminho do log e extensões de uma vez só. Investigar
o código antes de olhar essa página é o erro de método mais comum de quem
está começando — a informação já existe, alguém só precisa lê-la.
:::

:::story Otimizada para 5.6
Duas semanas depois, o sobrinho da Dona Marlene respondeu ao chamado sobre o
PHP 8.

> *"Não recomendamos. Nossa infraestrutura é otimizada para 5.6, que é a
> versão mais estável do mercado."*

Dedé encaminhou para a Vera, sem comentário nenhum.

A resposta veio em quatro minutos:

> *"Ele também acha que o Sistema tá ótimo."*

Encaminhou para a Márcia também. Essa demorou mais.

> *"Coloca na ata. Se a gente trocar de hospedagem em março, quero que esteja
> escrito em janeiro que eu avisei."*
:::
