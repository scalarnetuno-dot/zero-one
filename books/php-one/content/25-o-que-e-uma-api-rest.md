---
title: "O que é uma API REST"
number: 25
slug: o-que-e-uma-api-rest
part: p5
kicker: "Seu Juvenal quer um botão que renova tudo. A pergunta difícil não é como fazer — é o que acontece quando alguém aperta duas vezes."
goal: >-
  Desenhar os endereços de uma API a partir dos recursos, separar o que é
  seguro do que é idempotente, escolher o status que já responde metade da
  pergunta, e saber o que pode e o que não pode mudar depois que alguém
  começou a consumir.
---

:::story Renovar tudo
— Uma coisinha — disse Seu Juvenal. — Um botão que renova tudo de uma vez.
A Dona Marlene pega seis livros.

— Dá — disse Dedé.

— Ótimo.

— A pergunta é o que acontece quando ela aperta duas vezes.

Seu Juvenal achou que era piada e esperou o resto.

— Falando sério: o telefone dela é ruim. Ela aperta, a tela fica rodando,
ela aperta de novo. Os seis livros renovam duas vezes?

— Renovam vinte e oito dias?

— Ou o sistema recusa a segunda e ela acha que não funcionou.

Tainá levantou os olhos do caderno.

— E se ela fechar o aplicativo no meio?

— Aí é melhor ainda: ninguém sabe se renovou.
:::

## O endereço nomeia uma coisa, não uma ação

Uma API se desenha listando **os substantivos do domínio** e decidindo quais
deles merecem endereço próprio. A Casa Amarela tem cinco: livro, exemplar,
leitor, empréstimo e reserva.

Cada substantivo rende dois endereços:

| Endereço | O que é |
|---|---|
| `/livros` | a coleção inteira |
| `/livros/12` | um item dela |

E quando uma coisa só existe dentro de outra, ela vira um endereço aninhado:

```text
/livros/12/exemplares
```

Isso quer dizer "os exemplares **daquele** livro", e é diferente de
`/exemplares?livro_id=12`, que quer dizer "a coleção de todos os exemplares,
filtrada". As duas formas funcionam; a primeira diz que exemplar não faz
sentido sozinho, e no acervo ele não faz mesmo.

:::pitfall
Filtro não é recurso. `/livros/infantis` parece organizado e cria um
problema no dia seguinte, quando alguém quiser os infantis de 2020 em
diante, ou os infantis emprestados, ou os infantis de um autor.

Cada combinação viraria um endereço novo, e a lista cresce como o quadro de
classes do capítulo @cap:heranca-interfaces-e-traits. Filtro mora na
consulta: `/livros?classificacao=infantil&ano_minimo=2020`.

A régua: **se você consegue imaginar a combinação com outro filtro, é
filtro.**
:::

## Seguro, idempotente, e nem um nem outro

Aqui está a parte que quase ninguém ensina e que decide o comportamento da
sua API sob rede ruim.

:::term Seguro e idempotente
**Seguro** é o pedido que não muda nada no servidor. Pode ser repetido à
vontade, em qualquer ordem, por qualquer um.

**Idempotente** é o pedido que pode ser repetido sem mudar o resultado:
fazer uma vez e fazer cinco vezes deixa o sistema no mesmo estado.

Todo pedido seguro é idempotente. O contrário não vale.
:::

| Verbo | Seguro | Idempotente |
|---|---|---|
| `GET` | sim | sim |
| `PUT` | não | sim |
| `DELETE` | não | sim |
| `POST` | não | **não** |
| `PATCH` | não | depende do que está escrito |

Tabela: Isso não é convenção de estilo. É o que os navegadores, os
intermediários de rede e as bibliotecas de cliente supõem sobre a sua API
sem perguntar.

`PUT /livros/12` é idempotente porque manda o livro inteiro: repetir grava o
mesmo conteúdo. `DELETE /livros/12` é idempotente porque o **estado** final
é o mesmo — o livro não existe — mesmo que a segunda chamada responda `404`
em vez de `204`.

`POST /emprestimos` não é nenhum dos dois, e é aí que mora a Dona Marlene.

## O relatório que corrigia

O Sistema tem uma tela que você já conhece: o relatório que, quando acha uma
linha estranha, conserta. O endereço dela é este:

```text
GET /relatorio.php?mes=02&acao=corrigir
```

Um `GET` que altera dados quebra uma promessa que ninguém escreveu no código
e todo mundo depende:

- **o navegador pode buscar antes de você clicar**, para a página abrir mais
  rápido;
- **a rede pode guardar a resposta** e devolvê-la de novo para outra pessoa;
- **o cliente pode repetir sozinho** quando a conexão cai, porque repetir um
  `GET` é seguro por definição;
