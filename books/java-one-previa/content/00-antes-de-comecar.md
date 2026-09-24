---
title: "Antes de começar"
matter: front
numbered: false
kicker: "Um livro curto sobre uma linguagem que costuma ser ensinada longa demais."
---

Existem duas maneiras de ensinar Java. A primeira apresenta a linguagem
inteira — trinta anos de recursos, quatro tipos de laço, oito modificadores,
a hierarquia de coleções em um diagrama do tamanho de uma parede — e promete
que um dia aquilo vira um programa. A segunda escolhe um programa e ensina
só o Java que ele exige, quando ele exige.

Este livro é do segundo tipo. Ele tem um projeto: uma API REST de catálogo
de produtos, com banco de dados, validação, autenticação, testes e
documentação. Você vai construí-la. Cada conceito da linguagem aparece no
capítulo em que o projeto precisa dele, e não antes.

:::key
O livro não é uma referência de Java. É um caminho até uma API funcionando.
Se você quiser a referência completa depois, ela cabe em um site; o caminho
é que é difícil de achar.
:::

## Como este livro funciona

O projeto cresce em linha reta. No capítulo 2 você imprime uma linha no
terminal; no capítulo 17 responde uma requisição HTTP; no 23 tem um CRUD
completo; no 32 protege esse CRUD com um token; no 42 sobe tudo em um
contêiner. Cada capítulo encerra com o estado do projeto naquele ponto:

:::milestone
Você tem: nada ainda. Um terminal aberto, um JDK instalado e uma pasta
vazia. É exatamente daqui que todo software começa.
:::

O caminho não é limpo de propósito. Você vai escrever código que quebra,
ler a mensagem de erro inteira e consertar. É assim que se aprende a
programar de verdade — e é a parte que os tutoriais editam fora.

## O que você precisa

Um JDK 21 ou mais novo, um editor de texto e um terminal. Um banco
PostgreSQL aparece na Parte 4, e o capítulo 19 explica como subir um em dois
minutos. Nada mais.

```bash title="Confirme que está tudo no lugar"
java -version
javac -version
```

Se os dois responderem com um número de versão, você está pronto.

:::pitfall
`java -version` respondendo e `javac -version` não respondendo é o sintoma
clássico de ter instalado um JRE em vez de um JDK. O JRE só executa; o JDK
compila. Você precisa do segundo.
:::

## O elenco

Entre uma explicação e outra, você vai encontrar cenas de uma empresa. Ela se
chama Aurora Comércio, vende de tudo pela internet e acabou de decidir que
precisa de uma API — de preferência para ontem.

As cenas não são enfeite: elas existem porque conceito abstrato gruda melhor
quando vem colado a uma situação que você reconhece. Quando o livro explicar
`NullPointerException`, você vai lembrar do Seu Antônio.

:::story Os cinco que você vai encontrar
**Carlos** entrou há três semanas. Sabe lógica, não sabe Java, e foi
escalado para "aquele projetinho da API". Ele é você.

**Marina** é a desenvolvedora sênior. Já viu esse filme, sabe como termina e
mesmo assim insiste em revisar cada *pull request* linha por linha.

**Roberto** é o gerente. Não escreve código, escreve prazos. Para ele,
qualquer pedido cabe na frase "é só uma alteraçãozinha".

**Cláudia** cuida do produto. Traz requisitos novos com a naturalidade de
quem traz café — inclusive na véspera da entrega.

**Seu Antônio**, 68 anos, é o primeiro cliente da loja. Ele encontra, em dois
minutos de uso, bugs que a equipe não reproduz em duas semanas.
:::

:::art caption="O time da Aurora Comércio no primeiro dia do projeto." src="o-time-da-aurora-comercio-no-primeiro-dia-do-projeto.jpg"
Ilustração editorial minimalista em traço limpo: cinco personagens de corpo
inteiro lado a lado, como um retrato de elenco, sobre fundo branco. Carlos,
jovem desenvolvedor segurando um notebook novo demais e uma expressão de
otimismo ingênuo. Marina, desenvolvedora sênior de braços cruzados, caneca
de café, olhar de quem já sabe o que vem. Roberto, gerente de camisa social,
apontando para um cronograma impresso onde se lê apenas "3 SEMANAS".
Cláudia, product owner com um caderno cheio de post-its coloridos
transbordando. Seu Antônio, senhor de 68 anos com óculos na ponta do nariz,
segurando um celular na horizontal e apertando a tela com o dedo indicador.
Humor sutil, poucos elementos, sem cenário elaborado, estética de revista de
tecnologia, personagens expressivos, sem estética infantil.
:::

## Convenções

Trechos como `System.out.println` aparecem na fonte de código quando citados
no meio da frase. Blocos maiores vêm com o nome do arquivo no alto — em Java
esse nome importa mais do que em quase qualquer outra linguagem, e o
capítulo 2 explica por quê.

Cinco marcas aparecem nas margens do texto e vale reconhecê-las de antemão:

:::trivia
**Você sabia** traz a curiosidade, a história, a decisão de projeto que
ficou. Pode ser saltada sem prejuízo — mas é o que faz você contar a
história em uma mesa de bar.
:::

:::pitfall
**Erro comum** mostra a armadilha antes de você cair nela. Quase sempre é
um erro que eu cometi.
:::

:::history
**Nos bastidores** conta por que a linguagem é assim. Java tem muitas
decisões estranhas, e quase todas têm um motivo datado.
:::

:::checkpoint
**Ponto de controle** fecha o capítulo listando o que você já sabe fazer —
não o que leu, o que *sabe fazer*.
:::

E **O projeto agora** é o marco do capítulo: uma frase sobre onde a API
está. Se você abrir o livro no meio, é a primeira coisa que deve procurar.
