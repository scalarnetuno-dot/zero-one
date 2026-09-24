---
title: "Documentação da API"
number: 50
slug: documentacao-da-api
part: p11
kicker: "A integração do aplicativo levou três semanas. A única documentação da API era uma frase: \"pergunta pro Dedé\"."
goal: >-
  Publicar uma documentação que nasce do código e por isso não
  desatualiza: um esquema OpenAPI gerado das rotas, dos Form Requests e dos
  resources, com os erros descritos, exemplos executáveis, e um plano
  escrito para tirar um campo do ar sem quebrar quem o usa.
---

:::story Pergunta pro Dedé
O aplicativo do leitor não era feito pela Vertexo. A associação tinha
conseguido, por outro edital, um estúdio pequeno de Recife que fazia
aplicativos para ONG. Eles tinham uma desenvolvedora, a Lívia, e três
semanas.

No primeiro dia, a Lívia mandou um e-mail educado perguntando pela
documentação da API. Márcia encaminhou para o Dedé. Dedé respondeu com o
endereço de homologação e a frase "qualquer dúvida, me chama".

No segundo dia, a Lívia chamou. Queria saber o formato do `POST
/emprestimos`. Dedé explicou. No terceiro, queria saber por que o `422`
tinha `errors` e o `409` não tinha. Dedé explicou que estava mudando. No
quinto, queria saber se `devolver_ate` vinha com hora. Dedé não lembrava e
foi olhar.

Na segunda semana, a Lívia mandou uma planilha. Tinha quarenta e uma
linhas, uma por rota que ela tinha descoberto testando, com o que achava
que cada uma recebia e devolvia. Onze estavam erradas. Três eram rotas que
o Dedé tinha apagado na semana anterior.

— Ela fez a documentação — disse Tainá, olhando a planilha.

— Ela fez a documentação da API que existia terça passada — disse Dedé.

Márcia apareceu na porta.

— O estúdio diz que o atraso é por causa da nossa API.

— É — disse Dedé.

— Como assim, é?

— Ela está certa. Toda vez que eu mudo alguma coisa, ela descobre
testando.
:::

## Documentação que não nasce do código começa a mentir

A planilha da Lívia é o destino de toda documentação escrita à mão sobre
uma API que muda. No dia em que é escrita, está certa. Na semana seguinte,
uma rota muda de nome, um campo ganha um formato, uma validação nova
aparece — e ninguém lembra de atualizar o documento, porque o documento
não está no mesmo lugar que o código e ninguém é avisado quando os dois
divergem.

A documentação num wiki, num PDF, numa página do Notion tem o mesmo
defeito do número guardado do capítulo @cap:o-que-vamos-construir: é uma
cópia de algo que já existe em outro lugar, e cópia diverge.

A saída é a mesma: não guardar a cópia. **Gerar** a documentação a partir
do que já existe — as rotas, os Form Requests, os resources — de forma que
mudar o código mude o documento, sem que ninguém precise lembrar.

## OpenAPI: o esquema que gera tudo o mais

Existe um formato padrão para descrever uma API HTTP, e ele se chama
OpenAPI. É um arquivo JSON ou YAML com cada rota, o que ela recebe, o que
devolve em cada status, e os formatos de cada objeto:

```yaml
paths:
  /api/emprestimos:
    post:
      summary: Realiza um empréstimo
      security: [{ bearer: [] }]
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [exemplar_id, leitor_id]
              properties:
                exemplar_id: { type: integer }
                leitor_id: { type: integer }
      responses:
        '201':
          description: Empréstimo criado
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Emprestimo' }
        '409':
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Erro' }
```

O arquivo é verboso e ninguém deveria escrevê-lo à mão. O valor dele está
no que se faz **a partir** dele:

- uma página navegável, com cada rota, cada campo e um botão para testar;
- clientes gerados automaticamente para o aplicativo — em Kotlin, Swift,
  TypeScript —, com os tipos certos;
- validação automática, na suíte de testes, de que as respostas reais
  seguem o esquema.

O esquema é o contrato do capítulo @cap:o-que-e-uma-api-rest, num formato
que as máquinas leem.

## Gerar a partir das rotas, requests e resources

