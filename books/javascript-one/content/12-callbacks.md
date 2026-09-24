---
title: "Callbacks"
number: 12
slug: callbacks
part: p4
kicker: "Gravar o status chama quem notifica, que chama quem atualiza a tela. Quando a notificação falhou, a tela ficou esperando. E ninguém soube."
goal: >-
  Passar uma função para outra, entender que o código que espera não para
  o programa, ler uma cadeia de três continuações na ordem em que elas de
  fato rodam, e não deixar o erro do meio sumir.
---

:::story A tela que esperava
Segunda, 30 de março. O Paulo marcou a E-5230 como entregue no aplicativo
de teste às 10h02. A tela do painel continuou dizendo "a caminho" até o
meio-dia, quando ele recarregou a página.

— Gravou? — perguntou a Bia.

— Gravou às 10h02. Está no servidor. A tela é que não soube.

A Bia abriu o trecho do painel que atualiza o status:

```javascript
gravarStatus(e, function () {
  notificarCliente(e, function () {
    atualizarLinha(e);
  });
});
```

— A tela só atualiza depois que a notificação termina — disse ela.

— E a notificação terminou? — perguntou o Rafael.

A Bia procurou no log do servidor. Às 10h02, uma linha:

```text
WhatsApp API: 503 Service Unavailable
```

— Não.

— Então a tela está esperando até agora.
:::

## Uma função como argumento

O capítulo @cap:arrays-e-objetos passou funções para `map` e `filter`.
Uma função é um valor como outro qualquer: pode ser guardada num nome,
posta num array, e entregue a outra função.

```javascript title="avisar.js" numbered
function processar(codigo, depois) {
  console.log(`processando ${codigo}`);
  depois(codigo);
}

function avisar(codigo) {
  console.log(`aviso: ${codigo} pronta`);
}

processar("E-5230", avisar);
```

```text
$ node avisar.js
processando E-5230
aviso: E-5230 pronta
```

`processar` recebe `avisar` no parâmetro `depois` e a chama quando
termina. Repare: `avisar`, sem parênteses. Com parênteses, `avisar()`
chamaria a função ali, e o que seria entregue é o resultado dela.

:::term Callback
Uma função entregue a outra para ser chamada depois — quando a outra
terminar, ou quando algo acontecer. Quem a recebe decide quando chamar e
com quais argumentos.

"Callback" é o papel da função, não um tipo de função. `avisar` é callback
na linha em que é passada a `processar`.
:::

## O que não espera

Até aqui, tudo rodou em ordem, de cima para baixo. Gravar no servidor não é
assim. O pedido sai, e a resposta volta dezenas ou centenas de
milissegundos depois — e o programa **não para** para esperar.

`setTimeout` simula isso: chama uma função depois de um tempo.

```javascript title="espera.js" numbered
console.log("1. pedindo a gravação");

setTimeout(function () {
  console.log("3. o servidor respondeu");
}, 300);

console.log("2. seguindo com o resto");
```

```text
$ node espera.js
1. pedindo a gravação
2. seguindo com o resto
3. o servidor respondeu
```

A linha 2 do resultado vem de uma linha que está **depois** do
`setTimeout` no código, e roda **antes** do callback dele. O `setTimeout`
agenda a função e devolve na hora. O programa segue. Trezentos
milissegundos depois, a função agendada roda.

É por isso que gravar, notificar e atualizar a tela no painel são escritos
como callbacks: cada um só pode começar quando o anterior respondeu, e
"quando o anterior respondeu" não é a linha seguinte.

:::key
Código que espera uma resposta — de rede, de disco, de um tempo — não
bloqueia o programa. Ele recebe uma função para chamar depois, e o
programa continua. A ordem das linhas no arquivo deixa de ser a ordem em
que as coisas acontecem.
:::

## Três continuações

O trecho do painel, reproduzido na pasta `borba` com tempos simulados:

```javascript title="status.js" numbered
function gravarStatus(e, depois) {
  setTimeout(() => {
    console.log(`gravado: ${e}`);
    depois();
  }, 200);
}

function notificarCliente(e, depois) {
  setTimeout(() => {
    console.log(`notificado: ${e}`);
    depois();
  }, 300);
}

function atualizarLinha(e) {
  console.log(`tela: ${e} entregue`);
}

console.log("início");
gravarStatus("E-5230", () => {
  notificarCliente("E-5230", () => {
    atualizarLinha("E-5230");
  });
});
console.log("fim do arquivo");
```

```text
$ node status.js
início
fim do arquivo
gravado: E-5230
notificado: E-5230
tela: E-5230 entregue
```

"fim do arquivo" sai antes de tudo. Depois de 200 ms, a gravação; depois
de mais 300, a notificação; e só então a tela.

Cada callback está dentro do anterior, e o recuo cresce para a direita a
cada passo. Com três passos, lê-se. O `entrega.js` tem um trecho com seis,
e o nome que se dá a isso em qualquer equipe é o que a forma sugere: a
pirâmide.

## O erro no meio

Agora a notificação falha, como às 10h02:

```javascript title="status.js" numbered
function notificarCliente(e, depois) {
  setTimeout(() => {
    const falhou = true; // como às 10h02
    if (falhou) {
      console.log("WhatsApp: 503");
      return;
    }
    console.log(`notificado: ${e}`);
    depois();
  }, 300);
}
```

```text
$ node status.js
início
fim do arquivo
gravado: E-5230
WhatsApp: 503
```

