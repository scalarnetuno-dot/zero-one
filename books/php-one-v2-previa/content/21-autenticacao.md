---
title: "Autenticação com Sanctum"
number: 21
slug: autenticacao
part: p5
kicker: "O Sistema guardava as senhas em MD5, sem sal. Na hora do almoço, na máquina de um desenvolvedor, sessenta por cento caíram em quatro minutos."
goal: >-
  Responder "quem é você" com segurança: guardar senha do jeito certo,
  migrar as que estão erradas, emitir e revogar tokens com Sanctum, e
  escrever um login cuja resposta de erro não entrega nada — nem no texto,
  nem no tempo.
previa: true
---

## Senha nunca é guardada

## `bcrypt`, `argon2` e o custo que é proposital

### Migrar as senhas do Sistema

## Sessão e token: dois problemas diferentes

## Sanctum

## Login, logout e `GET /eu`

## Revogar de verdade

## A resposta que não diz se o e-mail existe
