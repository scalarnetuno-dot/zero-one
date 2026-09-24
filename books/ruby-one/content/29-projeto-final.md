---
title: "Projeto final"
number: 29
slug: projeto-final
part: p6
kicker: "Quarta, 3 de junho, 6h. Nove canteiros, a planilha numa mão, o tablet na outra. A Helena conferiu linha por linha."
goal: >-
  Juntar o que o livro construiu num módulo que cobre a manhã de 3 de
  junho — a lista dos nove canteiros, o cancelamento que libera, a factory
  honesta, a consulta da Serra Azul — e fazer, sozinho, o próximo pedido
  que o pátio vai trazer.
---

:::story Seis horas
Quarta, 3 de junho. A Lívia chegou ao pátio às 5h40, de carona com o Caio.
Não era obrigação. Ninguém tinha pedido.

A Helena estava no portão com a prancheta. Na prancheta, a planilha
`patio_SEMANAL.xlsx` impressa. No braço, o tablet com a tela de ocupação
aberta, filtrada pela Serra Azul.

Ela foi descendo a lista do papel com o dedo e, a cada linha, olhava o
tablet.

— PT-118, Contagem, CT-2041. Bate. PT-121, Betim, CT-3215. Bate. PT-133,
Contagem, atrasada. — Ela parou. — Bate. Está escrito "devol...". Eu sei.

O Seu Nestor chegou às 5h55, olhou a prancheta, não olhou o tablet.

A Helena desceu as quarenta e uma linhas. Na trigésima quarta, parou de
novo.

— CP-007, Nova Lima. A planilha diz CT-3190. A tela diz CT-3196.

A Lívia sentiu o estômago.

O Caio olhou o tablet por cima do ombro dela.

— O 3190 foi cancelado na sexta. O Rômulo refez com o 3196. Mesmo
compactador, mesmo canteiro.

A Helena pegou a caneta, riscou o 3190 na planilha e escreveu 3196 do
lado.

— Então quem estava errada era eu.

O Seu Nestor olhou a correção à caneta por um tempo.

— Solta o caminhão.
:::

## O que o módulo cobre

O adendo pedia uma coisa: a Serra Azul consultando, numa página, qual
equipamento está preso a qual contrato. Para isso ser verdade, o sistema
inteiro precisou dizer uma coisa só sobre cada máquina. O que foi feito,
na ordem em que a manhã depende:

| A manhã precisa de | Onde está | Capítulo |
|---|---|---|
| uma regra do que é ocupar | `Contract#occupying?` e o escopo `current` | @cap:views |
| cancelado libera a máquina | escopo, disponíveis, callback | @cap:associacoes |
| nenhum contrato sem responsável | validação | @cap:validacoes |
| a mesma máquina, um contrato por vez | validação de período | @cap:validacoes |
| uma reserva por contrato ativo | callback com a mudança | @cap:callbacks |
| a data que a Helena reconhece | `started_at`, com comentário | @cap:modelos |
| os 212 sem status resolvidos | migration de dados | @cap:migrations |
| cancelar é uma ação com nome | rota `cancel` | @cap:rotas |
| a Serra Azul lê o que é dela | API `v1` e credencial | @cap:autenticacao |
| isso continuar valendo em julho | a suíte com a factory honesta | @cap:testes |

Tabela: Nenhuma linha é um sistema novo. Todas são o `nortea` de 2016,
com um defeito a menos.

O Rails de 2016 não foi apagado. As três datas de começo continuam na
tabela. O `exportar_patio.rb` continua montando nome de método num texto.
O `CT-2041-2` continua existindo. O módulo novo é o pedaço do sistema em
que a Helena aceita comparar com o papel — e hoje, pela primeira vez, a
diferença estava no papel.

## A lista da manhã

A tela que a Helena conferiu é uma consulta, e não um relatório gerado de
madrugada — a resposta do capítulo @cap:jobs para o dia em que o Redis
cair:

```ruby title="app/controllers/occupancy_controller.rb" numbered
class OccupancyController < ApplicationController
  def index
    @customer = Customer.find(params[:customer_id])
    @contracts = @customer.contracts
                          .occupying_on(Date.current)
                          .eager_load(:equipment)
                          .order(:site, "equipment.patrimony")
  end
end
```

