---
title: "O que é o Laravel"
number: 27
slug: o-que-e-o-laravel
part: p5
kicker: "A resposta para a pergunta da estagiária tem duas partes: o que o framework faz por você, e o que ele decide sem perguntar."
goal: >-
  Descrever o ciclo de uma requisição Laravel apontando, em cada etapa, o
  equivalente no micro-framework do capítulo anterior — e saber nomear o
  que a convenção cobra em troca do que entrega.
---

*"Por que a gente não usa esse e pronto?"*

Porque o arquivo de cem linhas atende três rotas e não valida entrada, não
trata erro, não fala com banco, não autentica ninguém, não padroniza
resposta, não tem teste e não tem documentação. Completar essa lista é o
trabalho de um ano, e o resultado seria um framework com um mantenedor só.

A resposta longa é este capítulo — e ela não começa em "o Laravel é ótimo".
Começa em o que, exatamente, um framework é.

## Framework é código que chama o seu

Uma **biblioteca** é código que você chama. Você decide quando, passa os
argumentos e recebe o resultado. O `symfony/var-dumper` é biblioteca: você
escreve `dump()` onde quiser.

Um **framework** é o contrário: ele é o programa, e o seu código são os
pedaços que ele chama. Você não escreve o laço principal, não trata a
requisição, não decide a ordem das etapas. Você preenche lacunas que alguém
já numerou.

:::term Inversão de controle
O nome disso. Com biblioteca, o controle é seu e você pede ajuda; com
framework, o controle é dele e ele pede o seu código.

Não é uma questão de tamanho. Existem frameworks pequenos e bibliotecas
enormes. A diferença é quem chama quem.
:::

Isso tem uma consequência prática que aparece no primeiro dia: **você não
escolhe a estrutura de pastas, o nome dos arquivos nem o formato das
classes.** O framework escolheu, e o preço de discordar é maior que o de
aceitar.

## As peças

O Laravel não foi escrito do zero em 2011. Ele é uma montagem, e boa parte
das peças de baixo vem do Symfony:

| Peça | Origem | Trabalho |
|---|---|---|
| `Illuminate\Http\Request` | estende a do Symfony | a requisição como objeto |
| `Illuminate\Http\Response` | estende a do Symfony | a resposta como objeto |
| `Illuminate\Console\Command` | estende a do Symfony | os comandos de terminal |
| `Illuminate\Container` | próprio | resolve dependências |
| `Illuminate\Routing` | próprio | a tabela de rotas |
| Eloquent | próprio | objetos que falam com o banco |
| Blade | próprio | gerar HTML |

Tabela: `Illuminate` é o nome do conjunto de componentes do Laravel. Cada um
deles é instalável sozinho, fora do framework.

Isso é uma informação útil e raramente dita: quando você lê `Request` no
código de um projeto Laravel, está olhando para uma classe que herda de uma
peça do Symfony com mais de quinze anos de uso. A parte "mágica" do
framework é mais fina do que parece — e a parte testada, mais grossa.

## O ciclo de uma requisição

Aqui está o capítulo inteiro em uma tabela. À esquerda, o que você escreveu
à mão; à direita, quem faz o mesmo trabalho no Laravel.

| No seu `mini.php` | No Laravel |
|---|---|
| o arquivo inteiro | `public/index.php` |
| — | `bootstrap/app.php` monta a aplicação |
| — | *service providers* registram e iniciam |
| `Container::obter` | `Illuminate\Container\Container` |
| o `array_reduce` das camadas | `Illuminate\Pipeline\Pipeline` |
| `$rotas`, o array | `routes/api.php` e `routes/web.php` |
| `Roteador::despachar` | `Illuminate\Routing\Router` |
| a função da rota | o seu controller |
| `Resposta` | `Illuminate\Http\Response` |
| `enviar()` | `$response->send()` |

Tabela: Duas linhas não têm equivalente no seu arquivo, e são exatamente as
duas que fazem um framework crescer sem virar bagunça.

**`bootstrap/app.php`** é o lugar onde a aplicação é montada antes de
qualquer requisição chegar: quais arquivos de rota existem, quais camadas
rodam em cada grupo, o que fazer com exceção não tratada. No seu arquivo,
isso estava misturado com as rotas porque eram três.

**Service provider** é a peça que você ainda não tem e vai querer. Cada
pedaço do framework — banco, fila, cache, sessão — tem um arquivo que diz ao
contêiner como construí-lo. Eles rodam em duas fases: primeiro todos
*registram* o que sabem fazer, depois todos *iniciam*.

:::key
A separação em duas fases existe por um motivo que você reconhece do
contêiner do capítulo anterior: na hora de iniciar, um provedor pode precisar
de algo que outro registrou.

Registrar é barato e não depende de ninguém. Iniciar pode depender de todo
mundo. Fazer as duas coisas numa passagem só criaria uma ordem de
carregamento — e ordem de carregamento é o problema do
`funcoes2_NOVO_final.php`, num prédio maior.
:::

