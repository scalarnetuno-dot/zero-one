# Zero One — arquitetura da pipeline editorial

Um sistema pequeno que produz muitos livros. A regra que sustenta tudo:
**o livro é dado; o layout é o sistema.** Um volume novo não traz código
novo — traz um `book.yaml`, arquivos `.md` e uma cor.

---

## 1. Estrutura de diretórios

```
zero_one/
├── collection/                    O SISTEMA (compartilhado por todos os volumes)
│   ├── collection.yaml            identidade, rótulos por idioma, cores
│   └── theme/
│       ├── tokens.yaml            ← fonte única da verdade visual
│       ├── fonts/                 IBM Plex (OFL), baixadas por _fetch.py
│       └── templates/
│           ├── style.typ.j2       design system → Typst (miolo)
│           ├── cover.typ.j2       capa: modo `front` e modo `wrap` (KDP)
│           └── epub/style.css.j2  design system → CSS (EPUB)
│
├── pipeline/                      O CÓDIGO (≈1.800 linhas, sem framework)
│   ├── model.py                   AST semântico
│   ├── parser.py                  Markdown + diretivas ::: → AST
│   ├── theme.py                   tokens + cor do volume → Theme
│   ├── diagrams.py                spec → geometria
│   ├── render_typst.py            AST → .typ
│   ├── render_epub.py             AST → EPUB 3 (+ SVG + Pygments)
│   ├── validate.py                revisor automático
│   ├── cover.py                   capa front/wrap + lombada pelo nº de páginas
│   ├── placeholder.py             arte provisória gerada localmente
│   ├── loader.py                  book.yaml + content/ → Book
│   ├── build.py                   orquestração (2 passagens)
│   └── cli.py                     python -m pipeline ...
│
├── books/
│   ├── _template/                 esqueleto de volume novo
│   ├── java-one/                  vol. 1 — laranja
│   │   ├── book.yaml              metadados + cor + ordem dos capítulos
│   │   ├── content/*.md           o livro
│   │   └── assets/                capa.png e figuras deste volume
│   └── python-one/                vol. 2 — azul (esqueleto)
│
├── build/<slug>/                  <slug>-leitura.pdf · <slug>.pdf ·
│                                  <slug>.epub · capa · typst/ (gerado)
└── docs/
```

Cada livro tem sua pasta. O layout é um só.

---

## 2. Modelo de dados

O parser não devolve HTML nem Typst: devolve um **AST semântico**
(`pipeline/model.py`). Nenhum nó sabe o que é milímetro.

```
Book
 ├── BookMeta        título, subtítulo, autor, volume, accent, idioma, ISBN…
 ├── Part[]          opcional
 └── Chapter[]       number, title, slug, kicker, matter(front|body|back)
      └── Block[]
           Heading · Paragraph · CodeBlock · Figure · Diagram · Callout
           Example · Exercise · Summary · ListBlock · Table · Quote · Term · Rule
```

Inline: `Text · Strong · Em · Code · Link · Ref`.

Dois detalhes que valem o preço:

- **`Exercise.answer`** guarda a resposta junto do exercício. A pipeline a
  recolhe e monta o apêndice “Respostas” sozinha.
- **`Term`** alimenta o glossário automático. O autor escreve o verbete
  onde ele faz sentido; o livro o organiza no fim.

---

## 3. Componentes mínimos

Quinze, e a regra é não crescer. Caixa nova é dívida de design.

| # | Componente | Markdown do autor |
|---|---|---|
| 1 | ChapterOpener | front matter (`title`, `number`, `kicker`) |
| 2 | Section / Subsection | `##`, `###`, `####` |
| 3 | Paragraph | texto |
| 4 | CodeBlock | ` ```java title="App.java" numbered ` |
| 5 | Figure | `![alt](imagem.png "legenda")` |
| 6 | Diagram | `:::diagram type="flowchart"` |
| 7 | Callout ×5 | `:::tip` `:::warning` `:::note` `:::key` `:::practice` |
| 8 | Example | `:::example Título` |
| 9 | Exercise (+answer) | `:::exercise level=2` |
| 10 | Summary | `:::summary` |
| 11 | Table | tabela Markdown + linha `Table:` |
| 12 | Quote | `> …` com `— atribuição` |
| 13 | Term | `:::term Palavra` |
| 14 | List | `-` e `1.` |
| 15 | Rule | `---` |

Mais a **capa**, que é gerada do mesmo design system e entra no PDF de
leitura e no EPUB.

Páginas de apoio (não são conteúdo, são sistema): folha de rosto, página
de crédito, sumário, abertura de parte, Respostas, Glossário, capa.

---

## 4. Sistema de estilos

`collection/theme/tokens.yaml` é o único lugar com valor visual. Ele define
página, margens, escala tipográfica, pesos, cores, espaços, fios, paleta de
código, geometria de diagrama e as regras do EPUB.

O fluxo é este:

```
tokens.yaml ──┬── style.typ.j2  → style.typ   (componentes do PDF)
              ├── editorial.tmTheme           (realce de sintaxe do PDF)
              ├── epub/style.css.j2 → style.css
              └── diagrams.py                 (geometria dos diagramas)
