# Mensageria One — roteiro editorial

> **Estado:** livro completo — abertura, 25 capítulos em 6 partes e
> encerramento (`content/00` a `content/26`). `python -m pipeline check`
> sem apontamentos; build com 305 páginas. Todo código e toda saída
> impressa foram executados contra um RabbitMQ 4 real (um nó, e um cluster
> de três no cap. 22); o consumidor Java do cap. 24 foi compilado com Maven
> e rodado contra o mesmo broker. Números de desempenho (caps. 16, 20, 23)
> são de um notebook de 12 núcleos e aparecem como medidos, não como regra.

**Volume 6 da coleção Zero One.** 25 capítulos numerados em 6 partes, mais a
abertura e o encerramento. Mesma filosofia dos volumes anteriores — o livro é
dado, o layout é o sistema — e a mesma régua editorial das `DIRETRIZES.md`:
ritmo variado, capítulos densos em código que roda, referência cruzada sempre
por `@cap:<slug>` e nunca para frente.

O livro ensina **RabbitMQ** — o suficiente para entender o que acontece dentro
do broker e decidir com segurança — e usa na prática a biblioteca
**Mirabel RabbitMQ** (`mirabel/rabbitmq`), em PHP. O leitor escreve primeiro o
protocolo à mão, com `php-amqplib`, e só depois ganha a biblioteca: ela chega
como resposta a um problema que ele já sentiu, nunca como mágica.

---

## Para quem é

Quem já escreve uma aplicação web (o PHP One cobre o necessário; qualquer
linguagem com HTTP e banco serve) e nunca pôs uma fila em produção. Ao fim, o
leitor:

1. explica, com os nomes certos, o caminho de uma mensagem do `publish` ao
   `ack` — conexão, canal, exchange, binding, fila, consumidor;
2. escolhe o tipo de exchange, a durabilidade e o prefetch por motivo, não por
   receita;
3. desenha retry com TTL e dead-letter, fila de erro, idempotência, confirms e
   outbox — e sabe o que cada um custa;
4. põe workers para rodar sob supervisor, mede a fila e aguenta uma Black
   Friday;
5. consome do mesmo broker em PHP e em Java, porque a mensagem é o contrato.

O que o livro **não** é: um curso de Kafka, de arquitetura de microsserviços
ou de certificação RabbitMQ. Kafka aparece como comparação honesta; clusters
aparecem no tamanho que uma empresa pequena precisa.

---

## O projeto contínuo

**Doce Mirabel.** Uma fábrica familiar de doces e geleias de Serra Clara, no
sul de Minas, que vende pela internet desde 2019. O carro-chefe é a geleia de
ameixa mirabel — a receita da Dona Cida, de 1979, que deu nome à empresa.

A loja é um Laravel monolítico feito por uma agência em 2021. Quando o cliente
clica em "Finalizar pedido", o `CheckoutController` faz, em sequência e dentro
da mesma requisição:

| Passo | Chama | Tempo típico | Tempo na Black Friday |
|---|---|---|---|
| 1 | gateway de pagamento | 400 ms | 2–9 s |
| 2 | ERP da fábrica (estoque, SOAP) | 900 ms | 30 s, depois cai |
| 3 | emissão da NF-e (SEFAZ) | 1,2 s | fora do ar por 40 min |
| 4 | cotação e etiqueta da transportadora | 600 ms | 3 s |
| 5 | e-mail de confirmação | 300 ms | 300 ms |
| 6 | WhatsApp da expedição | 500 ms | limite de taxa |
| 7 | pontos do programa de fidelidade | 200 ms | 200 ms |

Tabela: Sete dependências em fila indiana. Basta uma cair para o cliente ver
erro 500 — depois de ter sido cobrado.

O domínio foi escolhido porque entrega, sem inventar complexidade:

| O livro precisa de | O domínio entrega |
|---|---|
| trabalho que não cabe na requisição | NF-e, etiqueta, e-mail, estoque |
| fan-out | um `pedido.pago` interessa a quatro setores |
| roteamento por chave | `pedido.pago`, `pedido.cancelado`, `nfe.rejeitada`... |
| consumidor lento | a impressora de etiquetas da expedição |
| falha temporária | SEFAZ fora do ar, gateway lento |
| falha permanente | CEP que não existe, CPF inválido |
| duplicidade com dinheiro | a cobrança em dobro do pedido 40.117 |
| dual write | pedido salvo no banco, evento não publicado |
| outra linguagem | a transportadora parceira, que é Java |
| carga com data | Black Friday, 27 de novembro de 2026 |

