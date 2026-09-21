---
title: "Testando Python"
number: 36
slug: testando-python
part: p8
kicker: "O teste não prova que o código está certo. Ele prova que aquilo que já funcionava continua funcionando."
goal: >-
  Escrever testes com pytest, usar fixtures e parametrização, nomear testes
  que explicam a falha, e decidir o que merece teste.
---

Todo mundo testa. A pergunta é se o teste é uma pessoa clicando no `/docs`
pela quinta vez ou um arquivo que roda em dois segundos, sempre igual, sem
ninguém olhando.

## pytest

```text
$ pip install pytest
```

```python title="tests/test_precos.py" numbered
from decimal import Decimal

from app.precos import com_margem


def test_aplica_margem_padrao_de_doze_por_cento():
    assert com_margem(Decimal("10.00")) == Decimal("11.20")
```

```text
$ pytest
collected 1 item

tests/test_precos.py .                                   [100%]

1 passed in 0.03s
```

Não há classe, não há `setUp`, não há `self.assertEqual`. Uma função cujo
nome começa com `test_`, num arquivo cujo nome começa com `test_`, e o
`assert` do próprio Python.

O pytest reescreve o `assert` para mostrar os valores na falha:

```text
    def test_aplica_margem_padrao():
>       assert com_margem(Decimal("10.00")) == Decimal("11.20")
E       assert Decimal('11.50') == Decimal('11.20')
E        +  where Decimal('11.50') = com_margem(Decimal('10.00'))

tests/test_precos.py:7: AssertionError
```

Você não escreveu mensagem nenhuma e a falha já diz o valor esperado, o
valor obtido e de onde ele veio. Em `unittest`, a mesma informação exigiria
`assertEqual(a, b, "margem errada")` — e a mensagem desatualizaria.

## Arrumar, agir, afirmar

```python title="tests/test_produto.py" numbered
def test_vender_reduz_o_estoque():
    # arrumar
    produto = Produto(nome="Tomate", preco=Decimal("8.90"),
                      estoque=100)

    # agir
    produto.vender(30)

    # afirmar
    assert produto.estoque == 70
```

Três blocos, nessa ordem, separados por linha em branco. Quando um teste não
cabe nesse formato, quase sempre é porque ele está testando duas coisas — e
dois testes contam melhor a história do que um com seis `assert`.

:::key
O nome do teste é a documentação que nunca desatualiza, porque ela quebra
junto com o código. `test_vender_reduz_o_estoque` diz o que se espera;
`test_vender_1` não diz nada, e é o nome que aparece no relatório de falha
às onze da noite.
:::

## Testar o que deve falhar

```python title="tests/test_produto.py" numbered
import pytest


def test_nao_vende_mais_do_que_tem():
    produto = Produto(nome="Tomate", preco=Decimal("8.90"),
                      estoque=10)

    with pytest.raises(EstoqueInsuficiente) as erro:
        produto.vender(30)

    assert erro.value.disponivel == 10
    assert erro.value.pedido == 30
    assert produto.estoque == 10
```

Três afirmações e cada uma cobre uma coisa: a exceção certa foi levantada,
ela carrega os dados certos, e o estado **não** mudou. Essa terceira é a
mais esquecida e a mais valiosa: uma operação que falha pela metade é pior
que uma que não acontece.

## Fixtures

```python title="tests/conftest.py" numbered
import pytest


@pytest.fixture
def produto():
    return Produto(
        nome="Tomate italiano",
        preco=Decimal("8.90"),
        estoque=100,
    )
```

```python title="tests/test_produto.py" numbered
def test_repor_aumenta_o_estoque(produto):
    produto.repor(20)
    assert produto.estoque == 120
```

Uma fixture é uma função decorada cujo **nome vira parâmetro**. O pytest a
chama e entrega o resultado — exatamente a mesma ideia do `Depends` do
capítulo @cap:dependency-injection, e não é coincidência: as duas resolvem
o mesmo problema.

