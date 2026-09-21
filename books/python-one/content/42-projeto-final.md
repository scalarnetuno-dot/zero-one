---
title: "Projeto final"
number: 42
slug: projeto-final
part: p10
kicker: "Agora sem mastigar: os requisitos, o prazo e o dia em que alguém de fora usa o que você fez."
goal: >-
  Construir sozinho um módulo completo a partir de requisitos, empacotar a
  aplicação em contêiner e colocá-la no ar com o que uma API de verdade
  exige.
---

O catálogo cresceu uma decisão por vez. Agora a Cooperativa entrega apenas
os requisitos, e você decide como transformar uma necessidade ambígua em um
módulo que possa ser mantido.

A Cooperativa Sabiá quer registrar as **entregas** dos produtores. Os
requisitos estão abaixo, escritos como um cliente escreve — com ambiguidade
e com omissão. Parte do trabalho é perceber o que falta e decidir.

## Os requisitos

> Todo dia chega caminhão de produtor. Hoje a gente anota numa ficha: quem
> trouxe, o que trouxe, quantas caixas e quem conferiu. Queria isso no
> sistema.
>
> A entrega entra como *pendente*. O pessoal do armazém confere e marca
> como *conferida*, dizendo quantas caixas realmente chegaram — às vezes
> vem menos, às vezes vem caixa estragada. Aí o estoque do produto sobe com
> a quantidade conferida.
>
> Se a conferência achar problema grave, a entrega é *recusada* e o estoque
> não sobe.
>
> Precisa dar para ver as entregas de um produtor num período, e o total de
> caixas que ele trouxe no mês. O produtor só vê as dele. O pessoal do
> armazém vê tudo e confere. Só administrador pode apagar.

## O que o texto não diz

Antes de escrever código, escreva as perguntas. Estas são as que eu faria —
e a última é a mais importante:

- Entrega conferida pode ser alterada depois? Recusada pode ser reaberta?
- A quantidade conferida pode ser **maior** que a informada?
- Uma entrega pode ter vários produtos, ou é um produto por entrega? *(o
  texto diz "o que trouxe", no singular, e fichas de armazém costumam ter
  várias linhas)*
- "Total do mês" é pela data da entrega ou pela data da conferência?
- Quem recusa precisa justificar?

:::key
Entregar o sistema com essas perguntas respondidas por você, em silêncio, é
o erro mais caro que um desenvolvedor comete — e o mais comum. Cada
suposição não declarada vira uma regra que ninguém aprovou e que vai
aparecer no fechamento do mês.
:::

Para este exercício, as respostas são: **uma entrega, vários itens**; conferida e
recusada são estados finais; a quantidade conferida pode ser maior, com
aviso; o total é pela data da entrega; e a recusa exige motivo.

## O modelo

:::diagram type="er" caption="Duas entidades novas, ligadas às três que já existiam."
columns: 2
entities:
  - name: "Entrega"
    fields: ["id (PK)", "produtor_id (FK)", "data", "status", "motivo_recusa", "conferida_por (FK)", "conferida_em"]
  - name: "ItemEntrega"
    fields: ["id (PK)", "entrega_id (FK)", "produto_id (FK)", "caixas_informadas", "caixas_conferidas"]
relations:
  - { from: "Entrega", to: "ItemEntrega", label: "1:N" }
:::

```python title="app/models/entrega.py" numbered
class StatusEntrega(str, Enum):
    PENDENTE = "pendente"
    CONFERIDA = "conferida"
    RECUSADA = "recusada"


class Entrega(Base):
    __tablename__ = "entrega"

    id: Mapped[int] = mapped_column(primary_key=True)
    produtor_id: Mapped[int] = mapped_column(
        ForeignKey("produtor.id"), index=True
    )
    data: Mapped[date] = mapped_column(index=True)
    status: Mapped[StatusEntrega] = mapped_column(
        default=StatusEntrega.PENDENTE, index=True
    )
    motivo_recusa: Mapped[str | None] = mapped_column(
        String(300), default=None
    )
    conferida_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id"), default=None
    )
    conferida_em: Mapped[datetime | None] = mapped_column(
        default=None
    )
    itens: Mapped[list["ItemEntrega"]] = relationship(
        back_populates="entrega", cascade="all, delete-orphan"
    )
```

## Ordem de construção

Uma ordem possível, que mantém as dependências visíveis:

1. **Modelos e migração** — capítulos @cap:sqlalchemy e @cap:migrations.
2. **Esquemas** de entrada, conferência e saída — capítulo @cap:schemas.
3. **Repositório**, com a consulta por produtor e período — capítulos
   @cap:repository e @cap:filtros-e-buscas.
