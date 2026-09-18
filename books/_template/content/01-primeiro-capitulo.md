---
title: "Primeiro capítulo"
number: 1
kicker: "A frase que aparece sob o título na abertura do capítulo."
---

O primeiro parágrafo não recua e carrega a promessa do capítulo. Escreva
como quem responde a uma pergunta prática, não como quem apresenta um
índice de assuntos.

## Uma seção

Texto normal. `código no meio da frase` fica na fonte mono. **Negrito** e
*itálico* funcionam como em Markdown.

```python title="exemplo.py" numbered
def somar(a, b):
    return a + b
```

:::tip Título opcional
As cinco caixas são `tip`, `warning`, `note`, `key` e `practice`.
Cinco, e mais nenhuma: caixa nova é dívida de design.
:::

:::diagram type="flowchart" caption="Uma decisão e dois caminhos."
nodes:
  - { id: ini, type: start,    text: "Início" }
  - { id: d1,  type: decision, text: "deu certo?" }
  - { id: ok,  type: process,  text: "segue" }
  - { id: no,  type: process,  text: "corrige" }
edges:
  - { from: ini, to: d1 }
  - { from: d1,  to: ok, label: "sim" }
  - { from: d1,  to: no, label: "não" }
  - { from: no,  to: d1 }
:::

| Coluna | O que significa |
|---|---|
| `a` | primeira |
| `b` | segunda |

Table: Legenda da tabela, se houver.

:::summary
- Uma linha por ideia que o leitor precisa levar embora.
- Três a cinco itens. Mais que isso não é resumo.
:::

:::exercise level=1
O enunciado do exercício.

:::answer
A resposta, que a pipeline recolhe para o apêndice "Respostas".
:::
