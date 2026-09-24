---
title: "O que vamos construir"
number: 2
slug: o-que-vamos-construir
part: p1
kicker: "Onze caixas num slide, setenta e quatro mil reais, e ninguém na sala capaz de dizer o que a célula 14 faz."
epigraph: "Existem duas formas de construir um projeto de software. Uma é fazê-lo tão simples que, obviamente, não há deficiências. A outra é fazê-lo tão complicado que não há deficiências óbvias."
epigraph_by: "C. A. R. Hoare"
goal: >-
  Entender o que a Bem-Te-Vi está comprando quando pede "um sistema", separar
  planilha de regra de preço, e terminar com o Python instalado e conferido.
---

:::story Sabiá Data Platform
O slide tinha onze caixas ligadas por setas e, no meio, uma caixa maior,
escrita **IA**.

— É simples — disse o Sérgio. — A gente plataforma o dado, expõe a API e
plugga inteligência no preço.

Ele tinha vendido o projeto ao conselho da cooperativa em quarenta minutos
usando essas três palavras, o que é um talento de verdade.

A Bia levantou a mão.

— O que o notebook calcula hoje?

Houve um silêncio de três segundos, que numa reunião de nove pessoas dá
tempo de alguém mexer na caneta de propósito.

— Ele... processa — disse o Elias.

— Processa o quê?

O Elias tinha oito anos de Leme e já havia aprendido que resposta precisa
vira tarefa com o seu nome. Olhou para a Helena.

— O Cacá sabe.

— O Cacá mudou de estado.

— Ele responde WhatsApp.

— E a gente entrega quando?

A Helena respondeu sem consultar nada, porque administrava datas do jeito
que um bombeiro administra fósforo.

— A Bem-Te-Vi renova em 15 de abril.

— E se passar de 15 de abril?

— Eles compram da cooperativa de baixo. Um milhão e duzentos no ano.

A reunião durou mais cinquenta minutos e produziu três decisões de
arquitetura sobre um notebook que ninguém presente conseguia executar.
:::

Naquela mesma tarde, a Bia foi ao galpão ver o que a Leme tinha acabado de
se comprometer a substituir.

:::story A célula 14
— Você é a do computador? — perguntou a Dona Neuza, sem tirar o olho da
balança.

— Sou.

— Então não roda a 14.

O notebook estava aberto na célula com um comentário em vermelho, de 2021:
`# NÃO RODAR — Cacá`.

— O que ela faz?

— Dobra o tomate. Descobri em março, porque o Seu Onofre achou graça do
preço. Desde então eu pulo.

— E o resto?

Ela apontou a planilha com o queixo. Trinta e uma abas. Duas com o mesmo
nome, uma com `_OK` no final.

— Quando a menina do escritório e eu abrimos ao mesmo tempo, uma das duas
perde a manhã, e a gente só descobre na hora de carregar o caminhão. Quando
o produto vem de fora do estado, a margem é outra, e isso está na cabeça,
não na célula. Quando alguém busca açafrão sem o acento, não acha. E o de
sempre: o número do notebook e o número da planilha não fecham.

— Quanto não fecha?

— Três reais e quarenta. Em doze mil. Todo mês.

— Há quanto tempo?

— O do tomate, desde março. Os três e quarenta eu já nem lembro.

— E ninguém arrumou?

A Dona Neuza colou a etiqueta na caixa, alisou com o polegar e puxou a
seguinte.

— Todo ano vem um moço e diz que vai arrumar. Você é a terceira. O Cacá foi
o primeiro, e ele ainda deve um sábado.
:::

## A pergunta que trava o projeto

A reunião da manhã não foi um caso de incompetência. Aconteceu o que
acontece em empresa de qualquer tamanho: o sistema é um arquivo antigo,
quem escreveu foi embora, e a cobrança por um cronograma chega antes do
entendimento.

O resultado é sempre o mesmo — decisões tomadas em cima de uma caixa
escrita **IA**.

Repare em quem, das nove pessoas da reunião, conseguiu descrever o
comportamento do sistema: ninguém. E repare em quanto tempo a Dona Neuza
levou para descrever o dela: menos de um minuto, sem parar de etiquetar,
com quatro defeitos e uma frequência para cada um.

:::note Na sua carreira
"O que esse sistema faz hoje?" é a pergunta mais barata e mais impopular de
qualquer projeto que começa com a palavra plataforma.

