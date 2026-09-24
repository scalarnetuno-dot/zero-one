---
title: "Jobs"
number: 25
slug: jobs
part: p6
kicker: "Salvar um contrato levava oito segundos. Sete e meio eram o e-mail para a Helena, que ela lia no dia seguinte."
goal: >-
  Tirar do pedido o trabalho que não precisa acontecer antes da resposta:
  escrever um job, agendá-lo depois que o banco confirmar, saber o que o
  worker é, e fazer o job aguentar rodar duas vezes.
---

:::story Travou
Na segunda, 11 de maio, a Marta cadastrou um contrato de teste ao vivo,
na reunião com o Rômulo, para mostrar a tela nova. Clicou em **Salvar
contrato**.

A tela ficou parada. O cursor girando.

— Travou — disse o Rômulo.

— Não travou — disse a Marta, sem certeza.

Oito segundos. A página do contrato apareceu.

Depois da reunião, a Lívia abriu o log de homologação:

```text
Started POST "/contracts" for 10.0.4.17
Processing by ContractsController#create as HTML
  ...
  Delivered mail 6a1f...@nortea (7512.4ms)
Redirected to https://homolog.nortea.com.br/contracts/3241
Completed 302 Found in 8043ms
```

— Sete e meio de e-mail — disse ela. — O `notify_helena`.

O Caio leu por cima.

— E a Helena lê esse e-mail quando?

A Marta respondeu da porta:

— No dia seguinte. Às seis. Junto com a planilha.
:::

## O que não cabe no pedido

O capítulo @cap:callbacks deixou o `notify_helena` marcado: um e-mail
mandado dentro da gravação do contrato. Ele funciona. O problema é o
**tempo** e o **lugar**.

Um pedido HTTP é alguém esperando. Tudo que o controller faz antes de
responder é tempo de tela parada. A pergunta que separa o trabalho:

**Quem está esperando precisa disso para continuar?**

| Trabalho | A Marta precisa antes de ver a página? |
|---|---|
| gravar o contrato | sim, é o que ela pediu |
| criar a reserva | sim, senão a máquina parece livre |
| mandar o e-mail à Helena | não |
| gerar o PDF do contrato | não |
| avisar a Serra Azul pela API dela | não |

Tabela: As duas primeiras linhas são a operação. As outras três são
consequências dela, e podem acontecer segundos — ou minutos — depois.

## Job

Um **job** é uma classe que guarda um trabalho para ser feito depois, por
outro processo:

```ruby title="app/jobs/notify_helena_job.rb" numbered
class NotifyHelenaJob < ApplicationJob
  queue_as :default

  def perform(contract_id)
    contract = Contract.find_by(id: contract_id)
    return if contract.nil?

    ContractMailer.new_contract(contract).deliver_now
  end
end
```

`perform` é o método que o job executa quando chega a vez dele. O
controller, ou o model, não o chama direto. Agenda:

```ruby
NotifyHelenaJob.perform_later(contrato.id)
```

`perform_later` grava na **fila** um registro dizendo "rode
`NotifyHelenaJob` com este argumento", e volta na hora. Quem executa é
outro processo, que está olhando a fila.

O job recebe o **id**, não o contrato. O que vai para a fila é
transformado em texto e lido de volta depois, e um número atravessa isso
sem surpresa. Dentro do `perform`, o contrato é buscado de novo, **no
momento em que o job roda** — com o que o banco tem naquela hora, e não
com o que o controller tinha oito segundos antes. O `find_by` com `return`
cobre o contrato apagado nesse meio tempo.

:::term Job
Uma classe com um método `perform`, agendada com `perform_later` e
executada fora do pedido, por um processo que lê a fila.

O pedido responde assim que o job está na fila. O trabalho acontece
depois, e pode falhar sem que a pessoa na tela veja.
:::

## O worker