Existem duas famílias de ferramenta em PHP para produzir o OpenAPI.

**Anotações no código.** Você escreve, em atributos PHP em cima de cada
método, a descrição da rota. A ferramenta lê os atributos e monta o
esquema. O esquema fica preciso e tão atualizado quanto os atributos — que
são, de novo, uma cópia escrita à mão, agora mais perto do código.

**Inferência.** A ferramenta lê o próprio código — a rota, o tipo do Form
Request e as regras dele, o resource que o método devolve — e deduz o
esquema. O Scramble é a mais usada no ecossistema Laravel:

```text
$ composer require dedoc/scramble
```

Sem nenhuma outra linha, a rota `/docs/api` passa a existir em
desenvolvimento, e `/docs/api.json` devolve o esquema. Ele lê:

| De onde | O que deduz |
|---|---|
| `routes/api.php` | os caminhos e os verbos |
| o Form Request | os campos de entrada, tipos, obrigatórios |
| `Rule::enum` | a lista de valores aceitos |
| o `JsonResource` | os campos da resposta |
| `auth:sanctum` | que a rota exige token |
| `abort`, exceções e o Form Request | os status de erro possíveis |

Tabela: Tudo que este livro escreveu com cuidado nos últimos treze
capítulos vira, de graça, documentação — e é por ter sido escrito com
cuidado que ela sai certa.

Repare no efeito colateral. O `validated()` e o `JsonResource` foram
defendidos, nos capítulos @cap:validation-e-form-requests e
@cap:api-resources, por segurança e por contrato. Eles são também o que
permite a documentação ser inferida: um controller que faz
`$request->all()` e `return $model` não diz nada que uma ferramenta possa
ler.

A inferência não adivinha tudo. O que ela não deduz, você acrescenta — e o
lugar certo é o docblock do método, que fica ao lado do código:

```php title="app/Http/Controllers/EmprestimoController.php" numbered
/**
 * Realiza um empréstimo.
 *
 * Só a equipe empresta; o leitor não empresta para si
 * mesmo pelo aplicativo. O prazo depende do perfil do
 * leitor e é informado em `devolver_ate`.
 */
public function store(
    RealizarEmprestimoRequest $request,
    EmprestimoService $emprestimos,
) {
    // ...
}
```

O texto aparece na página, junto do que foi inferido. É o único pedaço
escrito à mão, e está a três linhas do código que descreve.

## Documentar o erro é documentar metade do contrato

A documentação que só mostra o caminho feliz é a mais comum e é metade do
contrato. A Lívia não perguntou três vezes sobre o `201`. Perguntou sobre o
`422`, o `409`, o que vem quando o token expira.

O formato único do capítulo @cap:erros-padronizados entra no esquema como
um componente. O Scramble aceita um gancho, registrado no provider, que
recebe o esquema depois de gerado e permite acrescentar o que a inferência
não viu. O resultado, no `openapi.json`, é este:

```yaml
components:
  schemas:
    Erro:
      type: object
      required: [tipo, mensagem]
      properties:
        tipo: { type: string }
        mensagem: { type: string }
        campos:
          type: object
          nullable: true
          additionalProperties:
            type: array
            items: { type: string }
        incidente: { type: string, nullable: true }
```

Toda resposta de erro de toda rota aponta para ele, e o cliente gerado a
partir do esquema ganha uma classe `Erro` com os quatro campos tipados.

E cada `tipo` possível ganha uma linha numa tabela, que é a parte da
documentação que o aplicativo mais consulta:

| `tipo` | Status | O aplicativo deve |
|---|---|---|
| `nao-autenticado` | `401` | levar ao login |
| `sem-permissao` | `403` | mostrar "sem permissão" |
| `nao-encontrado` | `404` | mostrar "não encontrado" |
| `validacao` | `422` | destacar os `campos` |
| `exemplar-indisponivel` | `409` | oferecer a reserva |
| `limite-de-emprestimos` | `409` | listar o que devolver |
| `leitor-com-pendencia` | `409` | mostrar o valor e como pagar |
| `muitas-requisicoes` | `429` | esperar o `Retry-After` |
| `falha-interna` | `500` | mostrar o `incidente` |