Quando for você a perguntar, peça um **exemplo**, não uma definição: *"me
mostra uma coisa que acontece de manhã, do começo ao fim"*. Definição todo
mundo improvisa. Exemplo, não.

E anote a resposta na frente de quem respondeu. Uma descrição que não foi
escrita na hora vira, duas semanas depois, duas descrições diferentes — em
geral na véspera de uma sprint.
:::

## Três pessoas querendo o mesmo preço

Antes de decidir qualquer ferramenta, vale entender o que a cooperativa
precisa no lugar da pasta.

Hoje o preço mora em dois lugares que não conversam: a planilha e o
notebook. Quem não está de pé na frente da Dona Neuza não consulta nada. O
comprador da Bem-Te-Vi liga. O Seu Onofre manda um áudio perguntando quanto
ficou a caixa de alface. Alguém abre a aba errada.

O que o contrato de R$ 74 mil precisa entregar, no fundo, são três usos do
mesmo número:

| Quem | O que precisa |
|---|---|
| a Dona Neuza, na balança | registrar o que chegou, ver o preço, baixar a caixa |
| o comprador da Bem-Te-Vi | consultar estoque e preço sem ligar para o galpão |
| o Seu Onofre, no telefone | ver só o que é dele, e quanto a cooperativa ficou devendo |

Tabela: Três perguntas diferentes, um preço só.

São três programas distintos, possivelmente escritos por pessoas distintas.
Se cada um calcular a margem do seu jeito, "orgânico acumula com agricultura
familiar?" vai existir em três versões — e elas vão divergir em três
velocidades diferentes. A de março, a do tomate dobrado, já é uma amostra.

A saída é ter **um** programa que sabe as regras, e combinar um jeito de os
outros pedirem as coisas a ele.

Esse jeito combinado tem nome.

:::term API
*Application Programming Interface*, interface de programação. É um contrato
entre dois programas: um sabe fazer alguma coisa, o outro precisa que ela
seja feita, e existe uma forma acordada de pedir e de responder.
:::

A Dona Neuza é uma API há trinta e um anos e ninguém nunca a chamou assim.
O Seu Onofre chega no galpão, diz o produto e mostra a nota. Ela responde
com o preço, ou com "acabou, volta quinta". Ele não precisa saber em qual
aba está o número, nem qual célula não pode rodar. Precisa saber **o que
pedir** e **em que formato ela responde**.

É isso que vamos escrever. A diferença é que o pedido vai chegar pela rede,
e a resposta vai sair em texto que outro programa consegue ler.

## Como um programa pede uma coisa a outro

Quando o sistema da Bem-Te-Vi quiser o preço do tomate, ele manda pela rede
um bloco de texto parecido com este:

```text
GET /produtos/12
Accept: application/json
```

A primeira linha diz **o que fazer** (`GET`, que significa "me dê") e
**onde** (`/produtos/12`, o produto número 12). A segunda diz em que formato
a resposta é bem-vinda.

Para cadastrar um produto novo, o bloco muda de verbo e ganha um corpo,
depois de uma linha em branco:

```text
POST /produtos
Content-Type: application/json

{"nome": "Tomate italiano", "preco": "8.90"}
```

O `POST` é um dos verbos que cobrem quase tudo que a cooperativa faz hoje
na planilha, sem chamar nada disso de verbo:

| Verbo | Significa | No galpão |
|---|---|---|
| `GET` | me dê | "quanto está o tomate?" |
| `POST` | crie um novo | entra produto que a cooperativa ainda não tinha |
| `PUT` | substitua | o preço mudou por inteiro |
| `PATCH` | altere um pedaço | só o estoque, o resto fica |
| `DELETE` | tire | saiu do catálogo |

Tabela: Cinco verbos cobrem o que a planilha faz com trinta e uma abas.

Repare no endereço: `/produtos`, e não `/criarProduto`. O verbo já está do
lado de fora, na primeira palavra. Quem coloca o verbo dentro do endereço
termina com `/criarProduto`, `/atualizarProduto` e `/apagarProduto` — três
endereços para uma coisa só, e nenhum jeito de combinar "tomate" com "abaixo
de dez reais".

A resposta volta com um número de três dígitos na frente. `200` é "aí
está". `201` é "criei". `404` é "não tenho esse". `422` é "entendi o pedido
e recusei, olha o que está errado". `500` é "quembrou aqui dentro". Errar
esse número é mentir para o programa que confiou em você: ele toma uma
decisão em cima do que você disse que aconteceu.

## O que a planilha já é, sem ser

