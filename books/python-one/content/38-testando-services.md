---
title: "Testando serviços"
number: 38
slug: testando-services
part: p8
kicker: "As regras da cooperativa não precisam de banco para serem verdadeiras — nem para serem testadas."
goal: >-
  Testar a camada de serviço com dublês, escolher entre falso e simulacro,
  e escrever testes de regra que rodam em milissegundos.
---

A camada de serviço do capítulo @cap:service concentra as decisões: preço
mínimo, estoque suficiente, nome duplicado, papel autorizado. É a camada
mais importante de testar — e, graças ao `Protocol` do capítulo
@cap:repository, a mais fácil.

## O falso

```python title="tests/dublês.py" numbered
class RepositorioFalso:
    def __init__(self, inicial: list[Produto] | None = None):
        self._dados: dict[int, Produto] = {}
        self._proximo = 1
        for p in inicial or []:
            self.criar(p)

    def buscar(self, produto_id: int) -> Produto | None:
        return self._dados.get(produto_id)

    def buscar_por_nome(self, nome: str) -> Produto | None:
        for p in self._dados.values():
            if p.nome == nome:
                return p
        return None

    def listar(self, limite=20, deslocamento=0) -> list[Produto]:
        todos = sorted(self._dados.values(), key=lambda p: p.nome)
        return todos[deslocamento : deslocamento + limite]

    def criar(self, produto: Produto) -> Produto:
        produto.id = self._proximo
        self._dados[produto.id] = produto
        self._proximo += 1
        return produto

    def remover(self, produto: Produto) -> None:
        self._dados.pop(produto.id, None)
```

```python title="tests/test_servico_produto.py" numbered
class SessaoFalsa:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


@pytest.fixture
def servico():
    return ProdutoServico(SessaoFalsa(), RepositorioFalso())
```

```python title="os testes" numbered
def test_criar_produto_devolve_com_id(servico):
    produto = servico.criar("Tomate", Decimal("8.90"), 100)

    assert produto.id == 1
    assert produto.nome == "Tomate"


def test_nao_aceita_nome_repetido(servico):
    servico.criar("Tomate", Decimal("8.90"), 100)

    with pytest.raises(ProdutoJaExiste):
        servico.criar("Tomate", Decimal("9.10"), 20)


def test_nome_e_normalizado_antes_da_comparacao(servico):
    servico.criar("Tomate   italiano", Decimal("8.90"), 1)

    with pytest.raises(ProdutoJaExiste):
        servico.criar("  Tomate italiano  ", Decimal("9.10"), 1)
```

```text
$ pytest tests/test_servico_produto.py
3 passed in 0.04s
```

Quatro centésimos de segundo, sem PostgreSQL instalado, sem migração, sem
rede. Esses testes rodam a cada `Ctrl+S` se você quiser — e é essa
velocidade que faz a diferença entre um teste que se executa e um que se
adia.

:::key
Esses testes só são possíveis porque o serviço recebe o repositório pelo
construtor. Se ele criasse a própria sessão, ou importasse `SessionLocal`
diretamente, não haveria onde encaixar o falso. O desenho do capítulo
@cap:dependency-injection não era formalidade — era isto.
:::

## Os tipos de dublê

| Nome | O que é | Quando usar |
|---|---|---|
| Falso (*fake*) | implementação simplificada que funciona | repositório, cache |
| Esboço (*stub*) | devolve resposta fixa | consulta externa |
| Espião (*spy*) | registra o que foi chamado | verificar envio de e-mail |
| Simulacro (*mock*) | espião com expectativas declaradas | último recurso |
| Boneco (*dummy*) | só preenche um parâmetro | argumento não usado |

Tabela: Os nomes vêm do vocabulário de Gerard Meszaros e valem porque
descrevem intenções diferentes — não porque a distinção seja rígida.

:::key
Prefira o **falso**. Ele é código de verdade, com comportamento de verdade,
e um teste escrito sobre ele verifica resultado. O simulacro verifica
**chamadas** — e um teste que afirma "o método X foi chamado com Y" quebra
quando você renomeia o método, mesmo que o comportamento esteja idêntico.
:::

## Quando o simulacro é a resposta certa

```python title="tests/test_notificacao.py" numbered
from unittest.mock import Mock


def test_avisa_o_produtor_quando_o_estoque_zera():
    notificador = Mock()
    servico = ProdutoServico(
        SessaoFalsa(),
        RepositorioFalso(),
        notificador=notificador,
    )
    produto = servico.criar("Tomate", Decimal("8.90"), 10)

    servico.vender(produto.id, 10)

    notificador.enviar.assert_called_once()
    (destinatario, mensagem), _ = notificador.enviar.call_args
    assert "Tomate" in mensagem
```

Aqui o simulacro é adequado porque o **efeito é a chamada**: o resultado
observável de "avisar o produtor" é que uma mensagem saiu. Não há estado
para inspecionar.

:::pitfall
`Mock()` aceita qualquer método. `notificador.enviarr(...)` — com dois
erres — funciona, não dá erro e o teste passa, verificando um método que não
existe. Use `Mock(spec=Notificador)` ou `create_autospec`: aí o simulacro
recusa o que a interface real não tem.
:::

## Testar o que o serviço decide, não como