- **o endereço inteiro vai para o log**, com os parâmetros, em cada máquina
  pela qual passar.

O defeito clássico dessa família é o sistema que perdeu conteúdo porque um
robô de indexação seguiu todos os links da tela de administração, e os links
de apagar eram `GET`. Ninguém tinha escrito nada errado — todos tinham
escrito `<a href>`.

:::key
A pergunta que separa `GET` de todo o resto não é "isso lê ou escreve?". É:
**algum intermediário pode repetir isso sozinho sem me avisar?**

Se a resposta for sim, e repetir causar dano, o verbo está errado.
:::

## A repetição que você não controla

Volte ao telefone da Dona Marlene, porque o problema dela não é ela apertar
duas vezes. É pior.

```text
> POST /renovacoes
> (a conexão cai antes da resposta chegar)
```

O aplicativo não sabe o que aconteceu. Pode ser que o pedido não tenha
chegado; pode ser que tenha chegado, sido processado e a resposta é que se
perdeu. As duas situações são idênticas do lado de fora.

Um cliente bem escrito tenta de novo. E se a sua API não estiver preparada,
a segunda tentativa cria a segunda renovação.

Há duas saídas, e a ordem importa.

**A primeira é desenhar a operação para ser idempotente.** "Renovar" pode
significar "somar catorze dias ao prazo" — que dobra quando repete — ou
"definir o prazo para catorze dias a partir de hoje" — que dá o mesmo
resultado nas duas chamadas. A segunda definição é a mesma regra da Vera,
custa igual e resolve o problema sozinha.

**A segunda, quando a operação não pode ser idempotente por natureza**, é
deixar o cliente carimbar a tentativa:

```text
POST /emprestimos
Idempotency-Key: 7f3a9c-tentativa-1
```

O servidor guarda a chave junto com a resposta. Se a mesma chave voltar, ele
devolve a resposta guardada em vez de criar de novo. É o mecanismo que as
operadoras de pagamento usam, e pelo mesmo motivo: ninguém quer cobrar duas
vezes porque o celular travou.

## Então o que é "renovar tudo"

Nem `PUT /emprestimos`, nem `GET`.

`PUT` numa coleção significa "substitua a coleção inteira pelo que estou
mandando" — o que, lido ao pé da letra, apagaria todos os empréstimos que
não estivessem no corpo. Ninguém faz isso, e é exatamente por isso que o
verbo não serve: ele promete uma coisa que você não vai cumprir.

A saída é lembrar que **a renovação é uma coisa**. Ela tem data, tem autor,
tem quantidade, e a Vera vai querer um relatório dela em algum momento. Se é
uma coisa, ela tem coleção:

```text
POST /leitores/47/renovacoes
Content-Type: application/json

{"emprestimos": [4471, 4472, 4473]}
```

```text
201 Created
Location: /leitores/47/renovacoes/91

{
  "id": 91,
  "renovados": [4471, 4472, 4473],
  "recusados": []
}
```

Criar um recurso chamado renovação resolve três coisas de uma vez: o verbo
fica honesto, a operação ganha um identificador que o cliente pode consultar
depois de uma conexão caída, e a resposta consegue dizer que dois livros
renovaram e um não — o que `PUT` não teria como expressar.

:::key
Quando uma ação não cabe em criar, ler, alterar ou apagar, a pergunta não é
"qual verbo eu invento?". É: **que substantivo está escondido aqui?**

Renovar esconde uma renovação. Devolver esconde uma devolução. Cancelar
esconde um cancelamento. Quase sempre o substantivo é algo que o negócio já
conta, já arquiva e já quer em relatório.
:::

## O status já responde metade

```text
201 Created
Location: /leitores/47/renovacoes/91
```

O `Location` na resposta de um `201` diz onde a coisa criada foi morar. É o
que permite ao cliente consultar depois sem adivinhar o endereço — e é o que
faz a renovação perdida da Dona Marlene ser recuperável.

Duas escolhas de status costumam ser decididas no braço e merecem regra:

**`409` contra `422`.** O `422` é sobre o **conteúdo do pedido**: campo
faltando, data no formato errado, quantidade negativa. O `409` é sobre o
**estado do sistema**: o pedido está impecável e a realidade não permite —
o exemplar já está emprestado, o leitor tem multa, a reserva já foi
cancelada.

A diferença é útil para quem consome: `422` pede para o usuário corrigir o
que digitou; `409` pede para ele olhar a tela de novo, porque o mundo mudou.

**`200` com erro dentro.** Não existe. Um corpo `{"sucesso": false}` com
status `200` obriga todo cliente a abrir e interpretar toda resposta antes
de saber se deu certo — e o primeiro que esquecer vai tratar um erro como
sucesso em silêncio.

## O contrato com quem você não controla