Tabela: A tabela é escrita à mão, e é a exceção que confirma a regra: ela
muda só quando uma exceção de domínio nova aparece, e o teste da seção
seguinte acusa quando isso acontece.

## Exemplos que a pessoa clica e executa

A página que o Scramble gera tem, em cada rota, um botão para enviar uma
requisição de verdade, com um campo para o token. A Lívia, no primeiro
dia, teria digitado o token de homologação e testado cada rota pela página,
vendo o formato real da resposta — em vez de montar a planilha à mão.

Exemplos executáveis têm uma exigência: um ambiente onde executar seja
seguro. A página aponta para **homologação**, com a base de dados das
factories do capítulo @cap:migrations-seeders-e-factories, e com o
`EnviadorNoLog` do capítulo @cap:service-container — nenhum aviso sai para
um telefone de verdade quando alguém clica em "testar" no `POST
/emprestimos`.

### O teste que compara o esquema com a realidade

A documentação gerada do código pode ainda divergir do comportamento: o
resource declara um campo como inteiro, e um caminho raro do código devolve
texto. Uma última camada fecha isso — conferir, **nos testes de feature**,
que cada resposta obedece ao esquema publicado:

```php title="tests/Feature/ContratoTest.php" numbered
test('respostas seguem o esquema OpenAPI', function (
    string $metodo,
    string $rota,
    array $corpo,
    int $status,
) {
    $resposta = $this->actingAs(Usuario::factory()->admin()->create())
        ->json($metodo, $rota, $corpo)
        ->assertStatus($status);

    expect($resposta)->toMatchOpenApi(
        base_path('docs/openapi.json'),
    );
})->with('rotas-do-contrato');
```

O `toMatchOpenApi` aqui é uma expectativa própria do projeto, construída
sobre uma biblioteca de validação de OpenAPI: ela lê o esquema, acha a
rota e o status, e confere cada campo da resposta. O arquivo
`docs/openapi.json` é **gerado na esteira** e versionado — e uma mudança
nele aparece no *diff* da revisão de código, onde alguém pode perguntar se
aquela mudança quebra o aplicativo.

:::key
São três camadas, cada uma protegendo contra um tipo de mentira:

A **inferência** impede que a documentação esqueça uma rota ou um campo.

O **arquivo versionado** faz toda mudança de contrato aparecer na revisão.

O **teste de contrato** impede que o código faça algo diferente do que o
documento diz.
:::

## Versionar e marcar o que vai sair

O capítulo @cap:api-resources deixou um plano pela metade: `devolver_ate`,
que o aplicativo 1.0 lê como `DD/MM/AAAA`, precisa virar `AAAA-MM-DD`. O
campo novo `devolver_ate_iso` foi acrescentado ao lado. Falta a parte que a
documentação resolve: **avisar**.

```php title="app/Http/Resources/EmprestimoResource.php" numbered
return [
    // ...

    /**
     * @deprecated Formato DD/MM/AAAA. Use `devolver_ate_iso`.
     *             Sai em 30/06/2026.
     */
    'devolver_ate' => $this->devolver_ate->format('d/m/Y'),

    'devolver_ate_iso' => $this->devolver_ate->toDateString(),
];
```

O esquema passa a marcar o campo com `deprecated: true`, a página o mostra
riscado, e os clientes gerados a partir do esquema passam a emitir aviso de
compilação quando alguém usa o campo.

O plano inteiro, escrito na documentação e não na cabeça de ninguém:

| Data | O que acontece |
|---|---|
| 01/03 | `devolver_ate_iso` publicado; `devolver_ate` marcado |
| 01/03 a 30/06 | o log conta as requisições que ainda vêm da 1.0 |
| 01/06 | aviso no aplicativo 1.0: "atualize até 30/06" |
| 30/06 | `devolver_ate` passa a ter o formato ISO |
| 30/09 | `devolver_ate_iso` sai, depois de três meses marcado |

Tabela: Seis meses para trocar o formato de um campo. Parece muito, e é o
tempo que um aplicativo instalado num celular sem atualização automática
leva para sumir.

