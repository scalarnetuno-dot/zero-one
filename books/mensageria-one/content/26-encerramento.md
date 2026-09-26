---
title: "Encerramento"
slug: encerramento
matter: back
numbered: false
kicker: "Uma linha apagada, um prego que ficou na parede, e uma pergunta sobre ameixas que ninguém soube responder."
---

:::story A linha 1
Na segunda-feira depois da Black Friday, a Júlia abriu o
`CheckoutController.php` do Marcelão pela última vez. Não havia mais
nada dele ali: a cobrança tinha sido reescrita, as sete chamadas tinham
virado um `createOrFirst`, uma transação e uma linha na outbox.

Só a primeira linha continuava igual:
`// NAO MEXER - BLACK FRIDAY 2023 - MARCELO`.

Ela apagou a linha, fez o commit e escreveu na mensagem: *mexemos*.

O Kaique viu a notificação do repositório no celular e riu sozinho.

À tarde, o Marcelão mandou um e-mail. Tinha visto, "por acaso", que a
loja tinha vendido dezesseis mil pedidos sem sair do ar, e queria saber
se a Doce Mirabel precisaria de consultoria para o ano que vem.

A Júlia respondeu que não, e agradeceu.

O Rafa, copiado no e-mail, respondeu em seguida: *precisamos de uma
reunião sobre Kafka*.
:::

## O que ficou pelo caminho

O livro escolheu um caminho — do checkout que caía à Black Friday que não
caiu — e deixou de lado o que não estava nele. Vale nomear o que ficou de
fora, para que a próxima pergunta tenha para onde ir:

| Assunto | Por que ficou de fora | Por onde começar |
|---|---|---|
| streams do RabbitMQ | são um log, como o do Kafka, e a Doce Mirabel precisava de filas | a documentação de *RabbitMQ Streams* |
| AMQP 1.0 | é outro protocolo, nativo no RabbitMQ 4; a `php-amqplib` fala o 0-9-1 | a página *AMQP 1.0* do RabbitMQ |
| shovel e federation | ligam brokers diferentes, em redes ou empresas diferentes | os plugins `rabbitmq_shovel` e `rabbitmq_federation` |
| TLS, usuários e virtual hosts | segurança de broker é um livro à parte | o guia *Access Control* e o de TLS |
| MQTT e STOMP | protocolos de outros mundos — IoT, navegadores | os plugins de cada um |
| Kubernetes | o operador do RabbitMQ para Kubernetes resolve o cluster de outro jeito | o *RabbitMQ Cluster Operator* |

Tabela: Nenhum desses assuntos muda o que você aprendeu; todos o
estendem.

## O que você sabe

Se você fez o caminho com as mãos, você sabe coisas que não estão em
nenhuma tabela deste livro.

Você sabe que uma mensagem pode sumir com `no_ack` e sabe o nome da coluna
em que ela aparece quando não some. Você sabe que um exchange descarta o
que não tem destino, e que uma fila não muda de argumento. Você viu uma
nota ser emitida duas vezes por um retry que voltava pelo lugar errado,
e sabe por quê. Você viu um checkout responder 201 com o broker parado.

E você sabe, principalmente, fazer a pergunta que separa uma fila útil de
uma fila de enfeite: **isso precisa ser feito agora, ou só precisa ser
feito?** Todo o resto — exchange, ack, retry, outbox, quorum — é a
resposta técnica para a segunda metade dessa frase.

:::story O nome
Na sexta de dezembro, a Dona Cida fez uma fornada de geleia de ameixa
para os funcionários, como fazia todo ano. Mandou um vidro para a mesa
da Júlia, com um bilhete escrito à mão.

*Para a moça da fila.*

A Júlia agradeceu na cozinha. A Dona Cida estava mexendo a panela de
cobre, a mesma de 1979.

— O Kaique me disse que o programa que vocês usam tem o nome da geleia.

— Tem. Mirabel.

— Quem fez?

— Um desenvolvedor que eu não conheço. É de código aberto; qualquer um
pode usar.

— E por que ele pôs esse nome?

A Júlia pensou.

— Não sei. Nunca perguntei.

A Dona Cida desligou o fogo e bateu a colher na borda da panela, duas
vezes, como fazia havia quarenta e sete anos.

— Então pergunta. Nome de ameixa ninguém dá à toa.

Na parede, ao lado do fogão, o prego continuava lá. Vazio.
:::

:::summary
- O checkout da Doce Mirabel terminou com uma transação, uma outbox e
	nenhuma chamada externa além do pagamento; o comentário de 2023 foi
	apagado.
- Streams, AMQP 1.0, shovel, federation, segurança e Kubernetes ficaram
	de fora, e estendem — não substituem — o que o livro construiu.
- A pergunta que decide se uma fila vale a pena é se o trabalho precisa
	ser feito agora, ou só precisa ser feito.
:::
