# Traduções

O **português (pt-BR) é a língua oficial** da coleção. Todo livro nasce,
é revisado e muda primeiro em `books/<slug>/`. As traduções acompanham o
original — nunca o contrário.

## Onde mora cada coisa

```
books/php-one-v1/                 ← fonte oficial, em português
├── book.yaml
├── content/*.md
├── assets/                       ← imagens compartilhadas por todos os idiomas
└── i18n/
    ├── en/
    │   ├── book.yaml             ← só os campos traduzidos
    │   ├── GLOSSARY.md           ← nomes de código e termos, fixos no volume
    │   ├── content/*.md          ← MESMOS nomes de arquivo do original
    │   └── assets/               ← (opcional) arte com texto localizado
    └── es/ …

books/php-one-v1-previa/          ← prévia: só um book.yaml + JPEG leves
├── book.yaml
├── assets/*.jpg                  ← gerados por `make preview`, servem a todos os idiomas
└── i18n/en/book.yaml             ← título/descrição da prévia em inglês
```

O slug de uma tradução é `<slug>-<idioma>`:

| Slug | O que é |
|---|---|
| `php-one-v1` | volume 1, português (oficial) |
| `php-one-v1-en` · `php-one-v1-es` | volume 1 em inglês · espanhol |
| `php-one-v1-previa` | prévia do volume 1, português |
| `php-one-v1-previa-en` · `-es` | a mesma prévia, nos outros idiomas |
| `php-one-v2-en` · `php-one-v2-es` | volume 2 em inglês · espanhol |

## Por que é econômico

- **Nada é duplicado.** A tradução não copia imagem, capítulo, estrutura
  nem configuração: herda tudo do original e sobrepõe só o texto.
- **Estrutura vem do original.** `number`, `slug`, `part`, `matter` e
  `numbered` de cada capítulo são sempre os do português — `@cap:` funciona
  igual em todos os idiomas, e mover um capítulo no original move em todos.
- **Prévia não guarda texto.** A prévia é um `book.yaml` com
  `preview_chapters`; o loader lê o volume fonte (no idioma certo) e fecha,
  na hora, os capítulos que não estão liberados. Os JPEG leves da prévia
  servem a todos os idiomas.
- **Só se retraduz o que mudou.** Cada capítulo traduzido guarda
  `source_hash` — a impressão digital do original de que partiu. Mudou o
  português, o capítulo aparece como desatualizado; o resto fica quieto.
- **Capítulo que falta não quebra o build.** Sai o original em português,
  com aviso no `check`. Um idioma pode nascer aos poucos.

## Fluxo

```bash
python -m pipeline i18n all                  # situação de todos os idiomas
python -m pipeline i18n php-one-v1-en        # só um idioma
python -m pipeline i18n php-one-v1 --new fr  # abre uma tradução nova

# depois de traduzir ou atualizar capítulos:
python -m pipeline i18n php-one-v1-en --stamp        # marca todos como em dia
python -m pipeline i18n php-one-v1-en --stamp 08 11  # só os capítulos 08 e 11

python -m pipeline build php-one-v1-en
python -m pipeline build php-one-v1-previa-en
```

Atalhos: `make i18n`, `make book BOOK=php-one-v1-en`.

## Regras de tradução

1. **Traduza do português**, sempre — nunca de outra tradução.
2. **Mesmo arquivo, mesma estrutura.** Mesmos títulos de seção na mesma
   ordem, mesmos blocos `:::`, mesmos diagramas, mesmas figuras.
3. **Código também se traduz**: identificadores, comentários, textos
   impressos e a saída mostrada. Um leitor em inglês não deveria ler
   `$emprestimo`. O `GLOSSARY.md` do idioma fixa cada nome — `tombo` é
   sempre o mesmo nome em todos os capítulos dos dois volumes.
4. **Não se traduz**: nomes próprios (Casa Amarela, Vera, Tainá, Dedé),
   títulos de livros do acervo, palavras-chave da linguagem, nomes de
   funções do PHP, comandos, SQL reservado, nomes de pacotes, arquivos de
   imagem (`src=`) e os campos estruturais do front matter.
5. **O humor se adapta**, não se decalca: a mesma cena, o mesmo número, o
   mesmo silêncio — com a frase que funciona no idioma.
6. **Moeda e datas** continuam as do Brasil (a história se passa lá): o
   leitor estrangeiro lê `R$` como leria `¥` num livro japonês.
7. **Arte com texto** (capas, ilustrações com letreiro) é localizada em
   `i18n/<idioma>/assets/` com o **mesmo nome de arquivo**. Sem arte
   localizada, a capa sai só tipográfica, com o título traduzido; as
   ilustrações usam a arte original.

## Idiomas disponíveis

Os rótulos do sistema ("Capítulo", "Sumário", "Dica"…) ficam em
`collection/collection.yaml → strings`. Hoje: `pt-BR`, `en`, `es`. Um
idioma novo pede um bloco novo ali mais a pasta `i18n/<idioma>/`.