No dia em que o aplicativo do leitor estiver publicado na loja, a sua API
deixa de ser sua. Existem telefones por aí com a versão antiga instalada, e
eles não vão atualizar porque você pediu.

| Mudança | Quebra? |
|---|---|
| acrescentar um campo na resposta | não |
| acrescentar um campo **opcional** no pedido | não |
| acrescentar um endereço novo | não |
| renomear um campo | **sim** |
| remover um campo | **sim** |
| mudar o tipo de um campo | **sim** |
| tornar obrigatório um campo que era opcional | **sim** |
| mudar o status devolvido num caso existente | **sim** |

Tabela: A coluna da esquerda é toda de acréscimos; a da direita, toda de
alterações e remoções. É a regra inteira, e ela cabe numa frase.

:::pitfall
O item mais esquecido é o último. Trocar um `200` por um `204` porque "não
tinha corpo mesmo" parece arrumação e derruba todo cliente que fazia
`if (status == 200)`.

O mesmo vale para o formato de erro. Se hoje o erro sai como
`{"erro": "texto"}` e amanhã sai como `{"erros": [...]}`, não importa que o
segundo seja melhor: o aplicativo publicado espera o primeiro.
:::

Quando a mudança for inevitável, o caminho conhecido é conviver com as duas
por um tempo — endereço novo em paralelo, ou um número de versão no caminho
— e desligar a antiga com data anunciada e medição de quem ainda usa.

## REST não é lei

REST é um estilo, não uma especificação com fiscal. Ele vale porque cria
expectativa compartilhada: quem nunca viu a sua API consegue adivinhar
metade dela.

Onde ele não couber, force menos e documente mais. Uma busca com quinze
filtros, uma operação em lote, um cálculo que não guarda nada — todas
existem, e nenhuma fica melhor sendo torcida até parecer um recurso.

O erro grave não é fugir do estilo. É fugir **em silêncio**, deixando o
cliente descobrir por tentativa.

## O desenho da Casa Amarela

Escrito antes da primeira rota, e é isso que faz dele um desenho:

| Verbo e endereço | Devolve | Idempotente |
|---|---|---|
| `GET /livros` | `200` com a lista | sim |
| `GET /livros/12` | `200` ou `404` | sim |
| `POST /livros` | `201` + `Location` | não |
| `PUT /livros/12` | `200` ou `404` | sim |
| `DELETE /livros/12` | `204` ou `404` | sim |
| `GET /livros/12/exemplares` | `200` com a lista | sim |
| `POST /emprestimos` | `201`, `409` ou `422` | não |
| `POST /emprestimos/7/devolucao` | `201` ou `409` | não |
| `POST /leitores/47/renovacoes` | `201` ou `409` | não |
| `GET /leitores/47/emprestimos` | `200` com a lista | sim |

Tabela: Dez linhas cobrem o sistema inteiro. Nenhuma delas tem verbo no
endereço, e as três últimas operações de circulação são substantivos que a
Vera já usa no balcão.

:::note Na sua carreira
O desenho da tabela acima leva quarenta minutos e economiza semanas — mas a
razão não é técnica.

Um endereço escrito depois do código carrega as decisões do código: o nome
da coluna, a ordem dos parâmetros, o que era fácil de consultar naquele dia.
Um endereço escrito antes carrega as decisões do **negócio**, e é por isso
que ele sobrevive à primeira troca de banco de dados.

Quando entrar num projeto que já tem API, peça essa tabela. Se ela não
existir, montá-la lendo as rotas é a melhor primeira semana que você pode
ter: ninguém conhece o sistema tão rápido quanto quem escreveu o índice
dele.
:::

:::summary
- Recurso é substantivo; coleção e item são dois endereços do mesmo
  substantivo.
- Aninhe quando a coisa não existe sozinha; filtre na consulta quando a
  combinação for imaginável com outro filtro.
- Seguro é não mudar nada; idempotente é poder repetir sem mudar o
  resultado. `POST` não é nenhum dos dois.
- `GET` que altera estado quebra a suposição de quem repete sozinho — e
  alguém sempre repete sozinho.
- Rede caindo depois do pedido é indistinguível de pedido não entregue:
  desenhe a operação idempotente ou aceite uma chave de idempotência.
- Ação que não é CRUD esconde um substantivo; criá-lo resolve o verbo, o
  identificador e o relatório de uma vez.
- `201` traz `Location`; `422` é conteúdo inválido; `409` é estado
  incompatível; `200` com erro dentro não existe.
- Acrescentar não quebra; renomear, remover, mudar tipo e mudar status
  quebram.
:::

:::checkpoint
Você desenha os endereços de um domínio a partir dos substantivos, classifica
cada operação como segura, idempotente ou nenhuma das duas, escolhe entre
`409` e `422` com argumento, e sabe dizer quais mudanças pode publicar sem
avisar ninguém.
:::

