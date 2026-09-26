---
title: "27 de novembro"
number: 25
slug: 27-de-novembro
part: p6
kicker: "Às 10h14 a SEFAZ caiu de novo. Desta vez, a única pessoa que percebeu foi a que estava olhando o painel."
goal: >-
  Montar o runbook da Black Friday — quem olha o quê, qual alerta pede qual
  ação, e o que não se faz no dia —, e acompanhar, hora a hora, cada peça
  do livro funcionando sob pressão, incluindo as que falharam.
---

:::story 6h40
A Júlia chegou à fábrica às 6h40. O Kaique já estava lá, com dois
cafés e o notebook aberto no painel.

— Tudo zerado — disse ele. — Nenhuma fila com mensagem, nenhuma na
`.error`. Os consumidores estão todos lá: seis no fiscal, quatro no
estoque, dois nos avisos, dois na expedição.

— A nova impressora?

— A Denise ligou às seis. Imprimiu vinte etiquetas de teste. A Zebrinha
imprimiu vinte também, e a Denise disse que a Zebrinha imprimiu mais
bonito.

O Rafa chegou às sete, de camiseta da campanha. Olhou para a tela.

— É isso? Uma tela com números zerados?

— É isso — disse Júlia. — Se tudo der certo, é isso o dia inteiro.

— E se der errado?

Ela apontou para uma folha impressa, colada com fita na parede, ao lado
do prego da Dona Cida.

— Aí a gente faz o que está escrito ali.
:::

## O runbook

Um **runbook** é o documento que diz o que fazer quando um alerta
dispara, escrito com calma, antes, por quem sabe — para ser seguido com
pressa, durante, por quem estiver de plantão. A folha na parede da
cozinha tinha uma tabela, e cada linha dela é um capítulo deste livro:

| Alerta | O que quer dizer | Ação |
|---|---|---|
| fila sem consumidor | um worker caiu e não voltou | ver o log do contêiner; `docker compose up -d` do serviço |
| espera do fiscal > 1h | a SEFAZ caiu por mais tempo que o retry cobre | nada no sistema; avisar o Seu Norberto |
| mensagem na `.error` do fiscal | nota que esgotou as tentativas | agrupar por motivo; corrigir a causa; reprocessar limpo |
| mensagem na `.error` de qualquer fila | pedido parado com motivo escrito | a mesma leitura por motivo |
| outbox com pendentes há > 5 min | o despachante não publica | ver o log do despachante; o broker está de pé? |
| espera da expedição > 4h | as impressoras não dão conta | avisar a Denise; é o plano B, não um incidente |

Tabela: Cada ação cabe numa linha porque cada decisão já foi tomada nos
capítulos anteriores.

E uma segunda lista, mais curta, do que **não** se faz no dia:

- nenhum deploy, de nada, entre 8h e 22h;
- nenhuma mudança de `delay`, prefetch ou tipo de fila;
- nenhuma mensagem apagada da `.error` sem que alguém leia o motivo;
- nenhum `requeue` manual de mensagem que falhou.

## 10h00

A collab da Tia Bia entrou no ar às 10h em ponto. O painel do Grafana
mostrava a linha de publicações da outbox subindo em escada.

| Hora | Pedidos na hora | Pico de publicação |
|---|---|---|
| 10h–11h | 3.870 | 2,1 por segundo |
| 11h–12h | 7.420 | 3,9 por segundo |
| 12h–13h | 5.110 | 2,6 por segundo |

Tabela: O pico de 7.420 pedidos por hora ficou abaixo da projeção de dez
mil, e acima de tudo o que a loja já tinha vendido numa hora.

O checkout respondia em menos de meio segundo. Ele não sabia de SEFAZ,
de ERP, de transportadora nem de impressora: gravava o pedido e a outbox,
na mesma transação, e respondia.

## 10h14

O alerta que chegou primeiro não foi de erro: foi de **espera**. A fila
`fiscal.pedidos-pagos.retry` começou a crescer, e a espera do fiscal
passou de dois segundos para dois minutos.