O arquivo `conftest.py` é especial: fixtures declaradas nele ficam
disponíveis para todos os testes da pasta e das subpastas, sem import.

```python title="fixture com limpeza" numbered
@pytest.fixture
def arquivo_temporario(tmp_path):
    caminho = tmp_path / "catalogo.csv"
    caminho.write_text("nome,preco\nTomate,8.90\n")
    yield caminho
    # o tmp_path do pytest se apaga sozinho
```

:::pitfall
Fixture que devolve um objeto **mutável** compartilhado entre testes é fonte
de falha intermitente: um teste altera, o seguinte recebe alterado, e a
ordem de execução passa a importar. O padrão do pytest evita isso — a
fixture é chamada de novo para cada teste. O que quebra a garantia é
declarar `scope="module"` ou `scope="session"` sem pensar.
:::

## Parametrização

```python title="tests/test_frete.py" numbered
@pytest.mark.parametrize(
    "caixas,esperado",
    [
        (1, Decimal("12.00")),
        (5, Decimal("28.00")),
        (40, Decimal("80.00")),
        (100, Decimal("80.00")),
    ],
)
def test_frete_por_faixa(caixas, esperado):
    assert frete(caixas) == esperado
```

```text
tests/test_frete.py::test_frete_por_faixa[1-12.00] PASSED
tests/test_frete.py::test_frete_por_faixa[5-28.00] PASSED
tests/test_frete.py::test_frete_por_faixa[40-80.00] PASSED
tests/test_frete.py::test_frete_por_faixa[100-80.00] PASSED
```

Quatro testes, um corpo. E cada caso aparece com nome próprio no relatório —
quando o de 100 caixas quebrar, você sabe qual quebrou sem abrir o arquivo.

:::key
Os casos que merecem estar na lista são as **bordas**: zero, um, o limite, o
limite mais um, o negativo, o vazio. É onde o defeito mora. Testar 5, 6 e 7
caixas é testar três vezes a mesma linha de código.
:::

## O que testar

| Testar | Não testar |
|---|---|
| regra de negócio | biblioteca de terceiros |
| cálculo com bordas | `getters` e `setters` |
| comportamento em erro | o framework |
| o defeito que apareceu ontem | código que não tem decisão |

Tabela: A terceira linha da esquerda é a mais rentável: todo defeito
corrigido merece um teste que o reproduza, escrito **antes** da correção.

:::story O teste que ninguém escreveu
O estoque negativo voltou.

Não o mesmo — outro caminho, outra rotina, o mesmo resultado. Bia abriu o
histórico e encontrou a correção de março, com a mensagem de commit certa e
a explicação certa.

Sem teste.

— A gente consertou — disse Rafa.

— A gente consertou uma vez — respondeu Bia. — O teste é o que faz o conserto
valer para as próximas.

Ela escreveu quatro linhas que reproduziam o defeito, viu falhar, corrigiu,
viu passar. Da segunda vez, a correção levou quinze minutos. Da primeira,
tinha levado dois dias.
:::

## Cobertura

```text
$ pip install pytest-cov
$ pytest --cov=app --cov-report=term-missing

Name                        Stmts   Miss  Cover   Missing
---------------------------------------------------------
app/services/produto.py        68      4    94%   51-54
app/repositories/produto.py    31      0   100%
---------------------------------------------------------
TOTAL                         214     19    91%
```

A coluna `Missing` é a única realmente útil: ela diz **quais linhas** nunca
rodaram. Costuma ser exatamente o tratamento de erro que ninguém exercitou.

:::warning
Cobertura mede linhas executadas, não comportamento verificado. Um teste sem
nenhum `assert` dá cem por cento de cobertura e não testa nada. Meta de
cobertura vira jogo: o time escreve testes que tocam linhas para bater o
número. Use o relatório para **encontrar buraco**, não como nota.
:::

## Como rodar

```text
$ pytest                             # tudo
$ pytest tests/test_produto.py       # um arquivo
$ pytest -k "estoque"                # por nome
$ pytest -x                          # para na primeira falha
$ pytest -q                          # saída curta
$ pytest --lf                        # só os que falharam antes
```

