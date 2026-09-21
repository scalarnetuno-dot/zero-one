---
title: "Antes de começar"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Um livro técnico escrito por alguém que já perdeu uma sexta-feira por causa de um ponto e vírgula."
---

Existe uma piada recorrente sobre PHP que já dura vinte anos, e ela tem um
fundo verdadeiro: a linguagem cresceu rápido, cresceu torta e carregou por
muito tempo decisões que não envelheceram bem. Quem aprendeu PHP em 2009
aprendeu a escrever coisas que hoje seriam recusadas em qualquer revisão de
código.

O que quase ninguém conta é o resto da história. O PHP 8 é uma linguagem
tipada, rápida e previsível, com enums, `readonly`, `match` e um sistema de
pacotes que funciona. E continua atendendo uma parte enorme da web —
inclusive a parte que paga salário.

Este livro é sobre o PHP de agora, escrito por quem conhece o de antes.

## A Casa Amarela

O projeto começa pequeno: uma biblioteca de bairro, quatro mil títulos e um
sistema antigo que ainda atende o balcão. Vera conhece as regras de
empréstimo; Tainá está aprendendo a programar; Dedé herdou o problema; Seu
Juvenal quer uma tela nova para ontem. O código também participa da história:
há um `funcoes2_NOVO_final.php`, senhas antigas e decisões que sobreviveram
porque, apesar de tudo, o sistema funcionava.

Você vai transformar esse cenário numa aplicação de verdade. Primeiro, um
programa pequeno que roda. Depois, dados que têm nome e tipo, regras que
podem ser testadas, uma API, banco de dados, autenticação e deploy. Cada
mudança nasce de uma necessidade do acervo, não de uma lista de recursos da
linguagem.

O PHP moderno aparece com seus acertos e suas cicatrizes. Quando uma
decisão histórica causar um defeito, o código vai mostrar o defeito. Quando
uma solução simples bastar, ela vence a arquitetura de palco.

:::key
Leia com um terminal aberto. Execute os exemplos, altere os valores e tente
quebrá-los. A memória de uma linguagem nasce mais depressa de uma saída
inesperada do que de uma definição decorada.
:::

## O elenco

Vera é a especialista do domínio, embora nunca tenha recebido esse título.
Tainá faz as perguntas que desmontam uma explicação apressada. Dedé traduz
problemas em código e aprende a não esconder decisões atrás de abstrações.
Seu Juvenal fornece prazos, requisitos e a frase "é só uma alteraçãozinha".

O Sistema não é um vilão. Ele tem quinze anos de serviço e os defeitos de
quem foi crescendo sem projeto. Modernizá-lo aos poucos será mais honesto do
que fingir que uma equipe consegue apagar a vida real com um botão de
reescrever.

## Como trabalhar

O código pressupõe os passos anteriores, mas a regra mais importante é
parar para testar. Os exercícios pedem pequenas decisões: escolher um tipo,
explicar uma comparação, prever uma saída, corrigir um defeito. Faça-os sem
consultar a resposta imediatamente. Um programa que você consegue prever é
mais valioso que um programa que apenas consegue copiar.

## O ambiente

Três coisas, todas gratuitas:

| O quê | Versão | Para quê |
|---|---|---|
| PHP | 8.3 ou mais novo | a linguagem |
| Composer | 2.x | dependências, a partir do capítulo 10 |
| Um editor | qualquer um | VS Code, PhpStorm, Vim |

Tabela: MySQL ou PostgreSQL só aparecem na metade do livro. Não instale
agora.

A instalação passo a passo está no capítulo @cap:o-que-vamos-construir,
junto do teste que confirma que deu certo.

:::warning Cuidado com a versão do sistema
Em várias distribuições Linux, `apt install php` instala uma versão antiga —
7.4 ainda aparece por aí. E no macOS, o PHP que vinha de fábrica foi
removido. Confira com `php -v` antes de acreditar que está instalado, e
prefira os repositórios oficiais: `ondrej/php` no Ubuntu, Homebrew no macOS.
:::

## Convenções

Código aparece assim, às vezes com o nome do arquivo:

```php title="exemplo.php"
$multa = 720;
echo 'R$ ' . number_format($multa / 100, 2, ',', '.');
```

O que o terminal responde aparece sem nome de arquivo e sem realce:

```text
R$ 7,20
```

E quando o programa quebra — o que vai acontecer muito, de propósito — o
erro vem inteiro, do começo ao fim, porque as linhas do meio são as que
importam.

:::key
Comando de terminal aparece com `$` na frente. O `$` representa o prompt e
não faz parte do comando. Em PHP isso confunde mais do que em outras
linguagens, porque `$` também começa toda variável — dentro de um bloco PHP,
ele é código; na primeira coluna de um bloco de terminal, é o prompt.
:::
