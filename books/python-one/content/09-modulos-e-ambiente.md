---
title: "Módulos e ambiente"
number: 9
slug: modulos-e-ambiente
part: p2
kicker: "Um arquivo só é um script. Dois arquivos já são uma decisão de arquitetura."
goal: >-
  Dividir código em módulos e pacotes, importar sem ciclos, instalar
  dependências de forma reprodutível e montar a estrutura de pasta que o
  projeto vai usar até o fim do livro.
---

Todo projeto Python começa com um arquivo. O segundo arquivo é onde as
dúvidas aparecem: onde ele mora, como o primeiro o encontra, e o que
acontece quando os dois precisam um do outro.

## Módulo é arquivo

```python title="precos.py" numbered
TAXA_PADRAO = 0.12


def com_margem(preco, taxa=TAXA_PADRAO):
    return preco * (1 + taxa)
```

```python title="app.py" numbered
import precos

print(precos.com_margem(8.90))
print(precos.TAXA_PADRAO)
```

Qualquer arquivo `.py` é um módulo, e o nome do módulo é o nome do arquivo
sem a extensão. Não há declaração, não há registro, não há configuração.

Há três formas de importar, e elas não são equivalentes:

```python title="formas.py" numbered
import precos                         # precos.com_margem(...)
from precos import com_margem         # com_margem(...)
from precos import com_margem as cm   # cm(...)
```

:::key
A primeira forma preserva a origem: quem lê `precos.com_margem` sabe de onde
veio. A segunda é mais curta e apaga essa informação. Use `from ... import`
quando o nome for autoexplicativo (`from decimal import Decimal`) e `import`
simples quando não for (`import json` e depois `json.dumps`).
:::

E há uma quarta forma, que este livro não usa:

```python
from precos import *
```

Ela despeja todos os nomes do módulo no seu arquivo. Você deixa de saber de
onde cada nome veio, e qualquer nome novo acrescentado ao módulo pode
sobrescrever silenciosamente um nome seu. É proibida em praticamente todo
guia de estilo profissional.

## Pacote é pasta

Quando os módulos passam de meia dúzia, eles se agrupam em pastas:

:::tree title="A estrutura que o projeto vai ter no fim do livro"
catalogo/
  app/
    __init__.py
    main.py               # a aplicação FastAPI
    models/               # as tabelas
      __init__.py
      produto.py
    schemas/              # o formato do JSON
      __init__.py
      produto.py
    repositories/         # as consultas
      __init__.py
      produto.py
    services/             # as regras
      __init__.py
      produto.py
    routers/              # as rotas HTTP
      __init__.py
      produtos.py
  tests/
  requirements.txt
  .env
:::

Cada pasta que contém um `__init__.py` é um **pacote**, e pode ser
importada:

```python
from app.services.produto import criar
```

O `__init__.py` pode estar vazio — e na maior parte das vezes está. Ele é
apenas a marca de que aquela pasta é para importar, não para guardar dado.

:::trivia
Desde o Python 3.3, uma pasta sem `__init__.py` também pode ser importada:
são os *pacotes de namespace*. Funciona, e ainda assim quase todo projeto
sério continua criando o arquivo vazio — porque a ausência dele muda
sutilmente como ferramentas de teste e empacotamento descobrem seus módulos,
e "sutilmente" é a palavra que ninguém quer no build.
:::

## `__name__`, finalmente

Todo módulo tem uma variável `__name__`. Quando o arquivo é executado
diretamente, ela vale `"__main__"`. Quando o arquivo é importado, ela vale o
nome do módulo.

```python title="precos.py" numbered
def com_margem(preco):
    return preco * 1.12


if __name__ == "__main__":
    print(com_margem(8.90))
```

Agora `python precos.py` imprime o teste, e `import precos` não imprime
nada. Sem essa guarda, **todo código solto no módulo roda na importação** —
e um `print` de teste esquecido no fim de um arquivo aparece em produção,
dentro do log, uma vez por processo.

