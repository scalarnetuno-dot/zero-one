---
title: "Antes de começar"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Quinze anos no ar, meio milhão de empréstimos e um arquivo chamado funcoes2_NOVO_final.php."
---

Esta é a pasta que atende o balcão de uma biblioteca de bairro:

```text
backup_16-03-2019.sql
config.php
conexao.php
emprestimo.php
funcoes.php
funcoes2.php
funcoes2_NOVO.php
funcoes2_NOVO_final.php
index.php
login.php
relatorio.php
relatorio_novo_OK.php
teste.php
```

São quatorze mil linhas de PHP escritas em 2009 e remendadas desde então por
quem estava disponível na hora. O backup mais recente é de 2019 e mora na
mesma pasta do site, o que significa que qualquer pessoa com o endereço
certo baixa o acervo inteiro.

E funciona.

Quinze anos no ar, meio milhão de empréstimos registrados, nenhum livro
perdido por culpa do software. A Vera abre o sistema às nove, empresta,
devolve, cobra multa e fecha às seis. Nesses quinze anos ele saiu do ar duas
vezes, as duas por causa da hospedagem.

Você vai substituir esse sistema. Não porque ele é ruim — porque ele não tem
mais para onde crescer. E o PHP que entra no lugar mal se parece com o que
escreveu essa pasta: este é o PHP de agora, ensinado por quem conhece o de
antes.

## A biblioteca, a empresa e a data

A **Biblioteca Comunitária Casa Amarela** tem quatro mil títulos e oito mil
exemplares. A **Vertexo Sistemas** — cento e oitenta pessoas, especialista em
transformação digital para clientes que não conseguem descrever o que têm
hoje — assinou o contrato para trocar o Sistema. Quem vai fazer o trabalho
é você.

E existe uma data que ninguém pode empurrar.

Nada disso é cenário. Prazo que não se move, orçamento que encolhe,
requisito que chega no pior momento e um sistema legado que precisa
continuar atendendo o balcão enquanto o substituto é construído — é isso que
transforma escolha técnica em decisão. Optar entre duas formas de escrever a
mesma coisa só fica interessante quando uma delas custa uma terça-feira.

## Quem aparece

**Dedé** tem sete anos de carreira, três deles na Vertexo, e é a voz que
explica o porquê. Está há oito meses ouvindo que a promoção sai no próximo
ciclo.

**Tainá** é estagiária, terceiro período. Faz as perguntas que desmontam uma
explicação apressada — não por ingenuidade, mas porque é a única pessoa da
sala que não perde nada ao dizer que não entendeu. Anota tudo num caderno.

**Vera** é bibliotecária da Casa Amarela há trinta e um anos. Sabe de cor
todas as regras de empréstimo e nunca escreveu nenhuma.

**Márcia** administra o prazo. O trabalho real dela é receber uma data
impossível de cima e reemiti-la para baixo em forma de sprint.

**Dr. Aurélio** é diretor de tecnologia. Nunca escreveu código e não finge
que escreveu.

**Seu Juvenal** preside a associação de moradores. Traz o requisito novo
sempre no pior momento, sempre embrulhado em "é só uma alteraçãozinha", e
sempre com razão sobre a necessidade.

E o **Sistema**, com maiúscula, é aquela pasta do começo. Ele não é o vilão.
Cada coisa moderna que aparecer aqui vai ser medida contra ele — e em
algumas dessas medições o Sistema ganha.

## Como o livro mostra as coisas

Código aparece assim, às vezes com o nome do arquivo:

```php title="multa.php"
$multa_em_centavos = 720;
echo 'R$ ' . number_format($multa_em_centavos / 100, 2, ',', '.');
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
não faz parte do comando: não digite. Em PHP isso confunde mais do que em
outras linguagens, porque `$` também começa toda variável — dentro de um
bloco de código PHP ele é código; na primeira coluna de um bloco de
terminal, é o prompt.
:::

Você não precisa instalar nada para começar a ler. Quando o primeiro
programa precisar rodar, a instalação vem junto, com o teste que confirma
que deu certo.

:::practice
Leia com um terminal aberto. Execute os exemplos, altere os valores e tente
quebrá-los. A memória de uma linguagem nasce mais depressa de uma saída
inesperada do que de uma definição decorada.
:::

A data que ninguém pode empurrar é 31 de março. Até lá, a Vera abre às nove
e o Sistema atende.