```ruby title="app/models/contract.rb" numbered
scope :occupying_on, ->(dia) {
  where(status: "active")
    .where("end_date >= :dia OR returned_at IS NULL", dia: dia)
}
```

O escopo é a mesma regra do `occupying?` do capítulo @cap:views, escrita
para o banco: ativo, e dentro do prazo ou ainda não devolvido. Um lugar
para a regra de um registro, um lugar para a regra da lista, e um teste
que confere que os dois concordam:

```ruby title="spec/models/contract_spec.rb" numbered
it "o escopo e o predicado concordam" do
  hoje = Date.new(2026, 6, 3)
  create(:contract)
  create(:contract, :overdue)
  create(:contract, :cancelled)

  pelo_escopo = Contract.occupying_on(hoje).to_a
  pelo_metodo = Contract.all.select { |c| c.occupying?(hoje) }

  expect(pelo_escopo).to match_array(pelo_metodo)
end
```

`match_array` confere que as duas listas têm os mesmos itens, em qualquer
ordem. Se alguém mudar a regra num lugar e esquecer o outro, este exemplo
é o que avisa.

## A consulta da Serra Azul

Às 10h, o Rômulo mostrou a página à TI da Serra Azul. Ela era a lista da
Helena, pela API, com a credencial de leitura:

```text
$ curl -s -H "Authorization: Bearer sa_live_..." \
    "https://nortea.com.br/api/v1/contracts?status=ativo"
[{"codigo":"CT-2041","patrimonio":"PT-118","canteiro":"contagem",
  "status":"ativo","chegada":"2026-03-03T06:12:00-03:00",
  "fim":"2026-06-30"},
 ...]
```

Quarenta e uma entradas. As mesmas quarenta e uma da prancheta.

O adendo foi cumprido na parte que dependia do sistema. A renovação foi
assinada às 16h, pelo Rômulo, e pela primeira vez em três anos a cláusula
de R$ 1.800 por dia não foi discutida na reunião.

## O que fica para depois

O livro termina aqui. O `nortea`, não. A lista que ficou na mesa do
Renato na sexta, 5 de junho:

- **O Ruby do servidor.** O 3.3 está só em manutenção de segurança até 31
  de março de 2027. A subida para o 3.4 precisa de uma data, longe de
  qualquer renovação, e da esteira rodando com as duas linhas antes.
- **As três datas.** Renomear para o que cada uma é, com migration, em dois
  deploys, depois de achar todos os leitores.
- **O `site_code`.** Primeiro o relatório para de ler, depois a coluna sai.
- **Os 94 contratos antigos sem responsável.** Preencher com a Helena, e
  então `null: false` no banco.
- **O `exportar_patio.rb`.** Trocar o nome montado num texto por uma lista
  explícita de métodos.
- **A planilha.** Não se apaga planilha. Ela perde sozinha, no dia em que o
  Seu Nestor olhar o tablet antes do papel.

:::milestone
Fim do livro. Você escreveu Ruby na `patio` e o levou para dentro de um
Rails de dez anos: diária em centavos, contrato como classe, falha com
tipo, gem com versão travada, model que conhece o que cada coluna
significa, validação que recusa o contrato impossível, callback que
observa a mudança, rota com nome, controller de sete linhas, view que
pergunta ao model, console usado sabendo o que grava, teste com a factory
honesta, job fora do pedido, API com contrato escrito e credencial com
escopo, e um deploy no horário certo. A Helena conferiu, linha por linha,
e a diferença estava no papel.
:::

:::summary
- O módulo de contratos não é um sistema novo: é o `nortea` de 2016 com a
  regra de ocupação num lugar só.
- A lista da manhã é uma consulta, com escopo, e um teste que confere que
  escopo e predicado concordam.
- A API da Serra Azul devolve a mesma lista, com a tabela combinada e a
  credencial de leitura.
- O que ficou para depois tem data e ordem, e nada dele é "reescrever do
  zero".
:::

:::exercise level=1
A Helena pede que a tela de ocupação mostre, no topo, os contratos
atrasados. Escreva a mudança no controller, sem mexer na regra de
ocupação.