:::pitfall
Código pesado fora de função e fora dessa guarda é um defeito clássico:
conexão com banco, leitura de arquivo, chamada de rede. Ele roda na
importação, antes do programa decidir se precisava daquilo — e em teste,
roda antes do primeiro teste começar.
:::

## Como o Python encontra um módulo

```text
Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import precos
ModuleNotFoundError: No module named 'precos'
```

Esse erro tem sempre a mesma causa: o arquivo não está em nenhum dos lugares
onde o Python procura. A lista de lugares está em `sys.path`, e ela é, nesta
ordem: a pasta do arquivo que você executou, as pastas do ambiente virtual e
as pastas do Python instalado.

:::practice
Rode `python -c "import sys; print(sys.path)"` uma vez, com o ambiente
virtual ativo e outra sem. As listas são diferentes, e essa diferença é a
explicação inteira do "mas eu instalei essa biblioteca".
:::

A consequência prática: rode sempre a partir da raiz do projeto, e use o
modo módulo quando o arquivo estiver dentro de um pacote:

```text
$ python -m app.main       # certo
$ python app/main.py       # quebra os imports relativos
```

## Importação circular

Dois módulos que se importam mutuamente formam um ciclo, e o Python falha de
um jeito que confunde:

```text
ImportError: cannot import name 'Produto' from partially
initialized module 'app.models.produto' (most likely due to
a circular import)
```

A mensagem é boa: *partially initialized*. O módulo A começou a carregar,
pediu o B, que pediu o A de volta — e o A ainda estava pela metade.

Existem truques para contornar (importar dentro da função, adiar a
anotação). Todos eles escondem o sintoma. A causa é de desenho: dois módulos
que precisam um do outro provavelmente são um só, ou há um terceiro
escondido dentro dos dois.

:::key
A arquitetura em camadas do capítulo @cap:service existe em parte para isso:
quando cada camada só conhece a de baixo, o ciclo é impossível por
construção. `router` importa `service`, `service` importa `repository`, e
nenhum deles olha para cima.
:::

## A biblioteca padrão

Python vem com uma biblioteca grande, e conhecer os módulos certos poupa
dependência externa:

| Módulo | Para quê |
|---|---|
| `datetime` | data e hora, com fuso |
| `decimal` | dinheiro |
| `pathlib` | caminhos de arquivo |
| `json` | ler e escrever JSON |
| `os` e `sys` | ambiente e processo |

Tabela: São os cinco que aparecem neste livro. A biblioteca inteira tem
mais de duzentos módulos e vale uma visita ao índice oficial.

```python title="padrao.py" numbered
from datetime import datetime, timezone
from pathlib import Path

agora = datetime.now(timezone.utc)
arquivo = Path("dados") / "catalogo.json"

print(agora.isoformat())
print(arquivo.exists())
```

:::warning
Use `datetime.now(timezone.utc)`, não `datetime.now()`. O segundo devolve a
hora local **sem dizer qual é o fuso** — e um horário sem fuso, gravado num
banco que outro servidor vai ler, é uma informação incompleta se passando
por completa. Guarde sempre em UTC; converta para o fuso do usuário só na
hora de exibir.
:::

## Dependências: instalar é fácil, repetir é o problema

```text
$ pip install fastapi
$ pip list
```

Instalar uma biblioteca é uma linha. O problema aparece quando outra pessoa
— ou o servidor, ou você daqui a seis meses — precisa do **mesmo** conjunto
de versões.

A forma mínima é um arquivo de requisitos:

```text
$ pip freeze > requirements.txt
```

```text title="requirements.txt"
fastapi==0.115.6
pydantic==2.10.3
sqlalchemy==2.0.36
uvicorn==0.34.0
```

E do outro lado:

```text
$ pip install -r requirements.txt
```

:::pitfall
`pip freeze` despeja **tudo** que está instalado, inclusive as dependências
das suas dependências. O arquivo fica grande e, pior, fixa versões de coisas
que você não escolheu. Muitos projetos mantêm dois arquivos: um escrito à
mão com o que você realmente pediu, e um gerado com tudo — e ferramentas
modernas como `uv` e `poetry` fazem essa separação sozinhas.
:::

## Configuração fora do código

