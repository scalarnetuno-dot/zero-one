---
title: "Antes de começar"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Quatrocentas e doze linhas, sete chamadas HTTP e um comentário na primeira linha pedindo para ninguém mexer."
---

Este é o método que fecha as vendas de uma fábrica de geleias:

```php title="app/Http/Controllers/CheckoutController.php"
// NAO MEXER - BLACK FRIDAY 2023 - MARCELO

public function finalizarPedido(Request $request)
{
    $pedido = Pedido::create($request->validated());

    $cobranca = $this->gateway->cobrar($pedido);          // 1
    $this->erp->baixarEstoque($pedido);                   // 2
    $nota = $this->sefaz->emitirNfe($pedido);             // 3
    $etiqueta = $this->transportadora->etiqueta($pedido); // 4
    Mail::to($pedido->cliente)->send(new Confirmacao($pedido));   // 5
    $this->whatsapp->avisarExpedicao($pedido, $etiqueta); // 6
    $this->fidelidade->somarPontos($pedido);              // 7

    return redirect()->route('obrigado', $pedido);
}
```

O original tem 412 linhas, porque cada um desses passos está cercado de
`try/catch`, três deles vazios. Mas o esqueleto é esse: o cliente clica em
"Finalizar pedido" e o servidor faz sete coisas, uma depois da outra, antes
de mostrar a página de obrigado.

E funciona.

Cinco anos no ar, R$ 11 milhões vendidos, geleia de ameixa entregue em todos
os estados do país. Numa terça-feira qualquer, as sete chamadas somam quatro
segundos e ninguém reclama.

Na Black Friday de 2025, a terceira chamada da lista — a nota fiscal — ficou
quarenta minutos sem resposta. Como a terceira não voltava, a quarta não
começava, a página de obrigado não aparecia, e o cliente, que já tinha sido
cobrado no passo 1, apertava o botão de novo.

Você vai desmontar esse método. Não porque ele é ruim — porque ele obriga
sete sistemas de sete empresas diferentes a estarem de pé no mesmo segundo,
e em um dia por ano isso não acontece.

## A fábrica, a data e o dinheiro

A **Doce Mirabel** faz doces e geleias em Serra Clara, no sul de Minas,
desde 1979. Começou na cozinha da Dona Cida, com uma panela de cobre e uma
receita de geleia de ameixa mirabel que ela se recusa a escrever. Hoje tem
trinta e oito funcionários, uma linha de envase e uma loja on-line que
responde por dois terços do faturamento.

A loja foi feita em 2021 por uma agência. O desenvolvedor que a escreveu
saiu da agência, virou consultor e cobra R$ 380 a hora para explicar o que
fez. A empresa contratou, em agosto, uma pessoa de tecnologia. Quem vai
fazer o trabalho é você.

E existe uma data que ninguém pode empurrar: **sexta-feira, 27 de novembro
de 2026**. Black Friday. O livro começa na segunda, 7 de setembro. São onze
semanas e meia.

Na última Black Friday, o checkout ficou quatro horas fora do ar. O contador
da empresa estimou as vendas perdidas em R$ 212 mil — sem contar os 311
estornos de clientes cobrados que não receberam nada. Neste ano a fábrica
tomou um empréstimo para a linha nova, e a parcela foi calculada em cima da
Black Friday.

Nada disso é cenário. Um prazo que não se move, um dia de carga que não se
ensaia em produção e um sistema que precisa continuar vendendo enquanto é
trocado: é isso que transforma "vamos usar uma fila" de frase de palestra em
decisão com custo.

## Quem aparece

Entre uma explicação e outra, você vai encontrar cenas da fábrica. Elas não
são enfeite: um conceito de mensageria gruda muito melhor quando vem colado
a uma impressora de etiquetas que não acompanha o ritmo.

:::story Os que você vai encontrar
**Júlia Tanaka** entrou em agosto como "a pessoa de tecnologia" da Doce
Mirabel. Veio de uma fintech com uma equipe inteira cuidando de
infraestrutura; aqui, a equipe é ela. Oito anos de carreira, desconfiança
saudável de moda e nenhuma paciência para reunião sem pauta.