A API também avisa na própria resposta, para os clientes que não leem
documentação:

```text
Deprecation: @1740787200
Sunset: Tue, 30 Jun 2026 23:59:59 GMT
Link: </docs/api#devolver_ate>; rel="deprecation"
```

Os cabeçalhos `Deprecation` e `Sunset` são padronizados, e um cliente bem
escrito os registra no log. Um middleware de rota os acrescenta nas rotas
que devolvem o campo — uma aplicação direta do capítulo @cap:middleware.

## Expor ou não a documentação em produção

O Scramble, por padrão, só mostra a documentação em ambiente local. A
decisão de abrir em produção é da equipe, e depende de quem consome a API.

**A API é pública**, para qualquer um integrar: a documentação é pública
também. Esconder não protege nada — qualquer pessoa descobre as rotas
usando o aplicativo com um inspetor de rede.

**A API é de um cliente conhecido**, como o aplicativo do estúdio de
Recife: a documentação fica atrás de autenticação, acessível para quem
integra.

**A API tem rotas administrativas**: essas rotas **não** entram na
documentação pública, mesmo que o resto entre. Publicar
`/api/admin/leitores/exportar` num documento aberto é entregar o mapa de
onde procurar.

A Casa Amarela publica a documentação em homologação, com login, e gera
dois esquemas: um completo, para a equipe, e um só com as rotas do leitor,
para o estúdio.

:::note Na sua carreira
Documentação de API costuma ser vista como tarefa de fim de projeto, e é
por isso que ela chega tarde e desatualizada. Tratada como consequência do
código — gerada, versionada, testada —, ela deixa de ser uma tarefa.

E tem um efeito que pouca gente antecipa: ela muda a conversa com quem
consome a API. A Lívia deixa de perguntar e passa a apontar — "o esquema diz
inteiro e veio texto". Uma pergunta custa uma interrupção; um apontamento
contra um documento é um defeito com endereço. Quem publica a documentação
certa ganha, de graça, um testador externo que trabalha para o próprio
projeto.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  config/scramble.php            # dois esquemas: equipe e leitor
  docs/
    openapi.json                 # gerado na esteira, versionado
  app/Providers/
    AppServiceProvider.php       # componente Erro no esquema
  app/Http/Middleware/
    AvisaDepreciacao.php         # Deprecation, Sunset, Link
  tests/Feature/
    ContratoTest.php             # resposta real × esquema
:::

:::summary
- Documentação escrita à mão é uma cópia do código, e cópia diverge.
- OpenAPI descreve rotas, entradas, respostas e erros num formato que gera
  página, clientes e validação.
- Inferência lê rotas, Form Requests, `Rule::enum`, resources e middleware;
  o que o livro escreveu com cuidado vira documentação.
- `$request->all()` e `return $model` não documentam nada.
- O erro é metade do contrato: o componente `Erro` e a tabela de `tipo`
  descrevem o que o cliente deve fazer.
- Exemplos executáveis precisam de um ambiente em que executar seja
  seguro.
- O esquema versionado mostra mudanças de contrato na revisão; o teste de
  contrato confere a resposta real contra ele.
- Campo que sai é marcado, avisado por cabeçalho e retirado num plano com
  datas.
- Rotas administrativas não entram na documentação pública.
:::

:::checkpoint
A API da Casa Amarela tem `/docs` e `openapi.json` gerados do código, com
os erros e os seus `tipo` descritos, exemplos que se executam em
homologação, um teste que confere cada resposta contra o esquema, e um
plano com datas para trocar o formato de `devolver_ate` sem quebrar o
aplicativo 1.0.
:::

:::exercise level=1
Diga o que a ferramenta de inferência consegue deduzir sozinha e o que
precisa ser acrescentado à mão:

1. Que `POST /livros` exige `titulo`.
2. Que o leitor não pode criar empréstimo pelo aplicativo.
3. Que `estado` do exemplar aceita `bom`, `emprestado`, `restauro` e
   `extraviado`.
4. Que `devolver_ate` será retirado em 30/06.
5. Que o `409` de empréstimo pode ter o `tipo` `exemplar-indisponivel`.

