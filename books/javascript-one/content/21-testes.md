---
title: "Testes"
number: 21
slug: testes
part: p6
kicker: "O Paulo cancelou a entrega no intervalo entre o clique em iniciar rota e a resposta do servidor. A entrega cancelada voltou a aparecer a caminho."
goal: >-
  Escrever um teste com node:test que falha pelo motivo certo e passa
  quando o código muda; testar o intervalo que ninguém imaginou, e não um
  espelho do caminho feliz; e saber o que um teste verde afirma.
---

:::story O intervalo
Sexta, 17 de abril, 10h. O Paulo sentou ao lado da Bia com o celular de
teste do motorista numa mão e o notebook na outra.

— Olha. No celular, eu inicio a rota da E-5701. — Tocou. — No notebook,
antes de o celular terminar de gravar, eu cancelo.

Clicou. A linha ficou riscada.

— Agora espera.

Um segundo depois, a linha deixou de estar riscada. "A caminho".

— A gravação da rota voltou depois do cancelamento — disse a Bia. — E
escreveu por cima.

— O motorista vai até a loja — disse o Paulo. — A loja cancelou.

— Quanto tempo tem esse intervalo?

— Com o 4G do cais, até dois segundos. Eu fiz isso onze vezes hoje de
manhã.

— Você jurou que ia achar alguma coisa.

— Eu sempre juro.
:::

## Um teste é uma afirmação que roda

Até aqui, a conferência de cada capítulo era um `console.log` e um par de
olhos: rodar, ler a saída, ver que está certa. Funciona uma vez. Não
funciona na décima alteração, quando ninguém lembra mais qual saída era a
certa.

Um **teste** é um programa que roda o código e **confere** o resultado
sozinho, e diz passou ou falhou. O Node traz o que é preciso, sem
instalar nada: o módulo `node:test`.

```javascript title="test/frete.test.js" numbered
import { test } from "node:test";
import assert from "node:assert/strict";
import { calcularFrete } from "../frete.js";

test("Franca, 8 kg, sem urgência", () => {
  const frete = calcularFrete({ cidade: "Franca", pesoKg: 8 });
  assert.equal(frete, 2160);
});
```

```text
$ node --test
✔ Franca, 8 kg, sem urgência (0.6ms)
ℹ tests 1
ℹ pass 1
ℹ fail 0
```

`test(nome, função)` registra um teste. O nome é uma frase: diz o que está
sendo afirmado. `assert.equal(atual, esperado)` confere que os dois são
iguais — com `===`, porque o módulo é o `assert/strict`. Se não forem, o
teste falha, com os dois valores na mensagem.

`node --test` procura os arquivos de teste da pasta — os que terminam em
`.test.js`, entre outros — e roda todos. No `package.json`, a casa deixa
isso com nome:

```json title="package.json"
{
  "name": "borba",
  "type": "module",
  "scripts": {
    "test": "node --test"
  }
}
```

E `npm test` passa a rodar a suíte. É o comando que o Neto vai pedir antes
de qualquer coisa subir.

:::term Teste
Um programa que executa um pedaço do sistema e confere o resultado com
uma afirmação. Passa se a afirmação vale; falha, com os valores, se não.

Um teste verde afirma o que o nome dele diz, e nada além. `calcularFrete`
passar para Franca não diz nada sobre São Carlos.
:::

## O teste do caso do Paulo

O defeito do intervalo, reproduzido com o painel escrito para ser testado:
o servidor entra como um parâmetro, e o teste entrega um servidor falso,
que demora o quanto o teste mandar.

```javascript title="painel.js" numbered
export function criarPainel(servidor, inicial) {
  const entregas = new Map(Object.entries(inicial));

  function status(codigo) {
    return entregas.get(codigo);
  }

  async function iniciarRota(codigo) {
    await servidor.gravar(codigo, "a caminho");
    entregas.set(codigo, "a caminho");
  }

  async function cancelar(codigo) {
    entregas.set(codigo, "cancelada");
    await servidor.gravar(codigo, "cancelada");
  }

  return { status, iniciarRota, cancelar };
}
```

`Map` guarda pares de chave e valor, como um objeto, com métodos `get` e
`set`. `Object.entries` transforma o objeto inicial na lista de pares que
o `Map` aceita. O painel é criado por uma função — a closure do capítulo
@cap:closures guarda as entregas —, e o servidor vem de fora. É isso que
deixa o teste controlar o tempo.