4. **Serviço**, com a máquina de estados e a transação — capítulo
   @cap:service.
5. **Rotas**, com paginação e permissões — capítulos @cap:paginacao e
   @cap:usuarios-e-permissoes.
6. **Testes** nas três faixas — Parte 8.

O passo 4 é o coração, e ele tem um detalhe que o texto do cliente esconde:

```python title="app/services/entrega.py" numbered
def conferir(
    self, entrega_id: int, itens: dict[int, int],
    usuario: Usuario,
) -> Entrega:
    entrega = self.session.get(
      Entrega, entrega_id, with_for_update=True
    )
    if entrega is None:
      raise EntregaNaoEncontrada(entrega_id)

    if entrega.status is not StatusEntrega.PENDENTE:
        raise EntregaJaFinalizada(entrega.id, entrega.status)

    for item in entrega.itens:
        if item.id not in itens:
            raise ItemNaoConferido(item.id)
        item.caixas_conferidas = itens[item.id]

    for item in entrega.itens:
        produto = self.repo_produto.buscar(item.produto_id)
        produto.estoque += item.caixas_conferidas

    entrega.status = StatusEntrega.CONFERIDA
    entrega.conferida_por = usuario.id
    entrega.conferida_em = datetime.now(timezone.utc)

    self.session.commit()
    return entrega
```

A verificação de estado **antes de tudo** é o que impede a conferência
dupla: sem ela, chamar a rota duas vezes soma o estoque duas vezes. É o
mesmo cuidado do capítulo @cap:primeira-api sobre concorrência, agora com
consequência em caixas de tomate.

:::pitfall
Percorrer os itens duas vezes é deliberado. Se o estoque subisse no mesmo
laço que valida, uma falha no quinto item deixaria quatro produtos já
somados — e, embora a transação desfaça o banco, o objeto em memória fica
inconsistente e o log de auditoria já foi escrito. Valide tudo, depois
altere tudo.
:::

## Empacotando

```text title="Dockerfile"
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY migracoes ./migracoes
COPY alembic.ini .
COPY entrypoint.sh .

RUN useradd -m app && chmod +x entrypoint.sh && chown -R app:app /app
USER app

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
```

Quatro decisões que valem nome.

`requirements.txt` é copiado **antes** do código. As camadas do Docker são
cacheadas em ordem: com essa separação, alterar uma linha de Python não
refaz a instalação das dependências.

`PYTHONUNBUFFERED=1` faz o log sair na hora. Sem ele, a saída fica num buffer
e as mensagens aparecem em blocos atrasados — ou somem, se o processo morrer.

`USER app` tira o processo do `root`. Um contêiner comprometido rodando como
`root` é um problema muito maior que um rodando como usuário comum.

E `--host 0.0.0.0`, porque o padrão `127.0.0.1` só aceita conexões de dentro
do próprio contêiner — o que faz a aplicação subir perfeitamente e não
responder a ninguém.

```text title="compose.yaml"
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: >-
        postgresql+psycopg://catalogo:${POSTGRES_PASSWORD}@db/catalogo
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      db: {condition: service_healthy}

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: catalogo
      POSTGRES_PASSWORD: >-
        ${POSTGRES_PASSWORD:?defina POSTGRES_PASSWORD}
      POSTGRES_DB: catalogo
    volumes: ["dados:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U catalogo"]
      interval: 5s
      retries: 10

volumes:
  dados:
```

:::warning
Sem o `volumes:` no serviço do banco, os dados vivem dentro do contêiner e
somem com ele. `docker compose down` apaga o catálogo inteiro, e a pessoa
que rodou o comando não tem como saber que isso ia acontecer. Volume nomeado
é a diferença entre reiniciar e recomeçar.
:::

## Subir com as migrações

```text title="entrypoint.sh"
#!/bin/sh
set -e
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`set -e` aborta se a migração falhar — melhor não subir do que subir com o
esquema errado. E `exec` substitui o processo do shell pelo do servidor,
para que ele receba diretamente o sinal de encerramento do orquestrador.

:::pitfall
Com vários contêineres, todos rodam esse script ao mesmo tempo. O Alembic
toma uma trava no banco e os demais esperam — funciona, e não é o desenho
recomendado. Em produção séria, a migração é um passo **separado** da
implantação, executado uma vez, antes de a nova versão entrar no ar.
:::

## A rota de saúde, agora a sério

```python title="app/routers/saude.py" numbered
@router.get("/saude")
def vivo():
    return {"status": "de pé"}


@router.get("/pronto")
def pronto(session: SessaoDep):
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(503, "banco indisponível")
    return {"status": "pronto"}