O `--lf` é o que mais economiza tempo no dia a dia: corrija, rode só o que
estava quebrado, e só depois rode tudo.

:::summary
- pytest usa funções e o `assert` da linguagem; a falha mostra os valores.
- Arrumar, agir, afirmar — e um teste que não cabe nisso está testando duas
  coisas.
- O nome do teste é a documentação que quebra junto com o código.
- `pytest.raises` verifica a exceção, os dados dela e que o estado não mudou.
- Fixture é o `Depends` do teste; `conftest.py` a compartilha sem import.
- Parametrize as bordas, não o meio.
- Cobertura encontra buraco; ela não é nota.
:::

:::exercise level=1
Escreva dois testes para `com_margem`: um com a taxa padrão e outro com taxa
informada.

:::answer
```python
def test_margem_padrao():
    assert com_margem(Decimal("10.00")) == Decimal("11.20")


def test_margem_informada():
    resultado = com_margem(Decimal("10.00"), Decimal("0.08"))
    assert resultado == Decimal("10.80")
```
:::

:::exercise level=1
Escreva a fixture que devolve um produto pronto e dois testes que a usem,
confirmando que a alteração feita por um não vaza para o outro.

:::answer
```python
@pytest.fixture
def produto():
    return Produto(
        nome="Tomate", preco=Decimal("8.90"), estoque=100
    )


def test_vende(produto):
    produto.vender(40)
    assert produto.estoque == 60


def test_repoe(produto):
    produto.repor(40)
    assert produto.estoque == 140
```
Os dois passam em qualquer ordem porque a fixture é chamada de novo para
cada teste. Troque a assinatura para `@pytest.fixture(scope="module")` e
rode: um dos dois quebra, e qual deles depende da ordem — que é exatamente
o defeito descrito no capítulo.
:::

:::exercise level=2
Parametrize um teste que verifique o frete nas quatro faixas e acrescente o
caso de zero caixas.

:::answer
```python
@pytest.mark.parametrize(
    "caixas,esperado",
    [
        (1, Decimal("12.00")),
        (2, Decimal("16.00")),
        (40, Decimal("80.00")),
        (999, Decimal("80.00")),
    ],
)
def test_frete(caixas, esperado):
    assert frete(caixas) == esperado


def test_frete_de_zero_caixas_e_recusado():
    with pytest.raises(ValueError):
        frete(0)
```
O caso de zero ficou de fora da parametrização de propósito: ele não devolve
valor, levanta exceção. Forçar casos de natureza diferente na mesma lista
produz parametrizações com `None` e `if` dentro do teste.
:::

:::exercise level=3
Um colega defende cobertura mínima de 95% como regra obrigatória para
aprovar qualquer alteração. Avalie a proposta.

:::answer
O objetivo é bom e o instrumento é errado, por três motivos.

**Cobertura não mede verificação.** Um teste que chama a função e não afirma
nada cobre todas as linhas dela. Sob pressão de número, é exatamente esse
tipo de teste que aparece — e ele é pior que nenhum, porque dá confiança sem
dar garantia.

**A meta empurra o esforço para o lugar errado.** Os últimos pontos
percentuais costumam estar em `__repr__`, em tratamento de erro improvável e
em código gerado. Enquanto isso, a regra de preço mínimo do capítulo
@cap:validacao pode ter 100% de cobertura com um caso só, sem nenhuma borda
testada.

**Ela penaliza a alteração pequena.** Uma correção de duas linhas num arquivo
com cobertura baixa reprova por um número que ela não criou — e o efeito
prático é que ninguém encosta em código legado.

O que eu proporia no lugar: cobertura **do que mudou** — as linhas novas ou
alteradas da mudança precisam estar cobertas —, o relatório de `Missing`
lido na revisão em vez de um número no portão, e a regra que rende mais que
qualquer meta: todo defeito corrigido chega acompanhado do teste que o
reproduz. A cobertura sobe como consequência, e sobe nos lugares certos.
:::