E as **facades**, em uma frase, porque elas confundem quem chega: `Cache::get()`
não é um método estático de verdade — é um atalho que pergunta ao contêiner
qual objeto responde por "cache" e chama o método nele. Conveniência de
escrita, com o objeto real embaixo.

## Convenção sobre configuração, e o que ela custa

O Laravel decide muita coisa por você. Onde os controllers moram, como as
classes se chamam, qual tabela um model usa, em que ordem as camadas rodam,
como um erro vira resposta.

Cada decisão dessas é tempo que você não gasta — e uma liberdade que você
não tem.

| O que a convenção entrega | O que ela cobra |
|---|---|
| nenhuma decisão de estrutura no dia 1 | a estrutura não é discutível no dia 300 |
| qualquer pessoa da comunidade lê o projeto | o projeto se parece com todos os outros |
| atualização de versão com caminho pronto | sair do caminho encarece a atualização |
| resposta pronta para problema comum | problema incomum luta contra o padrão |

Tabela: A troca é boa na maioria dos projetos, e é uma troca. Quem chama
isso de "só vantagem" ainda não teve um requisito que briga com o padrão.

:::pitfall
O erro que custa caro não é escolher a convenção. É **recusá-la pela
metade**: manter o framework e reescrever a parte dele que você não gostou.

O resultado é um projeto que nem segue o manual nem tem um manual próprio —
e em que cada pessoa nova precisa aprender duas vezes: como o Laravel faz e
como aqui a gente faz.

Se a convenção não serve, o caminho honesto é discutir isso antes de
escolher o framework, e não seis meses depois com o prazo em cima.
:::

## O que ele decide por você, e como discordar

Nem tudo é imposto. Vale saber onde há espaço:

**Não dá para trocar sem dor:** a estrutura de pastas de topo, o ciclo de
requisição, o contêiner e o formato do arquivo de rotas.

**Dá para trocar, e é comum:** a camada de banco — dá para usar o Eloquent,
uma consulta escrita à mão ou os dois; a camada de resposta; a organização
interna de `app/`, que o framework não fiscaliza.

**É só padrão, e ninguém se importa:** nomes de pasta dentro de `app/`,
formato de controller, quantos arquivos de rota existem.

A régua: **quanto mais perto do ciclo da requisição, menos negociável.**
Quanto mais perto da sua regra de negócio, mais.

## Laravel, Symfony ou nenhum dos dois

Os três são respostas legítimas.

**Laravel** entrega mais coisa pronta e decide mais por você. Fila, e-mail,
autenticação, agendamento e upload vêm configurados, e o caminho de cada um
está documentado no mesmo lugar. O custo é que sair do trilho dá trabalho.

**Symfony** entrega peças mais soltas e configuração mais explícita. Ele
pede mais decisões no começo e cobra menos por decisões estranhas depois. É
a escolha frequente de empresa grande com equipe de plataforma.

**Nenhum dos dois** é resposta certa em duas situações reais: um serviço com
uma rota só, em que o framework seria mais código que o serviço; e um
projeto cujo problema é tão específico que nenhuma convenção ajuda — o que
é raro, e quase sempre alegado antes de ser verdade.

Para a Casa Amarela, a decisão cabe numa linha: um CRUD com regras de
negócio, autenticação simples, relatório, fila de lembretes e uma tela
administrativa é exatamente o formato para o qual o Laravel foi desenhado.

:::note Na sua carreira
"Qual framework é melhor?" é a pergunta de quem ainda não escolheu nenhum. A
pergunta de quem já entregou é outra: **qual atrito eu vou ter, e ele é o
atrito que eu sei pagar?**

Toda escolha de tecnologia tem um lugar onde ela dói. Saber nomear o lugar
antes de começar é a diferença entre uma decisão e uma torcida — e é a
resposta que impressiona numa entrevista técnica, porque mostra que você
levou um projeto até o ponto em que a dor apareceu.

Quando alguém defender uma escolha e não conseguir dizer o que ela custa,
ainda não é uma defesa. É entusiasmo, e entusiasmo tem prazo de validade
curto.
:::

:::milestone
Fim da Parte 5. Você leu uma requisição no fio, desenhou os endereços da API
antes da primeira rota, escreveu as quatro peças que todo framework PHP tem
e viu onde cada uma delas mora num framework de verdade. A partir daqui, o
Laravel entra — e nenhuma parte dele deveria parecer mágica.
:::

:::summary
- Biblioteca é código que você chama; framework é código que chama o seu.
- `Illuminate` é o conjunto de componentes do Laravel, e as peças de HTTP e
  console herdam do Symfony.
- O ciclo é o mesmo do micro-framework, com duas peças a mais:
  `bootstrap/app.php` e os service providers.
- Providers registram numa fase e iniciam noutra, para não depender de ordem
  de carregamento.
- Facade é atalho para um objeto que mora no contêiner, não método estático
  de verdade.
- Convenção entrega velocidade no dia 1 e cobra liberdade no dia 300.
- Recusar a convenção pela metade é pior que aceitá-la ou que não usar o
  framework.