A fila do `nortea` é o Sidekiq, desde 2021, quando o Sérgio precisou gerar
o relatório de medição fora do pedido. O Sidekiq guarda a fila no Redis —
um banco em memória — e roda um processo à parte, o **worker**, que tira
os jobs da fila e os executa:

```ruby title="config/application.rb"
config.active_job.queue_adapter = :sidekiq
```

```text
$ bundle exec sidekiq
INFO: Booted Rails 7.2.2 application in development environment
INFO: Starting processing, hit Ctrl-C to stop
```

Sem o worker rodando, `perform_later` continua funcionando — agenda —, e
nada acontece. Os jobs ficam na fila, esperando. No servidor, o worker é
um serviço que o sistema operacional mantém de pé. Na sua máquina, é um
segundo terminal.

`ApplicationJob` e `perform_later` são do Rails — o Active Job. O Sidekiq
é quem executa. Trocar o executor não muda o código dos jobs.

## Agendar depois do `COMMIT`

O `notify_helena` era um `after_save`. Trocado por um job, ficaria:

```ruby
after_save :notify_helena

def notify_helena
  NotifyHelenaJob.perform_later(id)
end
```

E tem um defeito que só aparece com o worker rápido. O `after_save` roda
**dentro** da transação, antes do `COMMIT` — a ordem do capítulo
@cap:callbacks. O job vai para a fila na hora. Se o worker o pegar nos
poucos milissegundos antes de o banco confirmar, o `find_by` do `perform`
não encontra o contrato — para o resto do banco, ele ainda não existe —, e
o job termina sem mandar nada. E se a transação for desfeita, a Helena
recebe o aviso de um contrato que nunca existiu.

O callback certo espera o banco confirmar:

```ruby title="app/models/contract.rb" numbered
after_commit :notify_helena, on: :create

private

def notify_helena
  NotifyHelenaJob.perform_later(id)
end
```

`after_commit` roda depois do `COMMIT`. `on: :create` restringe à
criação: editar o responsável não manda outro e-mail.

Para e-mail, o Rails tem um atalho que já faz o job:

```ruby
ContractMailer.new_contract(contrato).deliver_later
```

`deliver_later` agenda um job de e-mail pronto, do próprio Rails. O
`NotifyHelenaJob` continua valendo como exemplo, e para trabalho que não é
e-mail.

```text
Completed 302 Found in 94ms
```

Noventa e quatro milissegundos. A Marta clicou de novo na reunião de
quarta, e o Rômulo não disse nada.

:::key
Job agendado por callback vai em `after_commit`, não em `after_save`. O
job roda em outro processo, e esse processo só enxerga o que o banco já
confirmou.
:::

## Falhar e tentar de novo

O job roda longe da tela. Se o servidor de e-mail estiver fora, ninguém
vê a exceção. O Active Job e o Sidekiq tentam de novo:

```ruby title="app/jobs/notify_helena_job.rb" numbered
class NotifyHelenaJob < ApplicationJob
  queue_as :default
  retry_on Net::SMTPServerBusy, wait: :polynomially_longer,
                                attempts: 5

  def perform(contract_id)
    # ...
  end
end
```

`retry_on` diz: se esta exceção acontecer, agende de novo, esperando cada
vez mais entre as tentativas, até cinco vezes. Depois disso, o job vai
para a lista de mortos do Sidekiq, que o painel dele mostra, e onde alguém
precisa olhar.

## O job que roda duas vezes

Toda fila entrega um job **pelo menos uma vez**. Um worker que cai depois
de mandar o e-mail e antes de avisar a fila que terminou recebe o mesmo
job de novo quando volta. Nenhuma configuração elimina isso. O job
precisa aguentar.

Para o e-mail da Helena, dois e-mails iguais são um incômodo. Para o
aviso à Serra Azul, que o capítulo seguinte cria, dois avisos podem ser
duas entradas no sistema deles. A técnica é a do `find_or_create_by!` do
capítulo @cap:callbacks: registrar que o trabalho foi feito, de um jeito
que a segunda execução descubra.

