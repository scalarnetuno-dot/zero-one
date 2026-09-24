---
title: "Cache, logs e o que se mede"
number: 24
slug: cache-logs-e-medicao
part: p6
kicker: "A página do acervo ficou rápida e passou a mostrar como disponível um livro que estava emprestado. Por seis horas, que era o tempo de validade do cache."
goal: >-
  Tornar a aplicação observável e rápida, nessa ordem: medir antes de
  otimizar, cachear com uma estratégia de invalidação escrita, e registrar
  logs estruturados que dá para procurar — sem nunca gravar o que não pode
  ser gravado.
previa: true
---

## Uma fila existe porque esperar custa caro; um cache também

## Medir antes de otimizar

## `Cache::remember` e a pergunta difícil

### Invalidação por tempo e por evento

## Cache de configuração, rota e view

## Log não é `dd()`

## Níveis, canais e o log que dá para procurar

## O que nunca entra no log