- Quanto mais perto do ciclo da requisição, menos negociável; quanto mais
  perto da regra de negócio, mais.
:::

:::checkpoint
Você descreve o ciclo de uma requisição Laravel do `index.php` à resposta,
aponta o equivalente de cada etapa no arquivo que escreveu à mão, explica o
que é uma facade sem usar a palavra mágica, e consegue dizer o que a
convenção do framework custa.
:::

:::exercise level=1
Para cada item, diga se ele é biblioteca ou framework, e por quê:

1. `symfony/var-dumper`
2. Laravel
3. PHPStan
4. Eloquent, usado sozinho, fora do Laravel

:::answer
1. **Biblioteca.** Você chama `dump()` onde quiser; ela não chama nada seu.
2. **Framework.** Ele roda o ciclo e chama o seu controller.
3. **Ferramenta**, e vale separar a categoria: o PHPStan não é chamado pelo
   seu programa nem chama o seu programa — ele **lê** o seu programa, e roda
   fora da execução. Analisador, formatador e teste são dessa família.
4. **Biblioteca.** Fora do framework, o Eloquent é um pacote que você
   instala, configura e chama. Ele vira parte de um framework quando o
   framework é quem decide quando chamá-lo.

O caso 4 é o interessante: a mesma classe é biblioteca ou parte de framework
dependendo de quem está no comando. A distinção não está no código — está na
direção da chamada.
:::

:::exercise level=2
Pegue o `mini.php` do capítulo anterior e escreva, para cada peça dele, uma
frase dizendo o que o Laravel faz **a mais** no mesmo ponto.

Cubra: front controller, roteador, contêiner e middleware.

:::answer
**Front controller.** O seu `mini.php` lê o verbo e o caminho e despacha. O
`public/index.php` do Laravel primeiro monta a aplicação, roda os service
providers, resolve o ambiente e a configuração, e só então entrega a
requisição — e no fim trata a exceção que ninguém pegou, transformando-a
numa resposta com o formato certo.

**Roteador.** O seu casa uma expressão regular por rota, em ordem. O do
Laravel compila as rotas, agrupa por método, aplica restrições declaradas,
resolve nome de rota para URL, e ainda busca o registro no banco quando o
parâmetro é um model.

**Contêiner.** O seu resolve parâmetros que são classes e guarda o que
construiu. O do Laravel faz isso e mais: aceita instruções explícitas para o
que não dá para adivinhar, sabe amarrar uma interface a uma implementação,
distingue o que é único do que é novo a cada resolução, e consegue construir
o mesmo objeto de formas diferentes conforme o contexto.

**Middleware.** O seu é uma cadeia. O do Laravel é uma cadeia por grupo de
rotas, com parâmetros por rota, ordem declarada e a possibilidade de rodar
trabalho **depois** de a resposta já ter sido enviada.

O padrão das quatro respostas é o mesmo, e é o ponto do capítulo: nenhuma
delas é uma ideia nova. Todas são a mesma ideia com os casos difíceis
tratados.
:::

:::exercise level=3
Uma empresa vai começar um sistema novo e a equipe está dividida entre
Laravel e "sem framework, só as bibliotecas que a gente precisar".

Escreva os três argumentos mais fortes de cada lado — os de verdade, não os
de internet — e diga que informação sobre o projeto decidiria a questão.

:::answer
**A favor do Laravel.**

O primeiro é o custo do que não é o seu problema: autenticação, fila,
e-mail, agendamento e upload já existem, testados por muita gente, e nenhum
deles diferencia o seu produto.

O segundo é contratação e continuidade: existe gente que já conhece a
estrutura, e quem entrar no projeto em dois anos vai reconhecer o desenho
sem um mês de leitura.

O terceiro é a manutenção de segurança. Quando aparece uma falha numa peça
comum, ela é corrigida por quem mantém o framework, e você atualiza uma
dependência. Sem framework, cada peça é sua.

**A favor de não usar.**

O primeiro é o tamanho do que você carrega: um serviço com duas rotas roda
mais rápido, sobe mais rápido e tem menos superfície de ataque sem cinquenta
pacotes que ele não usa.

O segundo é a liberdade de desenho. Se o projeto tem uma restrição
incomum — latência muito baixa, formato de mensagem próprio, um modelo de
concorrência diferente —, a convenção vira briga diária.

O terceiro é a clareza: sem framework, o que acontece está escrito no seu
repositório, e o caminho da requisição cabe na cabeça de uma pessoa.

**A informação que decide.** Quantas dessas coisas o sistema vai precisar
nos próximos dois anos: usuário com sessão, permissão por perfil, envio de
e-mail, trabalho em segundo plano, tela administrativa, relatório, upload.

Se a resposta for "quase todas", o framework já ganhou — porque a
alternativa não é "sem framework", é "com um framework pior, escrito aqui
dentro, sem documentação". Se a resposta for "nenhuma delas, é um serviço
que recebe JSON e devolve JSON", a equipe que quer ficar sem tem razão.
:::