```ruby title="app/jobs/notify_serra_azul_job.rb" numbered
def perform(contract_id)
  contract = Contract.find_by(id: contract_id)
  return if contract.nil? || contract.notified_customer_at

  SerraAzulClient.new.notify(contract)
  contract.update_column(:notified_customer_at, Time.current)
end
```

Se já foi avisado, sai. `update_column` aqui é deliberado: é uma marca
técnica, sem validação e sem callback — o caminho por cima do capítulo
@cap:validacoes, usado para o que ele serve.

:::pitfall
Resta um buraco: o worker cair **entre** o `notify` e o `update_column`.
Aí a segunda execução avisa de novo. Fechar esse buraco exige que o outro
lado aceite o mesmo aviso duas vezes sem duplicar — um código único que
a Serra Azul reconheça. É a pergunta a fazer a qualquer integração: o
que acontece se a gente mandar duas vezes?
:::

:::summary
- Vai para job o que quem está esperando não precisa para continuar.
- `perform_later` agenda e volta; o worker executa. Sem worker, o job
  espera na fila.
- O job recebe o `id` e busca o registro quando roda.
- Job agendado por callback vai em `after_commit`. `deliver_later` é o job
  de e-mail pronto.
- `retry_on` tenta de novo. A fila entrega pelo menos uma vez: o job
  precisa aguentar rodar duas.
:::

:::exercise level=1
Para cada trabalho, diga se fica no pedido ou vai para um job:

1. Conferir que a máquina não está em outro contrato no período.
2. Gerar o PDF do contrato para a Serra Azul assinar.
3. Liberar a reserva ao cancelar.
4. Mandar à Helena o resumo das devoluções do dia, às 18h.

:::answer
1. No pedido. É a validação: sem ela, o contrato não pode ser gravado.
2. Job. O PDF pode levar segundos e ninguém precisa dele para ver a página.
3. No pedido, dentro da transação — o callback do capítulo
   @cap:callbacks. Cancelado com a reserva ainda de pé é a máquina presa.
4. Job, e agendado por horário, não por pedido. O Sidekiq tem extensões
   para isso; o importante é que ninguém espera por ele.
:::

:::exercise level=2
Um job do Sérgio de 2021 recebe o contrato inteiro:

```ruby
GerarMedicaoJob.perform_later(contrato)
```

E dentro dele usa `contrato.end_date`. Diga o que o job lê quando a data
de fim é alterada entre o agendamento e a execução.

:::answer
O Active Job não guarda o objeto inteiro na fila: guarda uma referência
ao registro, e o busca de novo no banco quando o job roda. O job lê a data
**nova**.

É o comportamento que se quer, e é também por isso que passar o id é a
forma recomendada: fica explícito que o registro é buscado na hora. O
problema aparece com o objeto apagado nesse meio tempo — a busca falha
antes mesmo do `perform` — e com objetos que não são registros, como um
hash montado no controller, que vão congelados na fila.
:::

:::exercise level=3
O Diego pergunta o que acontece se o Redis cair às 6h, na hora do pátio.
Responda para o formulário da Helena, para os e-mails e para a lista da
manhã.

:::answer
O formulário: `perform_later` precisa gravar na fila, e a fila está fora.
O `after_commit` levanta a exceção **depois** de o contrato estar gravado.
A Helena vê uma página de erro com o contrato já salvo, e pode tentar de
novo — e a validação de código único recusa, ou, pior, um código gerado
deixa passar o segundo. Vale capturar a falha de agendamento no callback e
registrar no log, para o contrato seguir com o aviso pendente.

Os e-mails: não saem enquanto o Redis estiver fora. Os agendados antes da
queda estão guardados nele; o Redis do `nortea` grava em disco, e eles
voltam quando ele volta.

A lista da manhã: não depende da fila. Ela lê o banco. É por isso que a
lista é uma consulta e não um job: a coisa que a Helena confere às 6h não
pode depender da peça que mais cai.
:::