```

Duas rotas, dois propósitos. `/saude` diz se o processo está vivo — se ela
falhar, reiniciar resolve. `/pronto` diz se ele consegue atender — se o banco
caiu, reiniciar **não** resolve, e o orquestrador deve tirar a instância do
balanceador sem matá-la.

Confundir as duas produz o pior comportamento possível: o banco oscila e o
orquestrador entra num ciclo de reinícios que só piora a situação.

## Log em produção

```python title="app/log.py" numbered
import logging
import sys


def configurar_log(nivel: str = "INFO") -> None:
    logging.basicConfig(
        level=nivel,
        stream=sys.stdout,
        format=(
            '{"hora":"%(asctime)s","nivel":"%(levelname)s",'
            '"origem":"%(name)s","msg":"%(message)s"}'
        ),
    )
```

Log vai para a **saída padrão**, não para arquivo: quem coleta, arquiva e
roda é o ambiente, não a aplicação. E em formato estruturado, porque
ninguém procura com expressão regular num volume de verdade.

:::warning
Nunca registre senha, token, corpo de requisição de autenticação ou dado
pessoal. O log é lido por mais gente que o banco, é copiado para ferramentas
de terceiros e costuma ter retenção longa. Um token num log é um token
vazado com data de validade muito maior que a dele.
:::

## A lista antes de publicar

| | Item |
|---|---|
| ☐ | `SECRET_KEY` gerada, fora do repositório, diferente da de teste |
| ☐ | HTTPS na frente, sem exceção |
| ☐ | CORS com as origens listadas, sem `*` |
| ☐ | migrações aplicadas como passo separado |
| ☐ | `/docs` fechada, se a API é interna |
| ☐ | `echo=False` no engine |
| ☐ | cópia de segurança do banco **testada** com restauração |
| ☐ | log estruturado, sem dado sensível |
| ☐ | limite de tamanho de página e de corpo de requisição |
| ☐ | `/pronto` ligada ao balanceador |

Tabela: A sétima linha é a que mais falha na hora certa: cópia de segurança
que nunca foi restaurada é um arquivo, não uma cópia de segurança.

## O ciclo se fecha

:::story A ficha na parede
Dona Neuza levou a última ficha de papel para a reunião. Estava rasurada em
dois lugares, com um número riscado e outro escrito por cima.

— Essa é de terça — ela disse. — O Onofre trouxe doze e chegaram dez. Quem
riscou fui eu, e eu não lembro por quê.

Bia abriu a tela de entregas no projetor. A de terça estava lá: doze
informadas, dez conferidas, conferida por Rafa, às 8h14.

— E o motivo?

— Tem um campo. — Bia clicou. *Duas caixas com fruta machucada, devolvidas
ao produtor.*

Dona Neuza leu duas vezes. Depois dobrou a ficha ao meio e guardou no bolso
do avental.

— Guarda essa aí — disse Rafa. — É a última.

— É por isso que eu vou guardar.
:::

:::art caption="O ciclo se fecha quando você vira a pessoa que responde a pergunta."
Charge editorial minimalista em fundo branco: uma coordenadora de armazém
mais velha, de avental, segurando uma ficha de papel amassada na mão
esquerda, enquanto olha para uma tela onde a mesma informação aparece
organizada em colunas. Ao lado dela, de pé, uma desenvolvedora com as mãos
nos bolsos, sem apontar nada, apenas observando a reação. Ao fundo, um
armazém com engradados empilhados. Poucos elementos, humor seco e afetuoso,
estética de revista de tecnologia.
:::

## Fora do escopo, por enquanto

Este livro acaba com uma API no ar. O que ele não cobriu, e que existe:

- **Tarefas em segundo plano** — relatórios pesados, e-mail, importação em
  lote. Comece por `BackgroundTasks` do próprio FastAPI; cresça para Celery
  ou ARQ quando precisar de reprocessamento e agendamento.
- **Cache** — Redis na frente de consultas caras, com a pergunta difícil de
  sempre: quando invalidar.
- **Observabilidade** — métricas e rastreamento distribuído. Log responde
  "o que aconteceu"; métrica responde "com que frequência"; rastreamento
  responde "onde foi o tempo".
- **Eventos** — quando a cooperativa tiver um segundo sistema, e os dois
  precisarem concordar sem um chamar o outro.

Nenhum deles precisa entrar por prestígio. Cada um deve nascer de um problema
observável: entender a necessidade, escolher onde a decisão mora e escrever o
teste que garante que ela continua valendo amanhã.

:::summary
- Requisito de cliente tem ambiguidade; as perguntas vêm antes do código.
- Máquina de estados verifica o estado antes de agir — é o que impede a
  operação dupla.
- Valide todos os itens, depois altere todos.
- No contêiner: dependências antes do código, log sem buffer, usuário não
  privilegiado, `--host 0.0.0.0`.
- Migração é passo separado da implantação.
- `/saude` e `/pronto` respondem perguntas diferentes.
- Cópia de segurança que nunca foi restaurada não é cópia de segurança.
:::

:::milestone
Acabou. Você começou no `print` e terminou com uma API tipada, testada,
versionada, documentada e no ar — feita de decisões que você consegue
justificar uma a uma. É exatamente isso que separa quem programa de quem
copia.
:::

:::exercise level=1
Implemente o modelo `Entrega` e `ItemEntrega`, gere a migração e confira o
arquivo gerado antes de aplicá-la.

:::answer
```python
class ItemEntrega(Base):
    __tablename__ = "item_entrega"

    id: Mapped[int] = mapped_column(primary_key=True)
    entrega_id: Mapped[int] = mapped_column(
        ForeignKey("entrega.id"), index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produto.id"), index=True
    )
    caixas_informadas: Mapped[int]
    caixas_conferidas: Mapped[int | None] = mapped_column(
        default=None
    )
    entrega: Mapped["Entrega"] = relationship(
        back_populates="itens"
    )
