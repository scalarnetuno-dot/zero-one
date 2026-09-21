---
title: "Exceções"
number: 13
slug: excecoes
part: p2
kicker: "Um erro tratado errado é pior que um erro não tratado: ele apaga a evidência."
goal: >-
  Tratar falhas com `try`/`except` sem engolir informação, criar exceções
  próprias, usar `with` para liberar recursos e escolher entre pedir permissão
  e pedir perdão.
---

Todo programa que toca o mundo real falha: o arquivo não existe, a rede caiu,
o texto não era um número, o produto foi apagado entre a consulta e a
atualização. A pergunta não é se vai falhar — é o que acontece quando
falhar.

```python title="conversao.py" numbered
entrada = "cento e vinte"

try:
    estoque = int(entrada)
except ValueError:
    print("valor inválido, usando zero")
    estoque = 0

print(estoque)
```

`try` marca o trecho arriscado. `except ValueError` captura **apenas** esse
tipo de falha. Tudo mais continua subindo.

## A hierarquia

Exceções formam uma árvore, e capturar um nó captura todos os descendentes.

:::diagram type="blocks" caption="A parte da hierarquia que você usa todo dia — e a que é melhor nunca capturar."
rows:
  - [{ text: "BaseException", note: "inclui Ctrl+C e saída do programa" }]
  - [{ text: "Exception", note: "tudo que faz sentido tratar" }]
  - [{ text: "ValueError", note: "tipo certo, valor impossível" }, { text: "TypeError", note: "tipo errado" }]
  - [{ text: "KeyError", note: "chave ausente" }, { text: "OSError", note: "arquivo, rede, permissão" }]
:::

| Exceção | Significa |
|---|---|
| `ValueError` | o tipo é certo, o valor não serve |
| `TypeError` | o tipo é errado para a operação |
| `KeyError` / `IndexError` | não existe essa chave / posição |
| `AttributeError` | o objeto não tem esse atributo |
| `ZeroDivisionError` | divisão por zero |
| `OSError` | arquivo, permissão, rede |

Tabela: Estas seis cobrem quase tudo que você vai capturar em código de
aplicação.

:::warning
`except BaseException` e `except:` sem tipo capturam também `KeyboardInterrupt`
e `SystemExit` — ou seja, capturam o seu `Ctrl+C` e a ordem de encerrar o
processo. Um servidor com isso no laço principal não desliga quando você
manda. Se precisar de um alcance amplo, o limite é `Exception`.
:::

## O `except` que apaga a evidência

```python title="o_pior_codigo.py" numbered
try:
    produto = buscar(id)
    atualizar(produto)
except Exception:
    pass
```

Este trecho é o defeito mais caro deste livro, e não porque seja difícil de
escrever — é porque parece responsável. Ele captura tudo, não registra
nada, e segue adiante como se tivesse dado certo.

Quando o relatório sair errado daqui a três meses, não haverá log, não
haverá rastro, não haverá nada. A informação existiu por alguns
microssegundos e foi descartada de propósito.

:::story O silêncio de novembro
A conferência de novembro não fechava. Faltavam 214 produtos.

Bia leu o log inteiro. Nada. Nenhuma linha de erro, nenhum aviso, nenhum
traceback. O sistema tinha rodado a madrugada inteira sem reclamar.

— Se não tem erro no log — disse Rafa —, então não deu erro.

— Ou deu erro e alguém mandou calar a boca.

Ela abriu a rotina de importação e rolou até o fim do laço. Estava lá, nas
duas últimas linhas, com a indentação perfeita:

```python
    except Exception:
        continue
```

— Duzentos e catorze vezes — disse Bia. — E ele continuou, cada uma delas.

Elias olhou por cima do ombro.

— Esse `continue` foi escrito por alguém que estava com pressa e queria que
o script terminasse. Ele terminou. — Fez uma pausa. — Todo dia, desde então.
:::

:::art caption="Um `except` vazio não conserta o erro: ele apaga a testemunha."
Charge editorial minimalista em fundo branco: uma sala de servidores com um
alarme de incêndio na parede, e uma pessoa de escada colocando fita adesiva
sobre a sirene, com expressão concentrada e satisfeita. Ao fundo, um fio de
fumaça sobe de um dos racks, ignorado. Poucos elementos, humor seco, estética
de revista de tecnologia.
:::

:::key
Se você vai capturar, faça uma das três: **trate** de verdade, **registre**
com o traceback, ou **relance** acrescentando contexto. `pass` não é
nenhuma das três.
:::

## `else` e `finally`

```python title="completo.py" numbered
try:
    arquivo = abrir(caminho)
except OSError as erro:
    print(f"não consegui abrir: {erro}")
else:
    processar(arquivo)
finally:
    limpar_temporarios()
```