### A arquitetura ao fim do livro

```text
Loja (Laravel) ── pedido.criado / pedido.pago ──▶ exchange "doce.eventos" (topic)
   │ outbox                                          │
   │                                                 ├─▶ fiscal.pedidos-pagos      → NF-e       (PHP, Mirabel)
   │                                                 ├─▶ expedicao.pedidos-pagos   → etiqueta   (PHP, Mirabel, prefetch 1)
   │                                                 ├─▶ estoque.pedidos           → ERP        (PHP, Mirabel)
   │                                                 ├─▶ avisos.pedidos            → e-mail/WhatsApp
   │                                                 └─▶ transportadora.coletas    → Java (Spring AMQP)
   └── cada fila com .retry (TTL + DLX) e .error, métricas no Prometheus
```

O checkout termina em **uma** escrita no banco (pedido + outbox, mesma
transação) e responde em 180 ms. Tudo o que era síncrono vira consumidor.

---

## A história satélite

Camada narrativa secundária, em blocos `:::story` de 200 a 380 palavras, em
pouco mais da metade dos capítulos. Mesmas duas proibições da coleção:
**nenhuma cena anuncia a piada no título**, e **nenhuma cena termina com o
narrador explicando o que ela significou**. O título da cena é uma fala ou um
fato dela.

### O que está em jogo

- **Prazo:** Black Friday, sexta-feira, **27 de novembro de 2026**. O livro
  começa na segunda, 7 de setembro — onze semanas e meia.
- **Dinheiro:** na Black Friday de 2025 o checkout ficou quatro horas fora do
  ar. A estimativa do Seu Norberto, o contador, é de **R$ 212 mil** em vendas
  perdidas, fora os 311 estornos. Em 2026 a Doce Mirabel tomou um empréstimo
  para a linha nova de envase, e a parcela foi calculada em cima da Black
  Friday.
- **Quem cobra:** o Rafa, toda segunda às 8h30, na "daily" de uma pessoa só; a
  Dona Cida, toda vez que um cliente antigo liga reclamando.
- **Algo em produção:** a loja, no ar, vendendo agora. E a collab com a *Tia
  Bia Receitas* — 2,3 milhões de seguidores — marcada para as 10h da Black
  Friday. Sem volta.

### O elenco

- **Júlia Tanaka** — desenvolvedora, oito anos de carreira, contratada em
  agosto como "a pessoa de tecnologia" da Doce Mirabel. Veio de uma fintech
  onde havia uma equipe inteira de plataforma; aqui, a equipe de plataforma é
  ela. Competente, cética com moda e com pressa. É a voz que explica o porquê.
- **Kaique** — 19 anos, estagiário de TI que também responde o WhatsApp do SAC
  à tarde. Aprende junto com o leitor e faz a pergunta que derruba o desenho,
  porque é o único que atende o cliente que foi cobrado duas vezes. Anota tudo
  no verso de etiquetas de envio — o "caderno de etiquetas".
- **Rafa (Rafael Mirabel)** — 31 anos, neto da Dona Cida, "CEO do digital".
  Cresceu a loja de zero a R$ 4 milhões por ano com Instagram e parcerias; é
  genuinamente bom nisso. Lê LinkedIn às 6h e chega com uma solução por
  semana: "só coloca uma fila", "só coloca um Kafka", "e se a fila tivesse IA?".
- **Dona Cida (Aparecida Mirabel)** — 71 anos, fundadora. Faz geleia desde
  1979, anotou pedido em papel por trinta anos e nunca perdeu um. Econômica nas
  palavras, é a especialista de domínio que ninguém chama de especialista: ela
  sabe exatamente o que acontece quando um pedido chega e o vidro acabou.
- **Denise** — chefe da expedição. Vinte e dois anos de fábrica. Opera a
  **Zebrinha**, a impressora de etiquetas térmica que imprime uma etiqueta a
  cada 1,8 segundo, nem um décimo mais rápido, e que ela defende como um
  membro da família. "A impressora não é lenta. Ela é a velocidade."
- **Seu Norberto** — contador terceirizado, 64 anos. Não entende de sistema e
  não precisa: ele entende de nota fiscal, e nota fiscal não é opcional, não é
  assíncrona para a Receita e não pode sair duas vezes. Traz a regra que
  ninguém pode flexibilizar.
- **Marcelão** — o desenvolvedor da agência que escreveu o checkout em 2021.
  Saiu da agência, virou "consultor" e cobra R$ 380 a hora para responder
  "isso aí eu fiz correndo". Não é vilão: fez, sozinho e com prazo, um sistema
  que vendeu por cinco anos.