A tela nunca atualiza. Não há erro, não há exceção: a função da
notificação simplesmente não chamou o `depois`. O programa termina, e a
linha continua "a caminho".

E pôr um `try` em volta não ajuda:

```javascript
try {
  gravarStatus("E-5230", () => { /* ... */ });
} catch (erro) {
  console.log("falhou", erro);
}
```

O `try` só vê o que acontece **durante** a chamada de `gravarStatus`. A
gravação, a notificação e a falha acontecem depois, quando o `try` já
terminou há muito tempo.

## A convenção do erro primeiro

O Node resolveu isso com uma convenção: o callback recebe **o erro como
primeiro argumento**. `null` se deu certo; o erro, se não deu.

```javascript title="status.js" numbered
function notificarCliente(e, depois) {
  setTimeout(() => {
    const falhou = true;
    if (falhou) {
      depois(new Error("WhatsApp: 503"));
      return;
    }
    depois(null);
  }, 300);
}

gravarStatus("E-5230", () => {
  notificarCliente("E-5230", (erro) => {
    if (erro) {
      console.log(`aviso não enviado: ${erro.message}`);
    }
    atualizarLinha("E-5230");
  });
});
```

```text
início
fim do arquivo
gravado: E-5230
aviso não enviado: WhatsApp: 503
tela: E-5230 entregue
```

Agora a falha chega a quem chamou, e ele decide. A decisão da Cláudia,
depois de ouvir a Lívia: a tela atualiza **sempre** que a gravação deu
certo. A notificação ao cliente é importante, e não é o que a Lívia
confere às 5h40. Se ela falhar, a linha ganha um aviso, e a tela segue.

:::pitfall
A convenção só funciona se todo callback da cadeia **olhar** o primeiro
argumento. Um `(erro, resultado) => { usar(resultado); }` que ignora o
`erro` é a falha calada de volta, com um parâmetro a mais. No `entrega.js`
há onze callbacks com `erro` no parâmetro. Quatro o leem.
:::

A ordem dos passos também mudou de sentido. A tela não depende da
notificação; depende da gravação. A cadeia certa é:

```javascript
gravarStatus(e, (erro) => {
  if (erro) {
    marcarFalhaDeGravacao(e, erro);
    return;
  }
  atualizarLinha(e);
  notificarCliente(e, (erroAviso) => {
    if (erroAviso) marcarAvisoPendente(e);
  });
});
```

A tela atualiza assim que a gravação volta. A notificação corre depois, e
a falha dela não segura nada. A E-5230 teria aparecido "entregue" às
10h02, com um ícone de aviso pendente ao lado.

:::summary
- Função é valor: pode ser passada a outra. `avisar`, sem parênteses, é a
  função; `avisar()` é o resultado dela.
- Callback é a função passada para ser chamada depois.
- Código que espera não bloqueia: `setTimeout`, rede e disco agendam o
  callback e o programa segue. A ordem das linhas deixa de ser a ordem dos
  acontecimentos.
- Um callback que não é chamado não dá erro: a cadeia para calada. `try`
  em volta não alcança o que acontece depois.
- Convenção do Node: erro como primeiro argumento. Todo callback da cadeia
  o lê.
:::

:::exercise level=1
Diga a ordem em que as linhas aparecem:

```javascript
console.log("A");
setTimeout(() => console.log("B"), 0);
console.log("C");
```

:::answer
`A`, `C`, `B`.

Mesmo com zero milissegundos, o `setTimeout` agenda a função para depois
que o código que está rodando agora terminar. O `C` está no código que
está rodando.
:::

:::exercise level=2
Escreva `gravarStatus(e, depois)` com a convenção do erro primeiro: se o
código da entrega não começar com `"E-"`, chama `depois` com um erro; senão,
com `null`. Chame duas vezes, uma com cada caso.

:::answer
```javascript
function gravarStatus(e, depois) {
  setTimeout(() => {
    if (!e.startsWith("E-")) {
      depois(new Error(`código inválido: ${e}`));
      return;
    }
    depois(null);
  }, 100);
}

gravarStatus("E-5230", (erro) => {
  console.log(erro ? erro.message : "gravado E-5230");
});
gravarStatus("5230", (erro) => {
  console.log(erro ? erro.message : "gravado 5230");
});
```

```text
gravado E-5230
código inválido: 5230
```

O `return` depois de chamar com erro é o que impede de chamar `depois` duas
vezes — uma com o erro e outra com `null`. Callback chamado duas vezes é
tela atualizada duas vezes, ou notificação em dobro.
:::

:::exercise level=3
Um trecho de `entrega.js`:

```javascript
function marcar(e, depois) {
  gravarStatus(e, (erro) => {
    if (erro) depois(erro);
    depois(null);
  });
}
```

O Paulo diz que, quando a gravação falha, a tela mostra o erro e, logo
depois, a entrega como gravada. Explique e corrija.

:::answer
Quando há erro, o `if` chama `depois(erro)` e **não sai**. A linha
seguinte roda também, e chama `depois(null)`. Quem chamou `marcar` recebe
as duas respostas: primeiro a falha, depois o sucesso. A tela mostra as
duas, na ordem.

```javascript
function marcar(e, depois) {
  gravarStatus(e, (erro) => {
    if (erro) {
      depois(erro);
      return;
    }
    depois(null);
  });
}
```

Com o `return`, cada caminho chama `depois` exatamente uma vez. É o defeito
mais comum da convenção do erro primeiro, e é uma das razões de o capítulo
seguinte existir.
:::
