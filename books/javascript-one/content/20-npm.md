---
title: "npm"
number: 20
slug: npm
part: p6
kicker: "Atualizar o Axios de 0.21 para a versão atual levou um minuto. A lista de canceladas de Franca parou de carregar, e só ela."
goal: >-
  Ler o package.json e o package-lock.json, instalar de propósito, atualizar
  uma dependência vendo exatamente o que quebra, e sair de três clientes
  HTTP para um no caminho de uma chamada com nome — não numa faxina geral.
---

:::story Um minuto
Quarta, 15 de abril, 11h. O Neto passou pela mesa da Bia com o notebook
aberto num relatório de segurança.

— O Axios do painel. 0.21.1. Tem aviso de vulnerabilidade desde 2021.

— Ele só é usado num lugar — disse a Bia. — A busca de canceladas, em
`entrega.js`.

— Então atualiza.

Ela atualizou numa cópia de homologação. Um comando, um minuto. O painel
subiu. A lista da manhã carregou. A lista de canceladas de Franca ficou
vazia.

No log do servidor:

```text
SyntaxError: Unexpected token 'o', "[object Obj"... is not valid JSON
    at JSON.parse (<anonymous>)
    at filtrarEntregas (servidor/rotas.js:41:25)
```

— O servidor não mudou — disse ela.

O Rafael olhou o log.

— O servidor não mudou. O que o Axios manda, mudou.
:::

## O `package.json`, de novo

O capítulo @cap:o-que-vamos-construir leu o `package.json` do painel
pela primeira vez: o nome e uma dependência. O da pasta `borba`, até aqui,
tem o nome e o `"type": "module"` do capítulo anterior. Quando uma
biblioteca entra, ele ganha uma seção:

```text
$ npm install axios@0.21.1
added 2 packages in 1s
```

```json title="package.json"
{
  "name": "borba",
  "type": "module",
  "dependencies": {
    "axios": "^0.21.1"
  }
}
```

`npm install axios@0.21.1` baixa o Axios dessa versão do registro npm para
a pasta `node_modules/`, e anota a dependência no `package.json`. "2
packages": o Axios e uma biblioteca de que ele depende, que veio junto.

O `^` na frente da versão é uma **faixa**: aceita 0.21.1 e qualquer
versão posterior que não mude o número que importa. Para versões que
começam com zero, a regra do npm é estrita — `^0.21.1` aceita 0.21.2,
0.21.4, e não aceita 0.22. Para versões 1 em diante, `^1.6.0` aceita 1.7,
1.20, e não aceita 2.0.

A convenção por trás disso é a versão semântica: o primeiro número muda
quando algo pode quebrar quem usa; o segundo, quando algo é acrescentado;
o terceiro, quando algo é corrigido. É uma promessa de quem publica. Não é
uma garantia.

## O lockfile

A instalação criou outro arquivo, que ninguém escreveu:

```json title="package-lock.json (trecho)"
"node_modules/axios": {
  "version": "0.21.1",
  "resolved": "https://registry.npmjs.org/axios/-/axios-0.21.1.tgz",
  "integrity": "sha512-dKQiRHxGD9PPRIUNIWvZhPTPpl1rf/OxTY...",
  "dependencies": {
    "follow-redirects": "^1.10.0"
  }
}
```

O `package-lock.json` grava a versão **exata** de cada pacote instalado —
inclusive os que vieram junto —, de onde veio, e uma impressão digital do
arquivo (`integrity`). Com ele, outra máquina que instalar a partir da
pasta recebe exatamente os mesmos arquivos, e não "a mais nova que a
faixa aceitar".

:::term Lockfile
O arquivo que grava as versões exatas resolvidas numa instalação, para
todas as máquinas instalarem igual. No npm, `package-lock.json`. Vai para
o Git junto com o `package.json`.

O `package.json` diz o que o projeto aceita. O lockfile diz o que ele usa.
:::

Dois comandos, e a diferença entre eles:

**`npm install`** instala o que o `package.json` pede, respeitando o
lockfile quando ele existe, e pode atualizá-lo.

**`npm ci`** instala **exatamente** o lockfile, apaga o `node_modules/`
antes, e falha se o lockfile e o `package.json` discordarem. É o comando
do servidor e da esteira: nada é resolvido de novo.

A pasta `node_modules/` não vai para o Git. Ela é recriada a partir do
lockfile. O `.gitignore` do capítulo de Git diz isso numa linha.

## Onze linhas, em 2016