```javascript title="test/intervalo.test.js" numbered
import { test } from "node:test";
import assert from "node:assert/strict";
import { criarPainel } from "../painel.js";

function servidorLento(ms) {
  return {
    gravar: () => new Promise((r) => setTimeout(r, ms)),
  };
}

test("iniciar rota muda para a caminho", async () => {
  const painel = criarPainel(servidorLento(10), {
    "E-5701": "separada",
  });

  await painel.iniciarRota("E-5701");

  assert.equal(painel.status("E-5701"), "a caminho");
});

test("cancelar enquanto a rota ainda grava", async () => {
  const painel = criarPainel(servidorLento(50), {
    "E-5701": "separada",
  });

  const gravando = painel.iniciarRota("E-5701");
  await painel.cancelar("E-5701");
  await gravando;

  assert.equal(painel.status("E-5701"), "cancelada");
});
```

O primeiro teste é o caminho feliz. O segundo é o Paulo: inicia a rota
**sem esperar** — guarda a promessa em `gravando` —, cancela, e só então
espera a rota terminar. O servidor falso demora 50 ms, e o cancelamento
acontece dentro desse intervalo.

```text
$ npm test
✔ iniciar rota muda para a caminho (11.8ms)
✖ cancelar enquanto a rota ainda grava (51.4ms)
ℹ tests 2
ℹ pass 1
ℹ fail 1

✖ failing tests:

test at test/intervalo.test.js:21:1
✖ cancelar enquanto a rota ainda grava (51.4ms)
  AssertionError [ERR_ASSERTION]: Expected values to be strictly
  equal:
  + actual - expected

  + 'a caminho'
  - 'cancelada'
```

Vermelho, **pelo motivo certo**: a entrega terminou `'a caminho'`, e o
teste esperava `'cancelada'`. É o que o Paulo viu no notebook, agora numa
linha que qualquer um roda.

:::key
Um teste novo precisa ser visto falhando antes de passar. Um teste que
nunca falhou pode estar afirmando nada — um `assert` com a variável
errada, uma função que nunca é chamada. O vermelho com os valores certos
na mensagem é a prova de que o teste enxerga o defeito.
:::

## A correção

A gravação da rota volta **depois** do cancelamento, e escreve sem
perguntar. A regra da Lívia: uma mudança feita enquanto a gravação estava
no ar é mais nova, e vence.

```javascript title="painel.js" numbered
async function iniciarRota(codigo) {
  const antes = entregas.get(codigo);
  await servidor.gravar(codigo, "a caminho");
  if (entregas.get(codigo) !== antes) {
    return;
  }
  entregas.set(codigo, "a caminho");
}
```

A função guarda o status de antes de pedir. Quando a resposta volta,
confere se alguém mudou a entrega no meio. Se mudou, não escreve. É a
rodada do capítulo @cap:promises, aplicada a uma entrega só.

```text
$ npm test
✔ iniciar rota muda para a caminho (11.8ms)
✔ cancelar enquanto a rota ainda grava (52.7ms)
ℹ tests 2
ℹ pass 2
ℹ fail 0
```

Verde. E os dois testes ficam na pasta: se alguém, daqui a um mês,
"simplificar" `iniciarRota` tirando o `if`, o segundo fica vermelho antes
de a Lívia ver a entrega cancelada voltar.

## O que testar

O primeiro teste — iniciar rota muda para a caminho — é o espelho do
código: repete, em forma de afirmação, o que a função obviamente faz. Ele
tem valor pequeno. Ele pega quem apagar a linha do `set`.

O segundo é o que ninguém tinha imaginado, e é por isso que vale. A regra
da casa, depois do Paulo:

- um teste para cada defeito que chegou à Lívia, escrito **antes** da
  correção, visto falhando;
- os intervalos: o que acontece se duas coisas acontecem ao mesmo tempo,
  ou uma no meio da outra;
- as bordas: frete com 5 kg e com 5,01; lista vazia; entrega sem cidade;
- o caminho feliz, uma vez, para cada função que importa.

:::pitfall
O teste do intervalo usa tempo de verdade: 50 ms. Com dezenas de testes
assim, a suíte fica lenta, e com o servidor da esteira ocupado, um
`setTimeout` pode atrasar e o teste falhar sem defeito. O `node:test`
tem um relógio falso para isso — `mock.timers` —, que avança o tempo sem
esperar. Para os dois testes do painel, 50 ms reais ainda são o jeito mais
fácil de ler.
:::