```

A mesma paleta de código vira tema TextMate no PDF e classes CSS no EPUB:
verde de string é o mesmo verde nos dois meios, porque sai do mesmo token.

**Preto, branco e neutros.** Cada volume escolhe **uma** cor em
`collection.yaml → accents`, e ela só aparece em: número do capítulo,
numeração de seção, fio de 22 mm, rótulo de figura, número de exercício,
barra de duas caixas e lombada. Nunca como fundo de página.

Tipografia: **IBM Plex Serif** no corpo (10 pt / 0.78em), **IBM Plex Sans**
nos títulos e rótulos, **IBM Plex Mono** no código. Todas OFL — livres para
incorporar em PDF comercial, o que a KDP exige.

---

## 5. Fluxo de processamento

```
books/<slug>/content/*.md + book.yaml
        │
        ▼  parser.py           front matter + blocos + diretivas
   AST semântico (model.py)
        │
        ▼  validate.py         31 checagens antes de qualquer render
        │
        ├─► render_typst.py ──► .typ ──► typst (embutido) ──► PDF
        │        └── diagrams.py devolve geometria; o PDF desenha com
        │            primitivas do Typst (fonte real, vetor real)
        │
        └─► render_epub.py ──► XHTML + CSS + SVG + Pygments ──► EPUB 3
```

O conteúdo nunca conhece o destino. Adicionar HTML, site ou áudio amanhã é
escrever um renderizador novo, não mexer no conteúdo.

---

## 6. Estratégia de PDF

**Motor: Typst, via `pip install typst`.** Sem LaTeX, sem Chrome headless,
sem instalação de sistema — o compilador vem dentro do pacote Python.

O que isso resolve de graça e seria caro fazer à mão:

- viúvas e órfãs, hifenização em português, justificação de verdade;
- cabeçalho corrente que muda por capítulo e some na abertura;
- margem espelhada (`inside`/`outside`) para livro encadernado;
- numeração de figura e tabela reiniciada por capítulo;
- sumário com página real, gerado do próprio documento.

**Duas passagens.** A primeira compila e conta as páginas; a KDP exige
margem interna maior conforme o livro engorda (`page.gutter_steps`). Se a
faixa mudou, a pipeline reescreve o `.typ` e compila de novo. Um livro de
38 páginas e um de 480 saem com a lombada certa sem ninguém pensar nisso.

**Blocos que não podem quebrar.** Código com até 26 linhas e caixas com até
600 caracteres viram blocos inquebráveis: rótulo sozinho no pé da página é
defeito, não estilo.

**Capa**: um desenho, dois recortes (`collection/theme/templates/cover.typ.j2`).

- `front` — uma página no tamanho do miolo. Vira a **página 1 do
  `<slug>-leitura.pdf`** (o livro já sai com capa) e, em PNG de 300 DPI, a
  capa do EPUB.
- `wrap` — contracapa + lombada + capa, com sangria de 3,175 mm, para a KDP
  impressa. A lombada mede `páginas × 0,0572 mm` (papel branco), por isso só
  pode ser gerada depois do miolo: `python -m pipeline cover <slug>`.

O miolo enviado à KDP **não** contém a capa — a Amazon rejeita. Por isso são
dois PDFs: `<slug>.pdf` (miolo) e `<slug>-leitura.pdf` (capa + miolo).

**Imagens**: a arte da capa é `assets/capa.png` (ou `cover_image:` no
`book.yaml`); as figuras entram por `![alt](arquivo.png "legenda")` e são
copiadas para o build. Enquanto a arte final não existe,
`python -m pipeline art <slug>` desenha placeholders em 300 DPI na cor do
volume (`pipeline/placeholder.py`) — gerados localmente, sem licença de
terceiros.

---

## 7. Estratégia de EPUB

EPUB 3 montado com a biblioteca padrão (`zipfile`) — sem dependência de
empacotador. Um XHTML por capítulo, `nav.xhtml`, `content.opf`,
`META-INF/container.xml`, `mimetype` gravado sem compressão.

Diferenças deliberadas em relação ao PDF, todas vindas dos tokens:

| | PDF | EPUB |
|---|---|---|
| Parágrafo | recuo de 5 mm | espaço de 0,75em |
| Diagrama | vetor Typst | o mesmo cálculo, em SVG |
| Código | tema TextMate | classes `.tok-*` |
| Tema escuro | não existe | `prefers-color-scheme` |

O mesmo `diagrams.py` produz as duas versões: a geometria é calculada uma
vez e apenas o traço muda.

---

## 8. Validações automáticas

`python -m pipeline check <slug>` — três níveis: **erro** (para o build com
`--strict`), **aviso**, **nota**.

No AST, antes de compor:

- capítulo vazio, sem título, com slug repetido ou curto demais;
- capítulo sem `:::summary`;
- título órfão (seção sem conteúdo) e salto de nível (`##` → `####`);
- linha de código mais larga que a mancha (`code.max_line_chars`);
- bloco de código vazio ou sem linguagem;
- imagem ausente no disco e imagem abaixo de 300 DPI no tamanho impresso;
- figura sem legenda; diagrama inválido ou alto demais para a página;
- tabela sem cabeçalho, com linha de tamanho diferente ou colunas demais;
- referência cruzada sem alvo (`@fig:x`, `@ex:y`);
- exercício sem resposta; lista de um item só; parágrafo vazio.

No PDF pronto:

- página com tamanho diferente do trim declarado (erro);
- total ímpar de páginas (a gráfica acrescenta folha);
- menos de 24 páginas (mínimo da KDP);
- páginas sem texto (as de abertura são intencionais e ficam listadas).

Mais os avisos do próprio Typst, repassados ao terminal.

---

## 9. Exemplo de um capítulo

```markdown
---
title: "Decidir"
number: 3
kicker: "Escolher um caminho é assumir o outro."
---

Até agora o programa fazia sempre a mesma coisa.

## `if` pede um `boolean`

```java title="Maioridade.java" numbered
if (idade >= 18) {
    System.out.println("Pode entrar");
}
```

:::diagram type="flowchart" caption="Toda decisão tem dois caminhos."
nodes:
  - { id: d1,  type: decision, text: "idade >= 18?" }
  - { id: sim, type: process,  text: "Pode entrar" }
edges:
  - { from: d1, to: sim, label: "sim" }
:::

:::warning
`==` compara referências. Para texto, use `equals`.
:::

:::summary
- `if` exige `boolean`; número não vale como condição.
:::

:::exercise level=2
Calcule a tarifa do estacionamento.

:::answer
O teto entra depois do cálculo, como uma segunda decisão.
:::
```

O autor nunca escreve tamanho, cor, posição ou quebra de página.

---

## 10. Exemplo de configuração de um livro

```yaml
title: "Java One"
subtitle: "O compilador como colega"
author: "Thiago Pablicio"
volume: 1
accent: orange
language: pt-BR
year: 2026
edition: "1ª edição"
isbn: ""
description: >-
  Java do zero sem IDE de quatro gigabytes e sem Spring no primeiro dia.
keywords: [Java, programação, iniciantes]
cover_bullets:
  - "Um arquivo, um main, nenhum framework"
course_slug: java-one
chapters:
  - 00-antes-de-comecar.md
  - 01-a-porta.md
```

É o arquivo inteiro. Não há CSS, não há template, não há layout.

---

## 11. Um volume novo, sem duplicar código

```bash
python -m pipeline new python-one --title "Python One" --accent blue --volume 2
# escreva books/python-one/content/*.md
python -m pipeline build python-one
python -m pipeline cover python-one
```

O que o volume novo traz: metadados, cor, texto e imagens.
O que ele **não** traz: layout, componente, CSS, template ou script.

Mudar o miolo de 6×9 para 5,5×8,5 em toda a coleção é editar duas linhas de
`tokens.yaml` e rodar `python -m pipeline build all`.

---

## Decisões e seus porquês

| Decisão | Por quê |
|---|---|
| Typst e não LaTeX/HTML→PDF | um `pip install`, sem instalação de sistema, e tipografia de livro de verdade |
| Diagrama como dado, não como imagem | o mesmo diagrama sai vetorial no PDF e em SVG no EPUB, com a fonte do livro |
| Parser próprio (≈300 linhas) | o AST precisa ser semântico; converter tokens de uma lib de Markdown daria mais código, não menos |
| Tokens em YAML | o design system precisa ser legível por quem não programa |
| Validador antes do render | erro de diagramação é mais barato no terminal do que na prova impressa |
| IBM Plex | superfamília OFL (serif + sans + mono) com licença clara para PDF comercial |

## O que falta (nesta ordem)

1. Importador `course_slug` → capítulos: ler `production_courses/<slug>/unit*.json`
   e gerar o rascunho dos `.md`.
2. Tradução: `books/<slug>/content/<lang>/` + `pipeline translate`, no modelo
   do V4 (fonte pt-BR, alvos revisáveis, build por idioma).
3. Renderizador HTML (mesmo AST) para a versão web de cada volume.
4. `Part` (abertura de parte) já existe no modelo e no `style.typ`, mas ainda
   não é lida do `book.yaml`.