```
`caixas_conferidas` é anulável de propósito: `None` significa "ainda não
conferido", que é diferente de "conferido, zero caixas". É a distinção do
capítulo @cap:variaveis-e-tipos com consequência em dinheiro.
:::

:::exercise level=2
Escreva os testes de serviço da conferência: caminho feliz, entrega já
conferida e item faltando na conferência.

:::answer
```python
def test_conferir_soma_o_estoque(servico, entrega):
    servico.conferir(entrega.id, {1: 10}, usuario_operador)

    assert servico.repo_produto.buscar(1).estoque == 110


def test_nao_confere_duas_vezes(servico, entrega):
    servico.conferir(entrega.id, {1: 10}, usuario_operador)

    with pytest.raises(EntregaJaFinalizada):
        servico.conferir(entrega.id, {1: 10}, usuario_operador)

    assert servico.repo_produto.buscar(1).estoque == 110


def test_item_faltando_recusa_a_conferencia(servico, entrega):
    with pytest.raises(ItemNaoConferido):
        servico.conferir(entrega.id, {}, usuario_operador)

    assert servico.repo_produto.buscar(1).estoque == 100
```
O terceiro teste é o mais importante dos três: ele verifica que a operação
recusada **não deixou rastro**. Sem essa afirmação, uma implementação que
soma o estoque antes de validar passaria nos dois primeiros.
:::

:::exercise level=3
A cooperativa decidiu que a entrega recusada pode ser reaberta pelo
administrador, "porque às vezes a recusa foi engano". Descreva o impacto
dessa frase no que você construiu.

:::answer
A frase parece pequena e muda a natureza da entidade. Três consequências.

**A máquina de estados deixa de ter estados finais.** `RECUSADA` volta a ser
`PENDENTE`, o que exige revisar toda condição escrita como "já finalizada".
E abre uma pergunta que a frase não responde: a conferida também pode ser
reaberta? Se não, por que uma sim e outra não — sendo que o engano é igual
de provável nas duas?

**O estoque passa a ter um caminho de volta.** Se a conferida for reabrível,
reabrir precisa **subtrair** o que foi somado — e subtrair pode deixar o
estoque negativo, porque o produto já pode ter sido vendido. Esse caso
precisa de uma decisão do negócio: recusar a reabertura, permitir negativo,
ou gerar um ajuste de acerto. Nenhuma das três é óbvia, e nenhuma é do
desenvolvedor.

**O estado atual deixa de contar a história.** Hoje a entrega tem um status;
depois da reabertura, ela terá tido vários, e a pergunta "por que essa
entrega foi recusada em março se ela está conferida?" não tem onde ser
respondida. Isso pede uma tabela de eventos:

```python
class EventoEntrega(Base):
    __tablename__ = "evento_entrega"

    id: Mapped[int] = mapped_column(primary_key=True)
    entrega_id: Mapped[int] = mapped_column(
        ForeignKey("entrega.id"), index=True
    )
    de: Mapped[StatusEntrega | None]
    para: Mapped[StatusEntrega]
    motivo: Mapped[str | None]
    por: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    em: Mapped[datetime]
```

E é aqui que está a lição final do livro. A frase do cliente tinha catorze
palavras. A resposta honesta a ela não é "feito, uma linha" — é uma pergunta
de volta sobre o estoque, uma decisão registrada por escrito, e uma tabela
nova. Saber disso, e conseguir explicar por quê em três frases que a Dona
Neuza entenda, é o que este livro inteiro tentou ensinar.
:::
