---
title: "Encerramento"
slug: encerramento
matter: back
numbered: false
kicker: "O calendário de farmácia continua na parede da Vertexo, com vinte e cinco sábados riscados e um circulado."
---

:::story O sábado circulado
Em junho, a Vertexo mudou de andar, e alguém precisou decidir o que fazer
com o calendário de farmácia da sala de reunião.

Estava do jeito que o Nonato tinha deixado em outubro: os sábados até 31
de março riscados um a um, com caneta azul. Um deles, de março, estava
circulado de vermelho, com uma anotação na letra da Márcia: *1.412*.

— O fim de semana que dá errado — disse a Tainá.

— Sempre tem esse — disse a Márcia.

O Nonato tirou o calendário da parede, enrolou e pôs embaixo do braço,
junto com o papel dobrado da senha do FTP, que ele tinha pedido para
guardar e ninguém tinha tido coragem de negar.

— Vinte e cinco fins de semana — disse ele. — Eu disse que era um por
item.

— Você disse que eram vinte e seis itens — disse o Dedé.

— E foram. O vigésimo sexto foi o Laravel. — Ele ajeitou o calendário
debaixo do braço. — Levou os outros vinte e cinco.

O Dedé demorou um pouco para entender que aquilo era um elogio.
:::

:::story Cinco estrelas
O aplicativo do Kauã entrou na loja em maio, com o logotipo da Casa
Amarela finalmente na proporção certa. Tinha quarenta e duas avaliações,
média 4,6. A mais curta era da Dona Marlene:

*"Agora o e-mail vem assinado pela biblioteca. Cinco estrelas."*

A mais longa era do Seu Juvenal, e terminava com uma sugestão de
funcionalidade.

Num sábado de junho, a Vera chegou às oito e quarenta, como em todos os
dias dos últimos trinta e um anos. Abriu o painel e conferiu o resumo do
dia: quatro devoluções na caixa, nenhum atrasado novo, duas reservas
esperando, e as trezentas capas que ela fotografou — todas em pé.

A Tainá chegou às nove, com o caderno. Estava na última página.

— Acabou? — perguntou a Vera.

— O caderno? Acabou. Comprei outro.

— E o que tem na última linha?

A Tainá leu:

— "Perguntar para quem faz o trabalho antes de escrever o código."

A Vera pensou um pouco.

— Isso devia estar na primeira.

A porta abriu. O Seu Juvenal entrou com uma sacola de mudas de alface.

— Bom dia, bom dia. Os meninos da horta viram o aplicativo e ficaram
animados. Eles querem uma coisinha. Pra controlar os canteiros, quem
planta o quê, quem rega em que dia. — Pôs a sacola no balcão. — Quanto
tempo leva pra fazer um sisteminha desses?

A Tainá abriu o caderno novo na primeira página.

— Quantos canteiros são?
:::

:::art caption="Todo sistema termina com alguém pedindo uma coisinha."
src="todo-sistema-termina-com-alguem-pedindo-uma-coisinha.png"
Ilustração editorial minimalista em fundo branco, tom leve de despedida:
o balcão de uma pequena biblioteca de bairro numa manhã de sábado. Atrás
dele, uma bibliotecária mais velha, de óculos, confere um monitor onde
aparecem miniaturas de capas de livro, todas em pé. Uma estagiária abre um
caderno novo na primeira página, caneta na mão. Do outro lado, um senhor
de boné acaba de pôr no balcão uma sacola de mudas de alface, com as mãos
abertas no gesto de quem vai pedir "só uma coisinha". Poucos elementos,
humor sutil, estética de revista de tecnologia.
:::

## O caminho dos dois volumes

Dois livros, sessenta capítulos, uma biblioteca de bairro. Olhando
de trás para a frente, cada coisa que o Laravel faz por você tem um lugar
em que você a fez à mão primeiro:

| O problema | À mão, no volume 1 | No framework, neste volume |
|---|---|---|
| guardar dado | SQL, PDO, transação | migrations, Eloquent |
| organizar código | Composer, namespaces | `app/`, autoload, service providers |
| montar objetos | o `Servicos` de closures | o contêiner que lê o construtor |
| configurar | `.env` e `config/` | `.env` e `config/`, com cache |
| dizer que deu errado | exceções de domínio | handler, `422`, `409`, formato único |
| tempo | `Relogio` injetado | `now()` congelado nos testes |
| arquivo grande | gerador, `fgetcsv` | `LazyCollection`, lote na fila |
| arquivo enviado | `rename` no fim | `Storage`, disco privado e público |
| avisar | `Registro` com contexto | `Log`, notificações por canal |
| trabalho demorado | o script da madrugada | filas, workers, lotes, ritmo |

Tabela: A mesma lista, dos dois lados. O framework não trouxe ideias novas
para este projeto; trouxe as mesmas ideias, prontas, testadas por mais gente.

É por isso que o volume 1 existe. Quem só conhece a coluna da direita usa o
Laravel. Quem conhece as duas consegue dizer por que ele faz o que faz — e
o que fazer no dia em que ele não fizer.

## O que este livro não cobre, e onde procurar

Algumas ferramentas ficaram de fora de propósito. Cada uma resolve um
problema real, e nenhuma é necessária para uma API como a da Casa Amarela.

**Livewire** e **Inertia** constroem interfaces interativas sem separar
front-end e back-end; a documentação oficial de cada um é o ponto de
partida.

**Vue** e **React** são o caminho quando o painel da Vera virar uma
aplicação de verdade no navegador; a API deste livro é exatamente o que
eles consomem.

**Octane** mantém a aplicação carregada na memória entre requisições, e
torna o `singleton` do capítulo @cap:service-container — e as variáveis
`static` do capítulo @cap:escopo-e-referencias — ainda mais perigosos; a
documentação do Laravel tem uma seção inteira sobre o que muda.

**Horizon** e **Redis** são o próximo passo da fila do capítulo
@cap:queues-na-pratica, no dia em que a tabela `jobs` deixar de bastar.

**Multitenancy** — várias bibliotecas no mesmo sistema, com dados
separados — é um problema de desenho antes de ser de pacote; comece pelos
artigos sobre banco compartilhado × banco por cliente. A segunda
biblioteca do bairro vizinho vai fazer essa pergunta.

**GraphQL** é uma alternativa ao REST para clientes que precisam montar as
próprias consultas; o pacote Lighthouse é a referência em Laravel.

**Microsserviços** e **Kubernetes** resolvem problemas de organizações com
dezenas de equipes; para uma biblioteca com três conceitos e um
computador, a resposta é a do caderno da Tainá.

## Uma última coisa

O Sistema de 2009 ficou quinze anos no ar sem perder um acervo. Foi escrito
num fim de semana, por alguém de vinte e três anos, com as ferramentas que
havia. O sistema novo vai ficar no ar enquanto alguém souber mexer nele — e
esse alguém, a partir de agora, pode ser você.

Quando chegar o seu Seu Juvenal, com a sacola de mudas e a coisinha que
leva um fim de semana, comece pela pergunta da Tainá. Quantos canteiros
são? Quem rega? O que acontece quando dois meninos regam o mesmo canteiro
no mesmo dia?

O código vem depois. Ele sempre veio.

:::milestone
Fim de PHP One. A Casa Amarela tem uma API em produção, um aplicativo na
loja, capas em pé, e-mails assinados pela biblioteca e uma fila que manda
o aviso das nove às nove. Tem também uma pasta com o Sistema de 2009, em
duas cópias, que ninguém apagou.

E, no balcão, um caderno novo, com uma pergunta na primeira página.
:::