Uma regra que vale para todo o resto do livro: senha, endereço de banco e
chave de API não moram no código.

```text title=".env"
DATABASE_URL=postgresql://user:senha@localhost/catalogo
SECRET_KEY=troque-isto-em-producao
```

```python title="config.py" numbered
import os

DATABASE_URL = os.environ["DATABASE_URL"]
SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
```

Repare na diferença entre as duas linhas. `os.environ["X"]` quebra na
partida se a variável não existir; `os.environ.get("X", padrão)` segue com
um padrão. A primeira forma é a certa para segredo: um servidor que sobe sem
chave secreta é pior que um servidor que não sobe.

:::key
O arquivo `.env` **nunca** entra no controle de versão. A primeira coisa que
o capítulo @cap:git faz é colocá-lo no `.gitignore`, junto com `.venv/` e
`__pycache__/`. Chave vazada em repositório é um incidente de segurança que
não tem desfazer: apagar o commit não apaga a cópia de quem clonou.
:::

:::summary
- Módulo é arquivo, pacote é pasta com `__init__.py`.
- `from x import *` apaga a origem dos nomes; não use.
- `if __name__ == "__main__":` separa o que roda do que se importa.
- `ModuleNotFoundError` é quase sempre ambiente errado ou pasta errada.
- Importação circular é sintoma de camadas mal separadas.
- Dependência se fixa em arquivo; segredo mora em variável de ambiente.
:::

:::exercise level=1
Crie um módulo `precos.py` com a função `com_margem` e um `app.py` que a
importe e imprima o resultado para três valores. Rode os dois de formas
diferentes e observe o efeito da guarda `__main__`.

:::answer
```python title="precos.py"
TAXA = 0.12


def com_margem(preco, taxa=TAXA):
    return preco * (1 + taxa)


if __name__ == "__main__":
    print("teste:", com_margem(10))
```

```python title="app.py"
from precos import com_margem

for p in (8.90, 3.50, 12.00):
    print(f"{p:.2f} -> {com_margem(p):.2f}")
```

`python precos.py` imprime o teste. `python app.py` não — porque a guarda
impediu.
:::

:::exercise level=2
O código abaixo dá `ModuleNotFoundError: No module named 'app'`, rodado de
dentro da pasta `app/`. Explique e dê duas soluções.

```text
catalogo/
  app/
    main.py        # from app.precos import com_margem
    precos.py
```

:::answer
O Python coloca no caminho de busca a pasta **do arquivo executado**. Rodando
`python main.py` de dentro de `app/`, o caminho passa a ser `app/`, e dentro
dela não existe nada chamado `app`.

Primeira solução: rodar da raiz, em modo módulo.

```text
$ cd catalogo
$ python -m app.main
```

Segunda: trocar o import por relativo — `from .precos import com_margem` —
que só funciona quando o arquivo é executado como parte do pacote, ou seja,
ainda exige a primeira solução. As duas convergem para a mesma regra: **a
raiz do projeto é o lugar de onde se roda**.
:::

:::exercise level=3
Sua equipe tem três desenvolvedores e um servidor. Duas pessoas conseguem
rodar o projeto; a terceira recebe erro numa função que as outras usam sem
problema. Liste, em ordem, as quatro perguntas que você faria — e diga qual
arquivo do projeto deveria ter evitado o problema.

:::answer
1. **Qual `python` você está usando?** `which python` ou `where python`,
   para confirmar que o ambiente virtual está ativo.
2. **Qual versão?** `python --version`. Uma sintaxe de 3.10 num Python 3.9
   dá erro de sintaxe onde ninguém espera.
3. **Quais versões das bibliotecas?** `pip freeze`, comparado com o das
   outras máquinas. Uma diferença de versão menor já muda comportamento.
4. **De onde você está rodando?** A pasta atual define o caminho de busca.

O arquivo que deveria ter evitado tudo isso é o `requirements.txt` com
versões fixas — acompanhado de um `README` dizendo qual versão do Python o
projeto exige. A versão da linguagem é uma dependência como qualquer outra,
e é a única que quase nunca é declarada.
:::