As quatro operações que a Dona Neuza faz todo dia têm iniciais que viraram
palavra: criar, ler, atualizar, apagar. **CRUD**. Não é uma arquitetura. É
o nome do trabalho mais comum de quem guarda dado de outra pessoa.

Fazer as quatro coisas é pouco. O notebook já faz as quatro, e mesmo assim
dobra o tomate e perde três reais e quarenta. O trabalho é fazê-las sem
duas pessoas gravarem em cima uma da outra, sem margem calculada diferente
em cada aba, e sem uma célula que só a Dona Neuza sabe pular.

## Instalando

Baixe o Python em <https://python.org>. No Windows, marque **Add python.exe
to PATH** na primeira tela. No macOS e no Linux quase sempre já existe um
Python instalado, e ele pode ser o 3.6 de alguém: confira antes de confiar.

Abra o terminal e digite:

```text
$ python --version
Python 3.12.4
```

Se aparecer `3.12` ou mais alto, está pronto. Se o comando não for
encontrado, tente `python3`. Em macOS e Linux esse é o nome usual.

:::warning A loja do Windows
Se você instalar o Python pela Microsoft Store, algumas versões deixam um
`python.exe` falso no caminho, que abre a loja em vez de rodar o programa.
Baixe do site oficial e marque a caixa do PATH.
:::

:::pitfall
`python` e `python3` podem ser programas diferentes na mesma máquina, com
versões diferentes. O galpão vive disso: um terminal responde 3.6, outro
responde 3.12, e os dois se chamam Python.

Descubra qual é o seu agora e use sempre o mesmo. Metade dos "mas eu
instalei essa biblioteca" da vida real é esta confusão, e a outra metade é
instalar no Python do sistema inteiro — assunto para o dia em que houver
uma biblioteca para instalar.
:::

:::practice
Rode `python --version` e, em seguida, `python` sem nome de arquivo. O
próprio interpretador abre e espera com `>>>`. Digite `2 + 2` e depois
`exit()`. Se a resposta foi `4`, a ferramenta que o resto do trabalho usa
está na mesa.

Não instale biblioteca nenhuma ainda. Não há o que instalar: ainda não
existe um programa.
:::

:::summary
- O sistema de hoje é um notebook mais uma planilha, e os dois discordam.
- Uma API é um contrato: o que se pede, onde, e em que formato volta a
  resposta.
- O verbo fica fora do endereço. O endereço nomeia a coisa.
- O número de três dígitos é a primeira frase da resposta.
- O Python da máquina se confere com `python --version` antes de confiar
  nele.
:::

:::milestone
Você tem o Python instalado e conferido, e sabe o que a Bem-Te-Vi vai
perguntar em 15 de abril. Ainda não há programa. É daqui que este começa.
:::

:::exercise level=1
O Seu Onofre manda um áudio: "Neuza, sobrou alface e quanto está a caixa?"
Escreva, em duas linhas, o que ele pediu e o que ela responderia — e marque
o que ele **não** precisou saber para receber a resposta.

:::answer
Ele pediu existência e preço de um produto. Ela responde com um número, ou
com "acabou".

Ele não precisou saber em qual aba está o preço, qual célula não pode
rodar, nem se o número saiu do notebook ou da planilha. Isso é o contrato.
O endereço e o verbo, quando existirem, são só essa conversa escrita num
formato que um programa consegue repetir.
:::

:::exercise level=2
Sem olhar a tabela, escreva o verbo e o endereço de cada operação: cadastrar
um produto, listar os produtos, ver um, trocar o preço, tirar do catálogo.

:::answer
```text
POST   /produtos       cadastra
GET    /produtos       lista
GET    /produtos/12    vê um
PUT    /produtos/12    troca
DELETE /produtos/12    tira
```
Os dois `GET` são o ponto: o mesmo verbo, num endereço e noutro, significa
coisas diferentes. O verbo diz a intenção. O endereço diz a coisa.
:::

:::exercise level=3
O Sérgio pediu um endereço `/produtos/baratos`, que devolva o que custa
menos de dez reais. Você aceitaria? Justifique em três linhas.

:::answer
Não. `baratos` não é um produto — é um filtro sobre os produtos. No dia em
que aparecerem `/produtos/caros`, `/produtos/em-falta` e
`/produtos/organicos`, serão quatro endereços que não se combinam: não há
como pedir "barato e orgânico".

A forma que combina é `GET /produtos?preco_max=10`. O endereço diz *o que*.
O que vem depois do `?` diz *quais*.
:::