## O que o verde não diz

O teste passa, e o painel novo não escreve mais por cima. O **servidor**
recebeu dois pedidos — "a caminho" e "cancelada" — e o que ele guarda
depende da ordem em que os dois chegaram lá. O teste não fala do
servidor, porque o servidor do teste é falso e não guarda nada.

A Bia escreveu isso no ticket, com a frase do teste e a pergunta: o
servidor aplica a mesma regra? O teste do painel não sabe responder.

:::milestone
Fim da Parte 6. A pasta `borba` é um projeto: arquivos com `import` e
`export` numa direção só, um `package.json` com lockfile, o Axios fora do
caminho da busca de canceladas, e `npm test` com o caso do Paulo — que
falhou primeiro e passa agora.
:::

:::summary
- `test(nome, função)` e `assert.equal(atual, esperado)`, do próprio Node.
  `node --test` roda os `.test.js`; `npm test` dá nome ao comando.
- O nome do teste é a afirmação. Verde afirma o nome, e mais nada.
- Receber o servidor como parâmetro deixa o teste controlar o tempo.
- Todo teste novo é visto falhando, pelo motivo certo, antes de passar.
- Teste o intervalo, a borda e o defeito que chegou à Lívia, não só o
  espelho do código.
:::

:::exercise level=1
Escreva dois testes para `calcularFrete`: a borda de 5 kg em Franca — sem
extra — e a de 6 kg — com um quilo de extra.

:::answer
```javascript
test("Franca, 5 kg, sem extra", () => {
  assert.equal(calcularFrete({ cidade: "Franca", pesoKg: 5 }), 1890);
});

test("Franca, 6 kg, um quilo de extra", () => {
  assert.equal(calcularFrete({ cidade: "Franca", pesoKg: 6 }), 1980);
});
```

A regra é "acima de 5". Os dois testes fixam o valor de cada lado do 5.

E eles mostram uma coisa que a leitura não mostrava: trocar `>` por `>=`
não mudaria nenhum dos dois. Com exatamente 5 kg, o extra seria
`(5 - 5) * 90`, zero, dos dois jeitos. Nesta regra, a borda não importa —
e é o teste de borda que responde isso, em vez de uma discussão sobre qual
operador está certo.
:::

:::exercise level=2
Escreva o teste do intervalo ao contrário: a entrega é cancelada, e,
enquanto o cancelamento grava, o motorista inicia a rota. Diga o que a
Lívia espera e se o painel do capítulo passa.

:::answer
```javascript
test("iniciar rota enquanto o cancelamento grava", async () => {
  const painel = criarPainel(servidorLento(50), {
    "E-5701": "separada",
  });

  const cancelando = painel.cancelar("E-5701");
  await painel.iniciarRota("E-5701");
  await cancelando;

  assert.equal(painel.status("E-5701"), "cancelada");
});
```

A Lívia espera `"cancelada"`: a loja cancelou, o motorista não deveria
sair. O painel do capítulo **falha**. `cancelar` muda o status na hora; o
`iniciarRota` guarda `"cancelada"` como o "antes", grava, confere que
ninguém mudou — e escreve `"a caminho"`.

A regra "a mudança mais nova vence" não basta: cancelada precisa vencer
rota, sempre. O conserto é `iniciarRota` recusar entrega cancelada, antes
e depois de gravar. O teste mostrou que a regra escrita era mais estreita
que a da Lívia.
:::

:::exercise level=3
O Marcos pede 80% de cobertura — a fração das linhas do código executadas
pelos testes — antes de 6 de maio. Responda, com o que 80% garante e não
garante no caso do Paulo.

:::answer
O `node --test --experimental-test-coverage` mede isso, e o número é útil
como mapa: mostra o arquivo que nenhum teste toca.

Como meta, 80% não garante o caso do Paulo. O primeiro teste do capítulo,
o do caminho feliz, já executa **todas** as linhas de `iniciarRota` na
versão com defeito: cobertura de 100% na função, com o defeito lá dentro.
O que pegou o defeito não foi executar mais linhas; foi executar as mesmas
linhas numa **ordem** que ninguém tinha imaginado.

A proposta que eu levaria: um teste para cada defeito que chegou à Lívia
desde março, escrito antes da correção. São os que valem R$ 3,50 cada.
A cobertura sobe junto, e sobe onde os defeitos estavam.
:::