### O Sistema

O quinto personagem, com maiúscula: `app/Http/Controllers/CheckoutController.php`,
412 linhas, um método `finalizarPedido()` com sete chamadas HTTP em sequência,
três `try/catch` vazios e um comentário na linha 1:

```php
// NAO MEXER - BLACK FRIDAY 2023 - MARCELO
```

Ele não é vilão. Vendeu R$ 11 milhões em cinco anos. Cada recurso do RabbitMQ
que o livro apresenta é medido contra ele — e em alguns capítulos o
`CheckoutController` ganha, o que é o ponto (@cap:quando-nao-usar-fila).

### O arco, em cinco movimentos

1. **Parte 1 — o problema.** A Black Friday de 2025 é reconstituída. A
   primeira proposta do Rafa ("só coloca uma fila") é certa pelo motivo errado.
2. **Parte 2 — o protocolo à mão.** Júlia e Kaique escrevem produtor e
   consumidor com `php-amqplib`. Cada conceito do AMQP aparece quando um
   defeito o exige: a mensagem que some, o consumidor que trava, a impressora
   que não acompanha.
3. **Parte 3 — a biblioteca.** O boilerplate cansa. Júlia adota a Mirabel —
   uma biblioteca pequena, de código aberto, que tem por coincidência o nome
   da ameixa da geleia — o que a Dona Cida considera um sinal.
4. **Parte 4 — as falhas.** O retry que vaza para o fiscal e emite a mesma
   NF-e duas vezes; a mensagem envenenada; o pedido 40.117; o broker que disse
   "recebi" sem ninguém perguntar; o banco que confirmou e a mensagem que não
   saiu.
5. **Partes 5 e 6 — produção e o dia.** Supervisor, métricas, teste de carga,
   o consumidor Java da transportadora, e 27 de novembro, que chega.

### Ganchos que voltam

Repetição com variação, plantada cedo e cobrada depois. Nenhum é explicado
quando volta.

| Gancho | Planta | Volta |
|---|---|---|
| o espeto de pedidos da Dona Cida (é uma pilha, não uma fila) | 0 | 2, 21 (ordem) |
| o pedido 40.117, cobrado duas vezes | 1 | 15, 24 |
| "só coloca uma fila" (Rafa) | 1 | 9 ("só coloca uma biblioteca"), 22 ("só coloca um Kafka") |
| a Zebrinha, 1,8 s por etiqueta | 3 | 8 (prefetch), 20 (carga), 24 |
| `// NAO MEXER - BLACK FRIDAY 2023` | 0 | 12, 25 (a linha é apagada) |
| o caderno de etiquetas do Kaique | 1 | uma etiqueta nova por parte |
| SEFAZ fora do ar | 1 | 13 (retry), 24 |
| os R$ 380 por hora do Marcelão | 1 | 12, 17 |

---

# Parte 1 — O problema antes da ferramenta

> Por que um checkout que funciona o ano inteiro cai no único dia que importa.

## 0. Antes de começar *(front matter)*

A pasta do checkout, a data, o elenco, o que instalar. **Evidência:** o leitor
sabe o que é o projeto e tem Docker e PHP 8.2+ respondendo.

## 1. A Black Friday que durou quatro horas — `a-black-friday-que-durou-quatro-horas`

**Mudança:** o leitor explica por que uma cadeia de chamadas síncronas cai
junto e calcula a disponibilidade dela. **Dor:** o `CheckoutController`
cobrou 311 clientes que viram erro 500. **Evidência:** um script PHP que
simula as sete chamadas, mede o tempo total e mostra a disponibilidade de
0,99⁷.

Assuntos: acoplamento temporal; latência somada; disponibilidade composta;
"trabalho que precisa ser feito" × "trabalho que precisa ser feito agora".
Cena: a reconstituição da BF 2025 na mesa da cozinha da fábrica, com as
planilhas do Seu Norberto.

## 2. Do espeto de papel ao broker — `do-espeto-de-papel-ao-broker`

**Mudança:** o leitor usa o vocabulário da mensageria (produtor, consumidor,
broker, fila, assíncrono, store-and-forward) e sabe de onde ele vem.
**Dor:** o Rafa quer "uma fila" e ninguém na sala sabe dizer o que isso
compra. **Evidência:** um produtor e um consumidor em PHP puro que se
comunicam por um diretório — a fila mais ingênua possível — e os três
defeitos dela.