```python title="fragil_vs_solido.py" numbered
# frágil: verifica como
def test_ruim(servico, repo):
    servico.criar("Tomate", Decimal("8.90"), 1)
    repo.buscar_por_nome.assert_called_once_with("Tomate")


# sólido: verifica o quê
def test_bom(servico):
    servico.criar("Tomate", Decimal("8.90"), 1)
    with pytest.raises(ProdutoJaExiste):
        servico.criar("Tomate", Decimal("9.10"), 1)
```

O primeiro quebra se você trocar `buscar_por_nome` por uma consulta com
índice único. O segundo continua passando — porque a regra continua valendo,
e a regra era o assunto.

## Testando o tempo e o acaso

```python title="tempo.py" numbered
def test_promocao_expira(monkeypatch):
    congelado = datetime(2026, 3, 14, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "app.services.produto.agora", lambda: congelado
    )
    ...
```

Melhor ainda é não precisar do remendo: uma função `agora()` injetada como
dependência permite que o teste passe a data que quiser, sem
`monkeypatch`.

```python
class ProdutoServico:
    def __init__(self, session, repo, agora=None):
        self.agora = agora or (
            lambda: datetime.now(timezone.utc)
        )
```

:::key
Tudo que é imprevisível — hora, número aleatório, identificador gerado,
chamada de rede — deve entrar por parâmetro. Um teste que depende do relógio
falha sozinho às onze da noite da virada do mês, e a pessoa que investiga
não faz ideia do porquê.
:::

## A pirâmide

:::diagram type="blocks" caption="Muitos testes rápidos embaixo, poucos e caros em cima."
rows:
  - [{ text: "ponta a ponta", note: "poucos · lentos · frágeis" }]
  - [{ text: "integração (API e banco)", note: "alguns · médios" }]
  - [{ text: "unidade (serviço e domínio)", note: "muitos · milissegundos" }]
:::

Os capítulos @cap:testando-a-api e @cap:testando-o-banco tratam das duas
faixas de cima. A de baixo é onde mora o volume — e ela é barata justamente
porque não toca em nada de fora.

:::summary
- O serviço se testa com um repositório falso, em milissegundos.
- Isso só é possível porque as dependências entram pelo construtor.
- Prefira falso a simulacro; simulacro verifica chamada, e chamada muda.
- `Mock(spec=...)` impede o teste de verificar um método inexistente.
- Verifique o que o serviço decide, não como ele chegou lá.
- Hora, acaso e rede entram por parâmetro.
:::

:::checkpoint
Você testa regras de negócio sem banco, escolhe o dublê pelo tipo de efeito
que precisa observar, e escreve testes que sobrevivem a refatoração.
:::

:::exercise level=1
Escreva os testes de `vender`: o caminho feliz e o de estoque insuficiente.

:::answer
```python
def test_vender_reduz_o_estoque(servico):
    p = servico.criar("Tomate", Decimal("8.90"), 100)

    servico.vender(p.id, 30)

    assert servico.buscar(p.id).estoque == 70


def test_vender_alem_do_estoque_e_recusado(servico):
    p = servico.criar("Tomate", Decimal("8.90"), 10)

    with pytest.raises(EstoqueInsuficiente) as erro:
        servico.vender(p.id, 30)

    assert erro.value.disponivel == 10
    assert servico.buscar(p.id).estoque == 10
```
:::

:::exercise level=2
Escreva o teste que garante que o serviço **não** confirma a transação
quando a operação falha.

:::answer
```python
def test_falha_nao_confirma_transacao():
    sessao = SessaoFalsa()
    servico = ProdutoServico(sessao, RepositorioFalso())
    p = servico.criar("Tomate", Decimal("8.90"), 10)
    commits_antes = sessao.commits

    with pytest.raises(EstoqueInsuficiente):
        servico.vender(p.id, 30)

    assert sessao.commits == commits_antes
```
Contar os `commit` é exatamente o tipo de verificação de **como** que o
capítulo desaconselha — e aqui é justificado, porque a fronteira da
transação é a regra, não um detalhe de implementação. A exceção à regra
existe quando o "como" **é** o comportamento.
:::

:::exercise level=3
O serviço passou a chamar uma API externa de cotação para converter preços.
Descreva como testá-lo, listando o que você testaria com dublê e o que não
testaria assim.

:::answer
A chamada externa entra por dependência, com um protocolo:

```python
class Cotacao(Protocol):
    def dolar_hoje(self) -> Decimal: ...


class CotacaoFixa:
    def __init__(self, valor: Decimal):
        self.valor = valor

    def dolar_hoje(self) -> Decimal:
        return self.valor
```

**Com dublê eu testaria:** a conversão com um valor conhecido; o
arredondamento nas bordas; o comportamento quando a cotação vem zero ou
negativa; e — o mais importante — o que acontece quando a chamada **falha**,
com um dublê que levanta exceção. Um serviço que fica sem cotação precisa ter
uma decisão escrita: recusar a operação, usar a última conhecida, ou usar um
padrão. Essa decisão é regra de negócio e merece teste.

**Com dublê eu não testaria:** que a API externa responde no formato
esperado. Isso é uma suposição sobre um sistema de terceiros, e um dublê que
a reproduz é apenas a minha suposição testando a si mesma — ela continua
passando no dia em que o fornecedor mudar o campo de `valor` para `rate`.

Para essa parte existem dois instrumentos diferentes: um **teste de
contrato**, que roda contra o serviço real fora do conjunto principal
(diariamente, ou na esteira noturna), e um **monitor em produção**, que
avisa quando a resposta deixa de casar com o esperado. Nenhum dos dois entra
na suíte que roda a cada commit — não se pede que o `pytest` dependa da
internet.
:::