:::exercise level=1
Classifique cada operação em segura, idempotente ou nenhuma das duas:

1. `GET /livros/12`
2. `DELETE /reservas/88`
3. `POST /emprestimos`
4. `PUT /leitores/47`
5. `POST /emprestimos/7/renovacao`, definida como "prazo passa a ser hoje
   mais catorze dias"

:::answer
1. **Segura** (e portanto idempotente).
2. **Idempotente**, não segura. A segunda chamada devolve `404` e o estado
   continua o mesmo: a reserva não existe.
3. **Nenhuma das duas.** Cada chamada cria um empréstimo novo.
4. **Idempotente**, não segura. Mandar o leitor inteiro duas vezes grava o
   mesmo conteúdo.
5. **Idempotente**, não segura — e é o ponto do enunciado. A operação é
   `POST`, que por padrão não é idempotente, mas a **regra escolhida** a
   torna: definir o prazo dá o mesmo resultado em qualquer número de
   repetições, enquanto somar catorze dias não daria.

O caso 5 mostra que a idempotência não é propriedade do verbo: é
propriedade da regra. O verbo só diz o que o cliente pode supor quando não
conhece a regra.
:::

:::exercise level=2
A Vera pede três coisas novas. Desenhe o endereço e o verbo de cada uma, e
diga o status de sucesso e um status de recusa possível.

1. Marcar um exemplar como extraviado.
2. Listar os dez livros mais emprestados do mês.
3. Perdoar a multa de um empréstimo.

:::answer
**1. Marcar como extraviado.**

```text
POST /exemplares/2117/extravio      → 201, ou 409
```

É um acontecimento com data e responsável, não uma edição de campo. O `409`
cobre o exemplar que já está marcado como extraviado.

A alternativa `PATCH /exemplares/2117` com `{"estado": "extraviado"}`
funciona e perde duas coisas: a data do acontecimento e a possibilidade de
recusar transições inválidas com clareza.

**2. Os dez mais emprestados.**

```text
GET /livros?ordenar=emprestimos&periodo=2026-02&limite=10   → 200
```

Não é um recurso novo: é a coleção de livros, ordenada e filtrada. Um
endereço `/livros/mais-emprestados` seria a armadilha do filtro virando
recurso — no mês seguinte alguém quer os mais emprestados entre os
infantis.

Sem status de recusa óbvio; um período malformado devolve `422`.

**3. Perdoar a multa.**

```text
POST /multas/312/perdao      → 201, ou 409
```

O `409` é para a multa já paga: o pedido está correto e o estado não
permite. Perdão é um acontecimento que a prestação de contas do edital vai
querer listar separado — mais um substantivo que o negócio já tinha e o
código ainda não.
:::

:::exercise level=3
A API do acervo está publicada há três meses e tem dois consumidores: o
aplicativo do leitor, na loja, e uma planilha que a associação atualiza
sozinha.

Chega o pedido: `GET /livros` hoje devolve `ano` como número, e precisa
passar a devolver um objeto com `ano` e `edicao`.

Escreva o plano em quatro passos e diga o que você responderia a "não dá pra
só trocar?".

:::answer
**Passo 1 — acrescentar, não trocar.** A resposta passa a trazer `ano`
(inalterado) e um campo novo, `publicacao`, com o objeto. Ninguém quebra,
porque acrescentar campo é a única mudança segura.

**Passo 2 — medir quem usa o campo velho.** Registrar, por consumidor, quem
ainda lê `ano`. Sem esse número, o passo 4 vira discussão de opinião.

**Passo 3 — anunciar com data.** Avisar os dois consumidores de que `ano`
sai numa data específica, com pelo menos um ciclo de atualização de
aplicativo de folga. Marcar o campo como obsoleto na documentação, não só
no e-mail.

**Passo 4 — remover depois que o número zerar**, e não na data anunciada se
ele não tiver zerado. A data é um compromisso com quem se adaptou; o número
é a realidade.

**"Não dá pra só trocar?"** Dá, e o custo tem endereço: todo telefone com a
versão publicada hoje passa a mostrar o ano em branco, ou a travar na tela
de detalhe, dependendo de como o aplicativo lida com um campo que virou
objeto. Eles não atualizam porque a gente pediu — atualizam quando a loja
empurra, e parte deles nunca.

A planilha da associação é pior, porque ninguém a mantém: ela vai parar de
funcionar numa terça e a Vera vai ligar na quinta.

O acréscimo custa um campo a mais na resposta por alguns meses. A troca
direta custa uma janela em que o produto está quebrado para uma fatia de
usuários que você não consegue nem contar.
:::
