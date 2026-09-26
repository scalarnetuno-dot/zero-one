# Zero One

Coleção de livros técnicos de programação — e a pipeline que os compõe.

O livro é dado. O layout é o sistema. Um volume novo não traz código novo.

```bash
python -m pip install -r requirements.txt
python collection/theme/fonts/_fetch.py      # fontes OFL, uma vez por máquina

python -m pipeline list
python -m pipeline check java-one     # o revisor automático
python -m pipeline art   java-one     # arte provisória (capa e figuras)
python -m pipeline build java-one     # capa + miolo + EPUB
python -m pipeline cover java-one     # capa completa da KDP (lombada calculada)
```

Um `build` deixa quatro arquivos em `build/<slug>/`:

| Arquivo | Para quê |
|---|---|
| `<slug>-leitura.pdf` | **capa + miolo** — é o que você lê e manda para alguém |
| `<slug>.pdf` | miolo limpo — é o que sobe na KDP impressa |
| `<slug>.epub` | EPUB 3 com capa embutida — KDP digital |
| `<slug>-capa.pdf` / `.png` | a capa sozinha |

E `cover` acrescenta `<slug>-capa-kdp.pdf`: contracapa + lombada + capa,
com sangria, no tamanho exato da espessura do livro.

## Capa e ilustrações

A capa é **arte + tipografia**: a pipeline compõe título, subtítulo, autor e
coleção, e coloca no meio a imagem de `books/<slug>/assets/capa.png` (ou a
que estiver em `cover_image:`). As figuras dos capítulos entram como
`![alt](arquivo.png "legenda")` e saem numeradas por capítulo.

Enquanto a arte definitiva não chega, `python -m pipeline art <slug>` gera
placeholders locais em 300 DPI, na cor do volume — nada baixado, nada com
licença de terceiros.

No Windows com `make` disponível: `make setup`, `make book BOOK=java-one`,
`make kdp BOOK=java-one`.

## Onde mexer

| Quero… | Mexo em |
|---|---|
| escrever um livro | `books/<slug>/content/*.md` |
| mudar título, cor, ISBN | `books/<slug>/book.yaml` |
| mudar o visual de TODA a coleção | `collection/theme/tokens.yaml` |
| mudar como um componente se desenha | `collection/theme/templates/style.typ.j2` |
| criar um tipo de diagrama | `pipeline/diagrams.py` |
| criar uma checagem nova | `pipeline/validate.py` |

Nunca mexa em `build/` — é saída.

## Volume novo

```bash
python -m pipeline new python-one --title "Python One" --accent blue --volume 2
```

Cores disponíveis em `collection/theme/../collection.yaml → accents`:
`red · blue · green · orange · purple · teal · amber · slate`.

## Como escrever

O dialeto é Markdown mais contêineres `:::`. O modelo completo está em
[`books/_template/content/01-primeiro-capitulo.md`](books/_template/content/01-primeiro-capitulo.md)
e a lista de componentes em [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

```markdown
:::tip Leia a saída com desconfiança
`56.4` e não `56.40`. Java imprimiu o número, não o dinheiro.
:::

:::diagram type="flowchart" caption="Do texto ao programa."
nodes:
  - { id: src, type: io,      text: "App.java" }
  - { id: cc,  type: process, text: "javac App.java" }
edges:
  - { from: src, to: cc }
:::
```

## Traduções e prévias

O português é a língua oficial. Traduções moram em
`books/<slug>/i18n/<idioma>/` e herdam do original tudo que não é texto;
o slug é `<slug>-<idioma>` (`php-one-v1-en`, `php-one-v2-es`,
`php-one-v1-previa-en`). Prévias são só um `book.yaml` — o texto vem do
volume fonte, no idioma certo.

```bash
python -m pipeline i18n all               # o que falta e o que ficou velho
python -m pipeline build php-one-v1-en
```

Detalhes em [`docs/TRADUCOES.md`](docs/TRADUCOES.md).

## Arquitetura

[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — diretórios, modelo de dados,
componentes, tokens, fluxo, PDF, EPUB, validações e KDP.
# zero_one