Uma dependência é código de outra pessoa, baixado de um registro público,
na hora da instalação. Em 22 de março de 2016, o autor de um pacote
chamado `left-pad` o retirou do registro npm, depois de uma disputa sobre
o nome de outro pacote dele. O `left-pad` tinha onze linhas: completava um
texto com espaços à esquerda. Milhares de projetos dependiam dele — a
maioria sem saber, porque ele vinha junto com outras dependências. Por
algumas horas, a instalação desses projetos falhou em todo lugar, até o
registro restaurar o pacote.

Depois disso, o npm passou a restringir a retirada de pacotes publicados.
O episódio ficou como a demonstração mais curta de uma coisa que continua
verdadeira: cada dependência é uma pessoa, um registro e uma rede entre o
seu `npm install` e o seu programa.

## Atualizar vendo o que quebra

O primeiro comando antes de atualizar:

```text
$ npm outdated
Package  Current  Wanted  Latest  Location
axios     0.21.1  0.21.4  1.x.x   node_modules/axios
```

`Current` é o instalado. `Wanted` é o mais novo que a faixa do
`package.json` aceita — 0.21.4, sem mudar o que importa. `Latest` é o mais
novo publicado: a linha 1. Para chegar ao 1, a faixa precisa mudar, e é
isso que o número de cima avisa: pode quebrar.

A Bia tinha rodado `npm install axios@latest`. A busca de canceladas de
Franca chamava o Axios assim:

```javascript title="entrega.js (trecho)"
axios.get("/entregas", {
  params: { cidade: "Franca", filtro: { status: "cancelada" } },
});
```

O `filtro` é um objeto dentro dos parâmetros. Cada versão do Axios monta o
endereço de um jeito:

```javascript title="endereco.js" numbered
import axios from "axios";

const url = axios.getUri({
  url: "/entregas",
  params: { cidade: "Franca", filtro: { status: "cancelada" } },
});
console.log(url);
```

```text
com axios 0.21.1:
/entregas?cidade=Franca&filtro=%7B%22status%22:%22cancelada%22%7D

com axios 1.x:
/entregas?cidade=Franca&filtro%5Bstatus%5D=cancelada
```

O 0.21 transformava o objeto em JSON e o mandava num parâmetro só —
`filtro={"status":"cancelada"}`, codificado. O 1 manda
`filtro[status]=cancelada`, outra convenção. O servidor de 2022 fazia
`JSON.parse(req.query.filtro)`, que funcionava com a primeira forma e
recebe, na segunda, algo que não é JSON.

O Axios documentou a mudança nas notas da versão 1. Ninguém no painel
leu, porque ninguém sabia que o painel dependia daquele detalhe.

:::key
Atualizar uma dependência é trocar código que você não leu por outro que
você não leu. Antes de atualizar, saiba **cada lugar** que a usa e **o
que** cada lugar espera dela. `npm outdated` diz o tamanho do salto;
`Latest` com o primeiro número diferente é um salto que pode quebrar.
:::

## De três clientes para um, numa chamada

A pasta de produção tem três jeitos de fazer pedido HTTP — a cena do
capítulo @cap:o-que-vamos-construir. A atualização do Axios foi a razão
concreta para escolher, e a escolha é o `fetch`, que a linguagem já traz,
e que não precisa de atualização de pacote nenhum.

A escolha **não** é uma faxina: trocar os três em todos os lugares numa
tarde, com a renovação da Mercado Leste em três semanas. É tirar o Axios
do caminho **de uma chamada com nome** — a busca de canceladas —, conferir
que ela manda exatamente o que mandava, e parar.

```javascript title="api.js" numbered
export function urlEntregas({ cidade, filtro }) {
  const params = new URLSearchParams({ cidade });
  if (filtro) {
    params.set("filtro", JSON.stringify(filtro));
  }
  return `/entregas?${params}`;
}

export async function buscarCanceladas(cidade) {
  const filtro = { status: "cancelada" };
  const url = urlEntregas({ cidade, filtro });
  const resposta = await fetch(url);
  return resposta.json();
}
```

`URLSearchParams` monta a parte do endereço depois do `?`, com a
codificação certa. `JSON.stringify` faz, de propósito e escrito, o que o
Axios 0.21 fazia por baixo: o filtro vai como JSON, o formato que o
servidor de 2022 lê.

E a conferência, a suíte mínima deste capítulo — um script que compara o
endereço novo com o que o Axios 0.21 montava:

```javascript title="confere-http.js" numbered
import axios from "axios";
import { urlEntregas } from "./api.js";

const params = { cidade: "Franca", filtro: { status: "cancelada" } };

const antigo = axios.getUri({ url: "/entregas", params });
const novo = urlEntregas(params);

const decodificar = (u) => decodeURIComponent(u);
console.log(decodificar(antigo));
console.log(decodificar(novo));
const iguais = decodificar(antigo) === decodificar(novo);
console.log(iguais ? "ok" : "DIFERENTE");
```

```text
$ node confere-http.js
/entregas?cidade=Franca&filtro={"status":"cancelada"}
/entregas?cidade=Franca&filtro={"status":"cancelada"}
ok
```

O script roda com o Axios 0.21 ainda instalado — é ele que diz como era.
Os dois endereços, decodificados, são iguais. A busca de canceladas passa
a usar `buscarCanceladas`, e o Axios deixa de estar no caminho dela.

Os outros usos — a pasta `http/` de 2022 e o `fetch` do Marcos em
`lista.js` — continuam onde estão, anotados num ticket. A Bia rodou
`npm ls axios` para confirmar quem ainda o puxava: ninguém mais na pasta
`borba`. O Axios saiu do `package.json` dela:

```text
$ npm uninstall axios
removed 2 packages in 1s
```

E o `confere-http.js`, que dependia dele para lembrar como era, foi
arquivado com o resultado `ok` colado no ticket.

:::summary
- `npm install pacote@versão` baixa e anota em `package.json`. `^` aceita
  atualizações que não mudam o primeiro número relevante.
- `package-lock.json` grava as versões exatas e vai para o Git;
  `node_modules/` não vai. `npm ci` instala exatamente o lockfile.
- 22 de março de 2016: o `left-pad`, onze linhas, saiu do registro e
  quebrou instalações pelo mundo.
- `npm outdated` mostra o salto. O Axios 1 mudou como monta objeto
  aninhado nos parâmetros, e o servidor de 2022 dependia da forma antiga.
- Sair de três clientes para um é por chamada com nome, conferida, e não
  por faxina.
:::

:::exercise level=1
Para cada faixa, diga se a versão 0.21.4 e a versão 1.6.0 são aceitas:

```json
"axios": "^0.21.1"
"axios": "~0.21.1"
"axios": "0.21.1"
```

:::answer
- `^0.21.1`: 0.21.4 sim; 1.6.0 não. Com versão começando em zero, o `^`
  trava o segundo número.
- `~0.21.1`: 0.21.4 sim; 1.6.0 não. O `~` aceita só mudanças no último
  número.
- `0.21.1`: nenhuma das duas. Sem símbolo, é a versão exata.
:::

:::exercise level=2
O Neto roda, no servidor, `npm install` em vez de `npm ci`. Diga o que
pode acontecer de diferente, e por que o `ci` existe.

:::answer
`npm install` pode resolver versões de novo, dentro das faixas do
`package.json`, e atualizar o lockfile no próprio servidor. Um pacote que
publicou uma correção ontem entra no servidor sem ter passado por nenhuma
máquina de desenvolvimento.

`npm ci` instala exatamente o que o lockfile diz, e falha se ele não
bater com o `package.json`. O servidor roda o que foi testado. É o mesmo
motivo do lockfile existir: o que a máquina da Bia rodou é o que o
servidor roda.
:::

:::exercise level=3
O Marcos propõe aproveitar a semana e trocar os três clientes HTTP da
produção por `fetch`, "já que o Axios saiu". Faltam três semanas para 6
de maio. Responda, com o que você faria nesta semana e o que ficaria para
depois.

:::answer
Nesta semana, nada além do que foi feito: a busca de canceladas saiu do
Axios, conferida. O Axios de produção continua anotado no ticket de
segurança, com a lista de onde ele ainda é usado.

A troca geral fica para depois de 6 de maio, uma chamada por vez, cada
uma com o seu `confere`. Cada chamada tem detalhes que o `fetch` faz
diferente — o objeto aninhado nos parâmetros foi só o primeiro. O `fetch`
não rejeita a promessa em resposta `404`, por exemplo, e o Axios rejeita:
todo `catch` que esperava o erro do Axios passaria a não ser chamado.

Três clientes são uma dívida. Trocar os três com a cláusula de trinta
segundos entrando em vigor é pagar a dívida pegando outra, maior, com
juros de R$ 3,50 por status.
:::