Quatro blocos, quatro papéis distintos:

- `try` — só o que pode falhar, e o mínimo possível.
- `except` — o que fazer quando falhou.
- `else` — o que fazer **se não** falhou. Mantém fora do `try` o código que
  não deveria estar protegido.
- `finally` — roda sempre, com erro ou sem. É o lugar de liberar recurso.

:::pitfall
O `try` grande é uma armadilha sutil: se ele tem dez linhas e uma delas
levanta `ValueError`, você não sabe qual. Pior, um `ValueError` de uma linha
que você não previu vai ser tratado pelo `except` que você escreveu para
outra — e o programa segue com uma suposição errada. Proteja a linha,
não o parágrafo.
:::

## `with`: o `finally` que você não escreve

```python title="arquivo.py" numbered
with open("catalogo.csv", encoding="utf-8") as f:
    for linha in f:
        print(linha.strip())
```

O `with` garante que o arquivo será fechado ao sair do bloco — por saída
normal, por `return` ou por exceção. É o mesmo serviço do `finally`, sem o
`finally`.

Isso se chama **gerenciador de contexto**, e você vai usá-lo o livro todo: a
sessão do banco no capítulo @cap:sqlalchemy é um, a transação no capítulo
@cap:service é outro, o cliente de teste do capítulo @cap:testando-a-api é
outro.

:::key
Toda vez que um recurso precisa ser devolvido — arquivo, conexão, trava,
transação —, procure primeiro se existe um `with`. Em Python, ele existe em
quase todos os casos, e escrever `try/finally` à mão é quase sempre estar
reinventando algo pronto.
:::

## Levantar a sua própria exceção

```python title="excecoes_do_projeto.py" numbered
class ErroDoCatalogo(Exception):
    """Base de todos os erros do domínio."""


class ProdutoNaoEncontrado(ErroDoCatalogo):
    def __init__(self, produto_id: int):
        self.produto_id = produto_id
        super().__init__(f"produto {produto_id} não encontrado")


class EstoqueInsuficiente(ErroDoCatalogo):
    def __init__(self, disponivel: int, pedido: int):
        self.disponivel = disponivel
        self.pedido = pedido
        super().__init__(
            f"estoque insuficiente: {disponivel} < {pedido}"
        )
```

Três decisões aqui merecem atenção.

A **base comum** permite capturar todos os erros do domínio com um `except
ErroDoCatalogo` — e distinguir os seus de um `ValueError` acidental de
biblioteca.

Os **dados anexados** (`produto_id`, `disponivel`) permitem que quem captura
monte a resposta HTTP sem precisar ler a mensagem de texto. No capítulo
@cap:tratamento-de-erros, `ProdutoNaoEncontrado` vira `404` e
`EstoqueInsuficiente` vira `409` — e essa tradução é uma linha, porque os
tipos são distintos.

E a **mensagem** é para humano: ela vai para o log, não para o usuário.

:::pitfall
Não crie uma exceção por mensagem de erro. Trinta classes com um `pass`
dentro não ajudam ninguém: o que distingue os casos precisa ser o
**tratamento**, não o texto. Se dois erros são tratados do mesmo jeito, são
o mesmo erro com mensagens diferentes.
:::

## `raise ... from`: não perder a causa

```python title="from.py" numbered
try:
    dados = json.loads(corpo)
except json.JSONDecodeError as erro:
    raise ErroDoCatalogo("corpo inválido") from erro
```

O `from` encadeia: o traceback final mostra as duas exceções, com a frase
*"The above exception was the direct cause of the following exception"*.
Sem ele, você troca uma informação técnica precisa por uma mensagem
genérica, e a pessoa de plantão às três da manhã fica sem o motivo real.

## Pedir perdão ou pedir permissão

Duas formas de escrever a mesma proteção:

:::compare left="Pedir permissão" right="Pedir perdão" lang="python"
if "preco" in dados:
    p = dados["preco"]
else:
    p = 0
---
try:
    p = dados["preco"]
except KeyError:
    p = 0
:::

A primeira é a tradicional; a segunda é a idiomática em Python, e tem uma
vantagem real em código concorrente: entre o `if` e o uso, o mundo pode
mudar — o arquivo que existia pode ter sido apagado, a chave pode ter sido
removida por outra thread.

A regra prática: se a falha é **esperada e frequente**, teste antes; se é
**excepcional**, capture. Verificar `if os.path.exists(...)` antes de abrir
um arquivo é, além de mais lento, uma garantia falsa.

:::trivia
Os dois estilos têm siglas antigas no vocabulário Python: LBYL, *look before
you leap*, e EAFP, *easier to ask forgiveness than permission*. A segunda
aparece na documentação oficial como o estilo característico da linguagem —
e é uma das poucas vezes em que a documentação de uma linguagem toma partido
explícito sobre estilo.
:::

