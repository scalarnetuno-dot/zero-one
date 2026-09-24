---
title: "Testes de feature, HTTP e banco"
number: 26
slug: testes-de-feature-http-e-banco
part: p7
kicker: "A esteira ficou vermelha por três dias num teste que passava em toda máquina local. Faltava um ORDER BY — no teste e no código."
goal: >-
  Verificar o contrato da API de ponta a ponta e as garantias que só o banco
  dá: requisições reais contra rotas reais, banco isolado a cada teste,
  permissões provadas pelo lado da recusa, e fakes de infraestrutura que não
  escondem o que deveriam testar.
previa: true
---

## `getJson`, `postJson` e o contrato verificado

## `RefreshDatabase`: isolamento sem `TRUNCATE`

### SQLite em memória, e onde ele mente

## `actingAs` e o teste de rota protegida

## Testar `403` é testar o que ninguém testa à mão

## O campo que nunca pode aparecer

## `assertDatabaseHas` e o que ele prova

## Fake de fila, e-mail e evento

## Suíte lenta: diagnosticar antes de culpar o banco

## A correção da esteira vermelha
