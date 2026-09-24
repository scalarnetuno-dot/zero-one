---
title: "Events, jobs e filas"
number: 23
slug: events-jobs-e-filas
part: p6
kicker: "O aviso de devolução foi enviado 1.400 vezes para a mesma pessoa. O job não era idempotente, e o worker reiniciou no meio."
goal: >-
  Tirar da requisição o trabalho que não precisa acontecer antes da
  resposta, desacoplar com eventos sem esconder o fluxo, rodar filas com
  worker que reinicia no deploy, e escrever jobs que podem falhar, voltar e
  rodar de novo sem repetir o efeito.
previa: true
---

## O que não precisa acontecer antes da resposta

## Event e listener: desacoplar sem esconder

## Job: a unidade de trabalho que pode falhar e voltar

## Driver de fila: `sync`, `database`, `redis`

## Worker, supervisor e o processo que precisa reiniciar

## Retentativa, `backoff` e `failed_jobs`

## Job precisa ser idempotente

## Quando o evento vira espaguete invisível