A SEFAZ tinha caído. Como em 2025.

O Kaique abriu o runbook, achou a linha, e leu em voz alta:

— Espera do fiscal acima de uma hora: avisar o Seu Norberto. — Olhou o
painel. — Está em dois minutos.

— Então não faz nada — disse Júlia.

Nas duas horas seguintes, o painel mostrou exatamente o que o capítulo
@cap:retry-com-ttl-e-dead-letter tinha desenhado: as notas iam para a
`.retry`, esperavam cinco minutos, voltavam, falhavam, voltavam de novo.
O worker do fiscal passava a maior parte do tempo livre. Nenhuma nota foi
para a fila de erro, porque a janela de retry — cinco minutos vezes treze
— era maior que a queda.

A SEFAZ voltou às 10h51. Em onze minutos, a fila fiscal esvaziou. Os
clientes receberam o e-mail de confirmação às 10h04, 10h15, 10h32 — na
hora da compra —, e a nota fiscal no fim da manhã. Nenhum deles
reclamou, porque nenhum deles percebeu.

## 11h07

O Kaique atendeu o WhatsApp do SAC.

— É o senhor do 40117 — disse ele, sem tirar o fone. — Ele comprou de novo.
E diz que apertou o botão três vezes, "por via das dúvidas".

A Júlia abriu o painel da outbox. Uma linha, `pedido-19203-pago`. Os três
cliques tinham chegado com o mesmo carrinho: o primeiro criou o pedido; o
segundo e o terceiro encontraram o índice único e receberam o mesmo
pedido de volta, sem gravar evento nenhum.

Às 11h09, o despachante publicou o evento duas vezes — a conexão caiu
entre publicar e marcar a linha como publicada. Na tabela `notas` do
fiscal, o pedido tinha uma linha, `emitida`: a segunda cópia encontrou a
reserva e não fez nada. Na fila da expedição, uma etiqueta. No gateway,
uma cobrança.

— Uma geleia — disse o Kaique, no WhatsApp. — Pode ficar tranquilo.

## 11h40

A impressora nova travou. Papel embolado, luz vermelha piscando. A Denise
tirou o rolo, olhou, e decidiu não mexer mais nela no dia.

No painel, a fila `expedicao.pedidos-pagos` começou a crescer. Com a
Zebrinha sozinha, a expedição imprimia duas mil etiquetas por hora, e
chegavam sete mil. A espera passou de uma hora às 12h20, de três às 14h.

Ninguém fez nada, porque era o plano. O consumidor da impressora nova
estava ligado a ela: com a impressora parada, o `handle()` falhava, as
mensagens iam para o retry — e, com prefetch 1, a Zebrinha pegava todas
as outras. O alerta de espera da expedição estava em quatro horas.

A Denise imprimiu até as 21h50. A transportadora, que coletava às 18h,
tinha sido avisada às 12h, pelo contrato de mensagens: o `coleta.agendada`
dos pedidos da tarde saiu com a data do dia seguinte.

## 14h22

O alerta de fila de erro disparou pela primeira vez no dia. Três
mensagens em `avisos.pedidos.error`.

A Júlia abriu os headers. `x-mirabel-failure-reason = poison`. Três
mensagens de texto puro, publicadas no exchange `doce.eventos` com a
routing key `pedido.promocao`.

— Isso não é nosso — disse ela.

Não era. Era o sistema de e-mail marketing da agência, que tinha sido
configurado, em outubro, para publicar direto no RabbitMQ da loja, "para
facilitar". Mandava texto em vez de JSON. A fila de avisos, ligada por
`pedido.*`, recebia.

As três mensagens foram lidas, anotadas e apagadas. O binding dos avisos
virou `pedido.pago` e `pedido.cancelado`, em vez do curinga. O e-mail para
a agência saiu às 14h40.

## 22h00

Às dez da noite, o painel voltou a mostrar o que mostrava às seis e
quarenta: tudo zerado. O Seu Norberto mandou uma mensagem no grupo:

