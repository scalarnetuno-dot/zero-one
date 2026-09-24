---
title: "Service Container e injeção de dependência"
number: 18
slug: service-container
part: p5
kicker: "Dedé abriu o contêiner de vinte linhas ao lado do contêiner do Laravel. A estagiária reconheceu a reflexão antes dele apontar."
goal: >-
  Entender o mecanismo que monta os objetos da aplicação, declarar
  dependência pelo construtor, escolher entre bind, singleton e scoped, e
  trocar uma implementação no teste sem tocar em quem a usa.
previa: true
---

## O `new` espalhado pelo código é o problema

## Pedir em vez de montar

## O contêiner monta o grafo

### Autowiring, e onde ele para

## `bind`, `singleton` e `scoped`

## Service Provider: onde as instruções moram

### `register` e `boot`

## Interface no construtor, implementação no provider

## Trocar a implementação no teste

## As duas formas de usar o contêiner errado