:::answer
1. Sozinha, pelo `required` do `StoreLivroRequest`.
2. À mão, no docblock. A inferência vê o `authorize()` e sabe que pode
   haver `403`, mas não sabe **por que** nem para quem.
3. Sozinha, pelo `Rule::enum(StatusExemplar::class)` — e continua certa
   quando um caso novo entrar no enum.
4. À mão, no `@deprecated` do resource.
5. Parcialmente. A ferramenta sabe que a rota pode devolver `409` se a
   exceção for lançada de um jeito que ela consegue rastrear; a lista de
   `tipo` possíveis é a tabela escrita à mão.

O padrão: o que é **estrutura** a ferramenta deduz; o que é **intenção** —
por quê, para quem, até quando — precisa de uma frase.
:::

:::exercise level=2
O campo `assunto` do `LivroResource` vai virar o objeto
`assunto_detalhado`, como o capítulo @cap:api-resources planejou. Escreva:
o trecho do resource com a marcação, a tabela de datas do plano, e a
condição **medida** que autoriza o último passo.

:::answer
```php
/**
 * @deprecated Texto solto. Use `assunto_detalhado`.
 *             Sai em 31/10/2026.
 */
'assunto' => $this->assunto->nome,

'assunto_detalhado' => new AssuntoResource($this->assunto),
```

| Data | O que acontece |
|---|---|
| 01/05 | `assunto_detalhado` publicado; `assunto` marcado |
| 01/05 a 31/10 | cabeçalhos `Deprecation` e `Sunset` nas rotas |
| 01/09 | aviso no aplicativo às versões que leem `assunto` |
| 31/10 | `assunto` sai |

**A condição medida:** o log estruturado registra, a cada requisição, a
versão do aplicativo que veio no cabeçalho `X-App-Versao`. O último passo
só acontece se, nas duas semanas anteriores a 31/10, as versões que ainda
leem `assunto` somarem menos de, digamos, 1% das requisições — e se a Vera
concordar em avisar pessoalmente quem ainda estiver nelas.

Se o número não cair, a data muda. A data do plano é uma intenção; o que
autoriza a retirada é a medição.
:::

:::exercise level=3
O estúdio de Recife pediu que a API passe a ter versão no caminho —
`/api/v1/...` —, "porque é o padrão do mercado e facilita para a gente".
Hoje a API não tem versão no caminho.

Escreva a resposta ao estúdio: o que a versão no caminho resolve, o que ela
custa para a Casa Amarela, o que a equipe já faz no lugar dela, e em que
situação você aceitaria.

:::answer
**O que ela resolve.** Permite mudar o contrato de forma incompatível —
renomear, remover, mudar formato — mantendo a versão antiga no ar para
quem ainda depende dela. O cliente escolhe quando migrar, mudando uma
parte da URL.

**O que ela custa.** Para cada versão viva, as rotas, os controllers, os
resources e os testes existem em dobro, ou são compartilhados com `if` por
versão. Um defeito de segurança precisa ser corrigido em todas. E a
tentação de publicar a v2 "para arrumar tudo" costuma produzir uma v2 que
fica ao lado da v1 por anos.

**O que a equipe já faz no lugar dela.** Evolução compatível: campo novo
ao lado do antigo, marcação no esquema, cabeçalhos `Deprecation` e
`Sunset`, retirada com data e medição. Isso resolve as mudanças que a API
teve até hoje sem duplicar nada, e o esquema versionado no Git mostra
exatamente o que mudou e quando.

**Quando eu aceitaria.** Se aparecer uma mudança que não pode ser feita ao
lado — o modelo de reserva mudar de "por livro" para "por exemplar", por
exemplo, alterando o significado de metade das rotas. Aí a v2 é honesta: é
outro contrato.

**E o que eu ofereceria ao estúdio agora:** prefixar as rotas com `/api/v1`
**hoje**, sem criar nenhuma v2, como um endereço reservado. Não custa nada,
atende ao pedido, e deixa o caminho aberto para o dia em que uma mudança
incompatível realmente aparecer. O que eu recusaria é usar a versão no
caminho como substituto da disciplina de evolução compatível — porque a
disciplina continua necessária dentro de cada versão.
:::