## Registrar, não imprimir

```python title="log.py" numbered
import logging

logger = logging.getLogger(__name__)

try:
    atualizar(produto)
except ErroDoCatalogo:
    logger.exception("falha ao atualizar produto %s", produto.id)
    raise
```

`logger.exception` registra a mensagem **com o traceback inteiro**, e só
funciona dentro de um `except`. O `raise` sem argumento relança a exceção
original, preservando o traceback.

`print` em servidor é um erro de categoria: ele não tem nível, não tem
carimbo de tempo, não tem origem, e não tem como ser desligado em produção
sem mexer no código.

:::summary
- Capture o tipo específico; `except Exception` é o limite máximo, nunca
  `BaseException`.
- `except: pass` apaga a evidência — trate, registre ou relance.
- `try` pequeno: proteja a linha, não o parágrafo.
- `with` é o `finally` que você não precisa escrever.
- Exceções do domínio com base comum viram códigos HTTP numa linha.
- `raise ... from` preserva a causa; `logger.exception` preserva o traceback.
:::

:::milestone
Com exceções próprias, o projeto ganha vocabulário: "produto não encontrado"
deixa de ser um `None` viajando pelo código e vira um fato com nome, que
qualquer camada pode capturar.
:::

:::exercise level=1
Escreva uma função `para_inteiro(texto, padrao=0)` que devolva o número
convertido ou o padrão quando a conversão falhar.

:::answer
```python
def para_inteiro(texto, padrao=0):
    try:
        return int(texto)
    except (ValueError, TypeError):
        return padrao
```
`TypeError` entra na tupla porque `int(None)` levanta `TypeError`, não
`ValueError` — e `None` é exatamente o que chega quando um campo não veio.
:::

:::exercise level=2
Escreva a classe `EstoqueInsuficiente` com os campos `disponivel` e
`pedido`, e uma função `vender(produto, quantidade)` que a levante. Depois
capture e imprima uma mensagem para o usuário usando os campos, não o texto
da exceção.

:::answer
```python
class EstoqueInsuficiente(Exception):
    def __init__(self, disponivel, pedido):
        self.disponivel = disponivel
        self.pedido = pedido
        super().__init__(f"{disponivel} < {pedido}")


def vender(produto, quantidade):
    if quantidade > produto.estoque:
        raise EstoqueInsuficiente(produto.estoque, quantidade)
    produto.estoque -= quantidade


try:
    vender(tomate, 500)
except EstoqueInsuficiente as e:
    print(f"Temos {e.disponivel}; você pediu {e.pedido}.")
```
Montar a mensagem a partir dos campos, e não do `str(e)`, é o que permite
traduzir a resposta, mudar o texto sem mexer em quem levanta, e devolver
JSON estruturado no capítulo @cap:tratamento-de-erros.
:::

:::exercise level=3
O código abaixo roda todas as madrugadas e "nunca dá erro". Aponte os três
defeitos e reescreva.

```python
def importar(linhas):
    total = 0
    for linha in linhas:
        try:
            nome, preco = linha.split(",")
            salvar(nome, float(preco))
            total += 1
        except:
            pass
    return total
```

:::answer
**Primeiro defeito:** `except:` sem tipo captura `KeyboardInterrupt` e
`SystemExit`. Esse laço não pode ser interrompido.

**Segundo:** `pass`. Toda linha malformada, todo erro de banco, toda falha
de rede desaparece sem rastro — e a função devolve um total que parece
correto.

**Terceiro:** o `try` cobre três operações com falhas de naturezas
diferentes. Uma linha com três vírgulas, um preço não numérico e um banco
fora do ar recebem exatamente o mesmo tratamento: nenhum.

```python
import logging

logger = logging.getLogger(__name__)


def importar(linhas):
    total = 0
    rejeitadas = []

    for numero, linha in enumerate(linhas, start=1):
        try:
            nome, preco = linha.split(",")
            valor = Decimal(preco.strip())
        except (ValueError, InvalidOperation) as erro:
            logger.warning("linha %s ignorada: %s", numero, erro)
            rejeitadas.append(numero)
            continue

        salvar(nome.strip(), valor)
        total += 1

    return total, rejeitadas
```

O que mudou de verdade não é o tratamento: é o **retorno**. A função agora
devolve o que deu certo e o que não deu. Quem chama decide se 214 linhas
rejeitadas são aceitáveis ou se a importação inteira deve ser desfeita — e
essa decisão nunca foi da função de importar.

Repare também que o erro de `salvar` ficou de fora do `try`. Uma falha de
banco não é uma linha ruim: ela derruba a importação, e deve mesmo derrubar.
:::