Assuntos: fila × pilha (o espeto da Dona Cida é LIFO); desacoplamento no
tempo; o intermediário que guarda; história — telégrafo e *store-and-forward*,
IBM MQSeries (1993), JMS (1998), o problema do "cada fornecedor, seu
protocolo", AMQP (JPMorgan, 2003), RabbitMQ e Erlang (2007), Kafka (2011).

## 3. O que vamos construir — `o-que-vamos-construir`

**Mudança:** o leitor sobe o RabbitMQ com Docker, navega pelo painel e publica
e consome a primeira mensagem **à mão, pelo painel**. **Dor:** ninguém da
Doce Mirabel viu uma fila de verdade. **Evidência:** a mensagem publicada no
painel aparece na fila e é lida com "Get messages".

Assuntos: a arquitetura-alvo; `docker compose`; o painel de gerenciamento
(Overview, Connections, Channels, Exchanges, Queues); o *default exchange*.
Cena: a Denise e a Zebrinha — o consumidor lento é apresentado antes de ter
nome técnico.

# Parte 2 — O modelo AMQP à mão

> `php-amqplib`, sem biblioteca por cima. Cada conceito entra quando um
> defeito exige.

## 4. Conexão, canal e a primeira mensagem — `conexao-canal-e-a-primeira-mensagem`

Conexão TCP × canal; `queue_declare`; `basic_publish` no default exchange;
`basic_consume` e o loop de `wait()`; o corpo é bytes e o JSON é decisão sua.
**Evidência:** `produtor.php` e `consumidor.php` trocando um pedido.

## 5. Ack: quando a mensagem pode morrer — `ack-quando-a-mensagem-pode-morrer`

`no_ack=true` e o `kill -9` que some com cinco pedidos; ack manual; `Unacked`
no painel; redelivery; `nack` com `requeue` e o loop infinito na CPU.
**Evidência:** matar o consumidor no meio e ver a mensagem voltar.

## 6. Exchanges e bindings — `exchanges-e-bindings`

Direct, fanout, topic (`*` e `#`), headers; binding; routing key; por que a
fila não é endereço de ninguém. O `pedido.pago` chegando a fiscal, expedição e
avisos com um publish só. **Evidência:** três consumidores, uma publicação.

## 7. O que sobrevive a um restart — `o-que-sobrevive-a-um-restart`

`durable` na fila × `delivery_mode=2` na mensagem; `docker restart` com e sem;
os quatro casos da tabela. Mensagem sem fila é descartada em silêncio.
**Evidência:** a tabela preenchida pelo leitor com o que sobreviveu.

## 8. A Zebrinha e o prefetch — `a-zebrinha-e-o-prefetch`

Consumidores concorrentes; round-robin; `basic_qos` e prefetch; o consumidor
lento que acumula 3.000 `Unacked`; fair dispatch. **Evidência:** dois
consumidores, um lento, antes e depois de `prefetch_count=1`.

# Parte 3 — Mirabel: a mesma coisa em doze linhas

> O boilerplate da Parte 2 vira duas classes. Nada some: tudo muda de lugar.

## 9. Por que uma biblioteca — `por-que-uma-biblioteca`

Contar o que se repete em todo produtor e consumidor da Parte 2; o que uma
biblioteca deve esconder e o que não pode esconder; instalar
`mirabel/rabbitmq`; configuração por `MB_RABBITMQ_*`. Rafa: "só coloca uma
biblioteca". **Evidência:** o `produtor.php` do cap. 4 reescrito com `Event`.

## 10. Eventos com Mirabel — `eventos-com-mirabel`

`Event`, `$routingKey`, `publish()`; o que vai no fio: `message_id`,
`content_type`, `delivery_mode`, `type`, `timestamp`, `x-schema-version`;
`correlationId` e `idempotencyKey`. **Evidência:** a mensagem aberta no
painel, propriedade por propriedade.

## 11. Workers com Mirabel — `workers-com-mirabel`

`Worker`, `$queue`, `$routingKeys`, `handle(Envelope)`; o contrato (retornou
→ ack; lançou → retry; `reject()` → error); a topologia que o worker declara
sozinho. **Evidência:** as três filas (`.retry`, `.error`) aparecendo no
painel na primeira execução.

## 12. Mirabel dentro do Laravel — `mirabel-dentro-do-laravel`

Evento no lugar da chamada HTTP no `CheckoutController`; comando Artisan
`rabbitmq:consume`; `config:cache` e o `getenv()` vazio; testar sem broker com
uma `ConnectionFactoryInterface` falsa. **Evidência:** o checkout respondendo
em 180 ms e o teste de feature verde sem RabbitMQ.

