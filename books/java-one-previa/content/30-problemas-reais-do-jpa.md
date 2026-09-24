---
title: "Problemas reais do JPA"
number: 30
part: p6
kicker: "O ORM faz exatamente o que você mandou. O problema é que você mandou sem saber."
epigraph: "Toda abstração não trivial vaza."
epigraph_by: "Joel Spolsky, lei das abstrações vazadas"
goal: >-
  Diagnosticar o problema N+1 pelo log, escolher entre `JOIN FETCH` e
  `@EntityGraph`, e explicar `LazyInitializationException` sem adivinhação.
previa: true
---

## O problema N+1

## As três soluções

## `LazyInitializationException`

## Transação: onde ela começa e onde termina

## O checklist do JPA em produção
