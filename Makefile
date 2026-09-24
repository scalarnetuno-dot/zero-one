# Coleção Zero One — atalhos.
#
#   make setup             instala dependências e baixa as fontes
#   make list              lista os volumes
#   make check BOOK=java-one
#   make preview BOOK=java-one  gera java-one-previa
#   make i18n                    situação das traduções (pt-BR é a fonte)
#   make book  BOOK=php-one-v1-en   um volume traduzido
#   make book  BOOK=java-one     PDF + EPUB
#   make cover BOOK=java-one     capa da KDP (depois do build)
#   make kdp   BOOK=java-one     miolo + capa, prontos para subir
#   make all                     todos os volumes
#   make clean BOOK=java-one

PYTHON ?= python
BOOK   ?= java-one

.DEFAULT_GOAL := help
.PHONY: help setup list check preview book cover kdp all clean fonts i18n

help:
	@$(PYTHON) -c "print(open('Makefile', encoding='utf-8').read().split('\n\n')[0])"

setup: fonts
	$(PYTHON) -m pip install -r requirements.txt

fonts:
	$(PYTHON) collection/theme/fonts/_fetch.py

list:
	@$(PYTHON) -m pipeline list

check:
	$(PYTHON) -m pipeline check $(BOOK)

preview:
	$(PYTHON) -m pipeline preview $(BOOK)
	$(PYTHON) -m pipeline build $(BOOK)-previa

i18n:
	$(PYTHON) -m pipeline i18n all

book:
	$(PYTHON) -m pipeline build $(BOOK)

cover:
	$(PYTHON) -m pipeline cover $(BOOK)

kdp: book cover
	@$(PYTHON) -c "from pathlib import Path; d=Path('build/$(BOOK)'); \
print('pronto para a KDP:'); \
[print('  ', p) for p in sorted(d.glob('*.pdf')) + sorted(d.glob('*.epub'))]"

all:
	$(PYTHON) -m pipeline build all

clean:
	$(PYTHON) -m pipeline clean $(BOOK)