*16.400 pedidos, 16.400 notas. Nenhum estorno.*

O Rafa respondeu com um print do faturamento. A Denise não respondeu: ela
tinha ido para casa às dez e dez, e a Zebrinha estava desligada pela
primeira vez em dezesseis horas.

:::story A última etiqueta
A Júlia desligou o notebook às 22h30. O Kaique estava arrumando a mesa, e
jogou fora os copos de café. Deixou o maço de etiquetas usadas, com as
anotações dele no verso, em cima do teclado dela.

— O que é isso?

— O que eu aprendi. Desde setembro.

Ela folheou. *fila = ?*. *fila = lugar que não esquece*. *pelo menos uma
vez ≠ uma vez*. *dinheiro não é número*. *só coloca um Kafka → só coloca
três RabbitMQ?*

A última etiqueta estava em branco.

— Essa é de hoje — disse o Kaique. — Ainda não sei o que escrever.

— Escreve o que aconteceu.

Ele pensou, e escreveu devagar, com a caneta da expedição:

*Nada.*
:::

:::milestone
Você tem: o sistema inteiro rodando na data que ninguém podia empurrar —
checkout com outbox, filas com retry e erro, consumidores idempotentes,
workers supervisionados, filas replicadas, métricas, alertas, um
consumidor em Java — e um runbook que transformou cada falha do dia numa
linha já escrita.
:::

:::summary
- Um runbook liga cada alerta a uma ação decidida antes; no dia, ninguém
	decide sob pressão o que podia ter sido decidido com calma.
- A queda da SEFAZ virou espera na fila `.retry`, não erro: a janela de
	retry era maior que a queda.
- O clique repetido do cliente virou uma nota e uma cobrança, pela chave
	de idempotência e pela reserva no banco.
- A impressora quebrada virou uma fila que acumula dentro do previsto, com
	o alerta calibrado para o plano, e não para o susto.
- A mensagem envenenada de um sistema de fora foi parar na fila de erro, e
	o curinga do binding foi trocado por chaves explícitas.
:::

:::exercise level=1
Às 11h40, com a impressora nova travada, o consumidor ligado a ela seguiu
consumindo e mandando mensagens para o retry. Que risco isso cria, e o
que teria sido mais simples?

:::answer
Cada etiqueta que caía no consumidor da impressora parada gastava uma
tentativa e cinco minutos de retry; se a impressora ficasse parada tempo
demais, as etiquetas esgotariam as tentativas e iriam para a fila de
erro, mesmo com a Zebrinha livre para imprimi-las.

Mais simples era **parar** o consumidor da impressora nova —
`docker compose stop` do serviço dela —, deixando a Zebrinha sozinha na
fila. Um consumidor ligado a um recurso que está fora não deve ficar
pegando trabalho só para devolver. É uma linha que faltou no runbook, e o
tipo de coisa que se descobre no dia e se escreve no dia seguinte.
:::

:::exercise level=2
Escreva a linha do runbook para o alerta "outbox com pendentes há mais de
5 minutos", com o diagnóstico em três passos e a ação para cada resultado.

:::answer
| Passo | Pergunta | Se sim | Se não |
|---|---|---|---|
| 1 | o despachante está no ar? (`docker compose ps`) | vá ao passo 2 | subir o serviço; conferir o log de por que caiu |
| 2 | o `ultimo_erro` da outbox fala de conexão? | o broker está fora: é a queda do capítulo sobre outbox; o checkout segue vendendo, esperar e acompanhar | vá ao passo 3 |
| 3 | o erro é `PublishNotConfirmedException`? | o broker está recusando: fila no limite ou sem disco; ver o Overview e os alarmes de memória e disco | ler o erro e escalar para quem mantém o despachante |

O que o runbook deixa claro, e que evita a decisão errada sob pressão: em
nenhum dos casos o checkout precisa sair do ar, e em nenhum deles alguém
deve apagar linhas da outbox.
:::