# Parte 4 — Quando dá errado (e vai dar)

## 13. Retry com TTL e dead-letter — `retry-com-ttl-e-dead-letter`

Por que não `requeue`; DLX; fila de espera com TTL; `x-death` e a contagem
que sobrevive a restart. Cena: o retry que voltou pelo exchange principal e
emitiu a NF-e duas vezes — o defeito real da Mirabel antiga, corrigido
dead-lettering pelo *default exchange*. **Evidência:** a mensagem passando
três vezes pela `.retry`, e a fila vizinha recebendo uma cópia só.

## 14. A fila de erro e a mensagem envenenada — `a-fila-de-erro-e-a-mensagem-envenenada`

Falha temporária × permanente; `nack` × `reject`; JSON inválido; headers
`x-mirabel-*`; reprocessar a `.error` com cuidado. **Evidência:** CEP
inexistente parado na `.error` com o motivo escrito.

## 15. Idempotência: o pedido 40.117 — `idempotencia-o-pedido-40117`

At-least-once; de onde vêm as duplicatas; `message_id` × chave de negócio;
`IdempotencyStoreInterface` com índice único; o que não dá para desfazer.
**Evidência:** a mesma mensagem entregue três vezes, uma cobrança.

## 16. O broker disse que recebeu? — `o-broker-disse-que-recebeu`

Publisher confirms; `basic.nack`; `PublishNotConfirmedException`; mensagem
sem rota descartada mesmo com confirm (`mandatory`); novas tentativas
limitadas dentro de uma requisição HTTP. **Evidência:** publicar com o broker
parado e ver o erro, em vez do silêncio.

## 17. Outbox: o banco confirmou, a mensagem não — `outbox`

O dual write; tabela de outbox na mesma transação; `toOutboxMessage()`;
`OutboxDispatcher`; por que ainda é at-least-once. **Evidência:** derrubar o
broker entre o commit e o publish e não perder o pedido.

# Parte 5 — Produção

## 18. Workers que não morrem — `workers-que-nao-morrem`

Supervisor e systemd; `SIGTERM` e `stop()`; reconexão com backoff;
heartbeat; memória em processo longo; `health()`. **Evidência:** `docker
restart rabbitmq` com os workers se recuperando sozinhos.

## 19. Medir a fila — `medir-a-fila`

API de gerenciamento; profundidade × tempo de espera; taxa de entrada ×
saída; `/metrics` para Prometheus; o painel no Grafana; o alerta que acorda
alguém às 9h30 e não às 15h. **Evidência:** o painel com as quatro curvas.

## 20. A Black Friday de mentira — `a-black-friday-de-mentira`

Teste de carga do publisher e dos consumidores (os laboratórios do repositório
companheiro); quantos consumidores; o gargalo que não é o RabbitMQ (é a
Zebrinha). **Evidência:** a tabela de throughput por número de consumidores.

## 21. Ordem, prioridade e a fila que nunca esvazia — `ordem-e-prioridade`

O que o RabbitMQ garante de ordem e o que não; single active consumer; filas
de prioridade; filas por urgência. O espeto da Dona Cida volta.

## 22. Quorum queues e o broker que cai — `quorum-queues`

Cluster em três nós; quorum × classic; o que mudou no RabbitMQ 4; streams em
um parágrafo honesto; RabbitMQ × Kafka × SQS numa tabela. Rafa: "só coloca um
Kafka".

## 23. Quando a fila é a resposta errada — `quando-nao-usar-fila`

Consulta que precisa de resposta; consistência que o cliente vê; o custo
operacional de um broker; o `CheckoutController` ganha um round.

## 24. O broker não sabe que língua você fala — `o-broker-nao-sabe-que-lingua-voce-fala`

A transportadora parceira consome em Java (Spring AMQP) o que a loja publica
em PHP; contrato de mensagem; `x-schema-version`; publicar de volta
`coleta.agendada`. **Evidência:** um consumidor Java de 40 linhas lendo o
evento da Mirabel.

# Parte 6 — O dia

## 25. 27 de novembro — `27-de-novembro`

A Black Friday, hora a hora. O runbook; o SEFAZ cai às 10h14; a fila fiscal
cresce e ninguém perde pedido; a Zebrinha; o 40.117 volta. **Evidência:** o
runbook do leitor.

## Encerramento *(back matter)* — `encerramento`

A linha `// NAO MEXER` é apagada. Kaique lê o caderno de etiquetas. A Dona
Cida pergunta por que a biblioteca tem o nome da geleia, e ninguém sabe
responder.
