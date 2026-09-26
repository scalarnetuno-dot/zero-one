---
title: "A Black Friday de mentira"
number: 20
slug: a-black-friday-de-mentira
part: p5
kicker: "O RabbitMQ aguentou os cinco mil pedidos da hora de pico sem perceber. A Zebrinha, não — e ninguém esperava que aguentasse."
goal: >-
  Planejar a carga da Black Friday a partir dos números do ano anterior,
  medir quanto cada consumidor processa e quanto mais consumidores ajudam,
  achar o gargalo que não é o broker, e transformar os números num plano
  de capacidade por fila.
---

:::story A planilha do Seu Norberto
Faltando cinco semanas, a Júlia pediu ao Seu Norberto os números da Black
Friday de 2025 — não os perdidos, os que tentaram entrar.

Ele trouxe uma planilha impressa, dobrada em quatro.

— Das dez às onze, 1.140 tentativas de pagamento. Das onze ao meio-dia,
4.960. Depois foi caindo.

— Cinco mil numa hora — disse a Júlia.

— A collab da Tia Bia deste ano é às dez — lembrou o Rafa. — Ela tem o
dobro de seguidores da parceira do ano passado.

— Então dez mil — disse o Kaique.

— Não dá para saber — disse a Júlia. — Mas dá para saber o que acontece
se forem dez mil.

A Denise, que tinha vindo só para ouvir, cruzou os braços.

— Dez mil etiquetas, a um vírgula oito segundo cada, são cinco horas de
Zebrinha. Sem parar para trocar o rolo.
:::

A Denise fez, de cabeça, a conta mais importante do capítulo. Mas ela é
uma das contas — a da expedição. Cada fila tem a sua, e cada uma tem um
gargalo diferente. O jeito de achá-los é o mesmo: medir quanto um
consumidor faz, medir quanto mais consumidores ajudam, e comparar com o
que vai entrar.

## O que vai entrar

O pico de 2025 foi de cerca de 5.000 pagamentos numa hora. A projeção
para 2026, com a collab maior, é de até 10.000 na hora de pico. Em
mensagens por segundo, para o broker:

```text
10.000 pedidos / 3.600 s ≈ 2,8 pedidos por segundo
```

Cada pedido pago é **um** publish no checkout e **quatro** entregas — uma
por fila interessada: fiscal, expedição, avisos, auditoria. No pior
momento, o RabbitMQ recebe menos de três mensagens por segundo e entrega
menos de doze.

Para o broker, isso é nada. O capítulo @cap:o-broker-disse-que-recebeu
mediu mil publicações confirmadas em pouco mais de um segundo num
notebook: quase trezentas vezes o pico da Doce Mirabel. O RabbitMQ não é o
gargalo da Black Friday, e o teste de carga não é para provar que ele
aguenta. É para descobrir quem não aguenta.

## Quanto um consumidor faz

O experimento usa uma fila de carga e um worker cujo `handle()` custa 20
milissegundos, o tempo de gravar num banco e chamar uma API rápida. Um
orquestrador sobe N consumidores, publica 600 pedidos de uma vez e mede
quanto a fila leva para esvaziar, consultando o `rabbitmqctl` até que
`ready` e `unacked` cheguem a zero:

| Consumidores | 600 pedidos em | Vazão |
|---|---|---|
| 1 | 13,3 s | 45/s |
| 2 | 7,1 s | 85/s |
| 4 | 3,4 s | 174/s |
| 8 | 2,2 s | 272/s |

Tabela: Medido num notebook de 12 núcleos, com todos os processos na
mesma máquina.

Até quatro consumidores, cada um a mais **dobra** a vazão: o trabalho é
independente, e o prefetch 1 reparte a fila pela capacidade de cada um.
Com oito, o ganho cai — a vazão sobe 56%, e não 100%. Os oito processos,
o broker e o orquestrador disputam a CPU do mesmo notebook, e cada ida e
volta pelo broker pesa mais quando o trabalho é curto.

Um consumidor de 20 ms faz 45 por segundo, e o pico da Doce Mirabel é de
2,8. **Um** consumidor dessa fila daria conta da Black Friday com folga de
quinze vezes.

## Quem não aguenta

A tabela acima vale para um trabalho de 20 ms. O trabalho de verdade de
cada fila é outro, e é ele que decide:

| Fila | Tempo por pedido | Um consumidor faz | Pico de 10.000/h pede |
|---|---|---|---|
| avisos | ~0,3 s (e-mail) | ~12.000/h | 1 consumidor |
| estoque | ~0,9 s (ERP) | ~4.000/h | 3 consumidores |
| fiscal | ~1,2 s num dia bom | ~3.000/h | 4 consumidores |
| expedição | 1,8 s (Zebrinha) | 2.000/h | **5 Zebrinhas** |

Tabela: "Um consumidor faz" é 3.600 dividido pelo tempo por pedido.

Três das quatro filas se resolvem com mais processos, que custam quase
nada. A expedição não: o consumidor dela é uma impressora. Pôr cinco
workers lendo a fila da expedição não imprime mais rápido — são cinco
processos esperando a mesma Zebrinha.

E o fiscal tem um asterisco. A SEFAZ num dia bom leva 1,2 s; na Black
Friday de 2025 ela ficou fora do ar quarenta minutos. Consumidores a mais
não ajudam contra um serviço que não responde; o que ajuda é a janela de
retry do capítulo @cap:retry-com-ttl-e-dead-letter ser maior que a queda.