**Kaique** tem dezenove anos, é estagiário de TI e responde o WhatsApp do
SAC à tarde. É ele quem atende o cliente cobrado duas vezes. Anota tudo no
verso de etiquetas de envio que sobram da expedição.

**Rafa** é o neto da fundadora e o "CEO do digital". Levou a loja de zero a
R$ 4 milhões por ano com Instagram e parcerias, e é muito bom nisso. Lê o
LinkedIn às seis da manhã e chega às oito e meia com a solução da semana.

**Dona Cida** fundou a empresa. Anotou pedido em papel por trinta anos e
nunca perdeu um. Fala pouco e sabe exatamente o que acontece quando um
pedido chega e o vidro acabou.

**Denise** chefia a expedição há vinte e dois anos e opera a Zebrinha, a
impressora de etiquetas. A Zebrinha imprime uma etiqueta a cada 1,8
segundo. Nem um décimo mais rápido.

**Seu Norberto** é o contador. Não entende de sistema e não precisa:
entende de nota fiscal, e nota fiscal não sai duas vezes.

**Marcelão** escreveu o checkout. Hoje cobra por hora para lembrar como.
:::

## Como este livro funciona

O caminho tem duas metades, e a ordem é de propósito.

Na primeira, você escreve mensageria **à mão**, com `php-amqplib`, a
biblioteca de baixo nível que fala o protocolo do RabbitMQ. Conexão, canal,
exchange, fila, confirmação de recebimento — cada peça aparece no momento
em que um defeito a exige, e você vê o defeito antes de ver a peça.

Na segunda, você troca o código repetitivo pela **Mirabel RabbitMQ**, uma
biblioteca pequena de código aberto que transforma um produtor em uma
classe de três linhas e um consumidor em uma classe com um método. Ela
chega depois de propósito: quando você a instalar, vai saber exatamente o
que ela está fazendo por você, e o que ela não pode fazer.

Cada capítulo termina com o estado do projeto:

:::milestone
Você tem: um checkout síncrono de sete passos, uma data e nenhuma fila. É
exatamente de onde quase todo sistema que hoje usa mensageria começou.
:::

## O que você precisa

**PHP 8.2 ou mais novo**, com as extensões `sockets` e `mbstring`, que o
protocolo do RabbitMQ exige. **Composer**, para instalar as bibliotecas.
**Docker**, para subir o RabbitMQ sem instalar nada na sua máquina. E um
terminal.

```bash title="Confirme que está tudo no lugar"
php -v
php -m
composer --version
docker --version
```

O `php -m` lista as extensões carregadas; procure `sockets` e `mbstring` na
lista. Se as quatro respostas vierem com número de versão e as duas
extensões aparecerem, você está pronto.

:::pitfall
No Windows, a extensão `sockets` costuma vir desligada. Abra o `php.ini`
que o comando `php --ini` indicar, procure a linha `;extension=sockets` e
tire o ponto e vírgula do começo. Sem ela, o primeiro `new
AMQPStreamConnection(...)` do livro falha com uma mensagem sobre uma função
de socket que não existe — e nada no texto do erro diz "instale a extensão".
:::

Não é preciso saber Laravel para as Partes 1 e 2: elas são PHP puro. O
Laravel entra na Parte 3, no tamanho em que o checkout precisa dele, e o
PHP One cobre o framework inteiro para quem quiser a volta completa.

:::summary
- O checkout da Doce Mirabel faz sete chamadas em sequência dentro de uma
	requisição; em dia normal isso custa quatro segundos, na Black Friday custou
	quatro horas.
- O projeto tem data (27 de novembro de 2026), dinheiro (R$ 212 mil perdidos
	no ano anterior) e algo em produção (a loja, vendendo agora).
- O livro escreve o protocolo à mão com `php-amqplib` antes de usar a
	Mirabel RabbitMQ, para que a biblioteca nunca pareça mágica.
- Você precisa de PHP 8.2+ com `sockets` e `mbstring`, Composer e Docker.
:::