:::answer
```ruby
@contracts = @customer.contracts
                      .occupying_on(Date.current)
                      .eager_load(:equipment)
                      .order(:site, "equipment.patrimony")
                      .to_a
                      .sort_by { |c| c.overdue? ? 0 : 1 }
```

`sort_by` com `0` para atrasado e `1` para o resto põe os atrasados
primeiro. O `sort_by` do Ruby não promete manter a ordem anterior entre
itens iguais, e a ordem por canteiro e patrimônio dentro de cada grupo
pode se perder. Para garanti-la, ordene por um array, que o Ruby compara
posição por posição:

```ruby
.sort_by { |c| [c.overdue? ? 0 : 1, c.site, c.equipment.patrimony] }
```

A regra de ocupação não mudou. Mudou a ordem em que a tela a mostra.
:::

:::exercise level=2
O Diego traz o caso do dia 4: uma plataforma devolvida às 17h, com o
contrato ainda ativo e a data de fim no dia 30. A Helena quer que ela
apareça livre a partir da devolução. Escreva a mudança no predicado, no
escopo e no teste, e diga por que os três mudam juntos.

:::answer
Devolvido é devolvido, qualquer que seja a data de fim:

```ruby
def occupying?(hoje = Date.current)
  return false unless status == "active"
  return false if returned_at

  true
end
```

```ruby
scope :occupying_on, ->(dia) {
  where(status: "active", returned_at: nil)
}
```

```ruby
it "devolvido antes do fim não ocupa" do
  devolvido = Time.zone.local(2026, 6, 4, 17)
  contrato = build(:contract, returned_at: devolvido)
  expect(contrato.occupying?(Date.new(2026, 6, 5))).to be(false)
end
```

A regra ficou mais simples: ocupa quem está ativo e não voltou. O `hoje`
continua no predicado para não mudar quem o chama.

Os três mudam juntos porque o teste do capítulo confere que predicado e
escopo concordam. Mudar só um deixa a esteira vermelha — que é
exatamente o que ela existe para fazer.
:::

:::exercise level=3
O próximo pedido é seu. O Rômulo fechou com uma segunda construtora, a
Vale Norte, e ela quer a mesma consulta pela API, mas **também** quer ser
avisada, pela API dela, quando um contrato for cancelado.

Faça o pedido inteiro, sozinho. Antes de escrever código, escreva as
respostas a estas perguntas, e deixe-as no primeiro commit:

1. Qual é a tabela combinada com a Vale Norte, e em que ela difere da da
   Serra Azul?
2. Onde mora o aviso: callback, controller ou job? Em qual momento da vida
   do contrato ele é agendado?
3. O que acontece se o aviso for enviado duas vezes, e como a Vale Norte
   reconhece a repetição?
4. Qual credencial a Vale Norte usa, com qual escopo, e qual teste prova
   que ela não lê contrato da Serra Azul?
5. Em que dia e horário isso sobe?

:::answer
Não há uma resposta única. Uma solução que acerta costuma ter isto:

**A tabela** é a mesma da Serra Azul — os seis campos, os status em
português —, e a diferença é acrescentada, não trocada: se a Vale Norte
quiser um campo a mais, ele entra na `v1` para as duas, porque acrescentar
não quebra ninguém.

**O aviso** é um job, agendado por um callback `after_commit` que observa
a mudança para cancelado — a combinação dos capítulos @cap:callbacks e
@cap:jobs. Nada de chamar a API da Vale Norte dentro do pedido da Helena.

**A repetição**: o job marca o contrato como avisado depois de enviar, e
sai se já estiver marcado; e o aviso leva o código do contrato e o
instante do cancelamento, para a Vale Norte descartar o que já recebeu.

**A credencial**: uma `ApiCredential` ligada ao `Customer` da Vale Norte,
com escopo `read`. O teste de *request* cria um contrato da Serra Azul e
confere o `404` com a credencial da Vale Norte.

**O dia**: segunda ou terça, 14h, longe da carga das duas construtoras,
com a esteira verde e a Helena avisada.

Se a sua solução mexeu na regra de ocupação, vale voltar e perguntar por
quê. O pedido não era sobre ocupação. Era sobre contar a outra pessoa, de
um jeito que ela possa confiar, o que o `nortea` já sabe.
:::