:::key
O teste de carga de um sistema com filas não mede o broker. Mede o
**trabalho** de cada consumidor, e acha a fila cujo trabalho não escala
com processos — uma impressora, uma API com limite de taxa, um serviço
externo lento. É ela que decide o plano.
:::

## O plano de capacidade

Com os números, cada fila ganha uma decisão explícita, com o custo dela:

| Fila | Decisão para 27/11 | Custo aceito |
|---|---|---|
| avisos | 2 consumidores | nenhum |
| estoque | 4 consumidores | carga no ERP; combinar com a fábrica |
| fiscal | 6 consumidores; retry de 5 min × 14 tentativas | notas podem atrasar até ~1h se a SEFAZ cair |
| expedição | 2 impressoras (a Zebrinha e a nova), prefetch 1 | se a nova falhar, a fila acumula e esvazia à noite |

Tabela: A expedição depende de uma impressora que nunca trabalhou num pico, e o plano diz isso em voz alta.

A última linha é a decisão mais importante e a menos técnica. A
impressora nova, de 0,2 segundo por etiqueta, faz cerca de 18 mil por
hora; com a Zebrinha, a expedição passa de 20 mil — o dobro do pico
projetado. Mas a nova chegou em outubro e nunca imprimiu sob pressão, e a
Denise confia na Zebrinha. O plano combinado cobre o caso ruim: se a nova
falhar, a Zebrinha segue sozinha, a fila acumula, e os pedidos das dez às
duas são embalados até as oito da noite. O cliente recebe no mesmo prazo,
porque a transportadora coleta uma vez por dia, às seis — e o alerta de
espera da expedição fica em quatro horas, não em cinco minutos.

Essa conversa só foi possível porque a fila existe. No sistema de 2025, o
checkout mandava imprimir na hora, e a Zebrinha travou.

## Ensaiando

Com o plano no papel, ele precisa ser ensaiado com carga de verdade — não
em produção, mas num ambiente com os mesmos workers e o mesmo broker. O
repositório companheiro do livro traz laboratórios prontos para isso: o
**Stress Test** publica até um milhão de mensagens e mede o publisher; o
**Consumer Lab** sobe de um a oito consumidores reais e mede quanto tempo
a fila leva para esvaziar; o **Production Gate** transforma os números num
veredito. Os três usam a Mirabel e o mesmo `/metrics` do capítulo
anterior.

O ensaio tem uma regra: ele termina com os **alertas** disparando e sendo
atendidos. Uma fila de erro que recebeu mensagens no ensaio e que ninguém
percebeu é o defeito mais valioso que um ensaio pode encontrar — ele custa
zero reais em outubro e o dia inteiro em novembro.

:::pitfall
Um teste de carga com `handle()` vazio mede o RabbitMQ e mais nada, e
sempre passa. O `handle()` do ensaio precisa fazer o que faz em produção
— ou esperar o tempo que o serviço externo leva —, senão a tabela de
capacidade é de outro sistema.
:::

:::milestone
Você tem: a carga projetada da Black Friday em mensagens por segundo; a
vazão medida por número de consumidores; o gargalo de cada fila
identificado — e o da expedição aceito como fila que acumula; e um plano
de capacidade com o custo escrito ao lado de cada decisão.
:::

:::summary
- Converta o pico de negócio em mensagens por segundo: 10.000 pedidos por
	hora são menos de 3 publicações e 12 entregas por segundo — pouco para
	o broker.
- Consumidores concorrentes escalam quase linearmente enquanto o trabalho
	for independente e houver CPU; na mesma máquina, o ganho cai.
- A capacidade de cada fila é 3.600 dividido pelo tempo por mensagem,
	vezes o número de consumidores que o trabalho permite.
- O gargalo é a fila cujo trabalho não escala com processos — uma
	impressora, uma API lenta ou com limite —, e ela decide o plano.
- O ensaio usa `handle()` com o custo real e termina com alertas
	disparando e sendo atendidos.
:::

:::exercise level=1
A SEFAZ passa a responder em 3 segundos na hora de pico, em vez de 1,2.
Quantos consumidores do fiscal são necessários para 10.000 pedidos por
hora, e o que isso muda no plano?

:::answer
Um consumidor faz 3.600 ÷ 3 = 1.200 notas por hora. Para 10.000, são 9
consumidores — arredondando para cima, 10, para ter folga.

O plano de 6 consumidores deixa de dar conta: a fila fiscal cresce cerca
de 2.800 por hora no pico e esvazia depois. Como a nota tem prazo em
horas, isso pode ser aceitável — mas precisa ser uma decisão, com o
alerta de espera do fiscal configurado para o limite que o Seu Norberto
aceitar.
:::

:::exercise level=2
O Rafa sugere pôr 50 consumidores em todas as filas "para garantir". Liste
o que isso custa, fila por fila, e o que acontece com o ERP da fábrica.

:::answer
Avisos: 50 processos para uma fila que precisa de 1 — memória e conexões
à toa, e o provedor de e-mail recebendo rajadas que podem estourar o
limite de envio. Fiscal: 50 chamadas simultâneas à SEFAZ, que pode limitar
ou bloquear o emissor. Expedição: 50 processos esperando duas
impressoras, sem imprimir uma etiqueta a mais.

E o ERP: 50 consumidores de estoque são 50 conexões SOAP ao mesmo tempo
num sistema que trava com poucas dezenas. A fila, que protegia o ERP
dosando a carga, passaria a ser o jeito mais rápido de derrubá-lo.
Consumidores são uma válvula: abri-la além do que o serviço de trás
aguenta só muda o lugar da enchente.
:::
