---
title: "Antes de começar"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Vinte e cinco fins de semana até 31 de março. O Nonato contou no calendário da parede, e a conta não fechou por um."
---

O volume 1 terminou numa sexta-feira, com a pasta arrumada e uma pergunta
no caderno da Tainá. Este começa na segunda.

## Segunda-feira, nove e dez

A primeira tarefa da semana não teve nada de web. O Dedé trocou a senha do
banco — a que tinha passado por onze arquivos e pelo histórico do Git — e
colou a nova no `.env`, que não vai para lugar nenhum.

— Qual era a antiga? — perguntou a Tainá.

— `senha`.

— E a nova?

— Não é `senha`.

O Nonato, da mesa ao lado, levantou a mão sem tirar os olhos da tela.

— Protesto. Em 2009 a senha era `casaamarela2009`. Alguém trocou para
`senha` depois de mim.

Às nove e quarenta, o Seu Juvenal entrou na sala de reunião da Vertexo com
um pacote de pão de queijo e um anúncio.

— O meu neto, o Kauã, fez um aplicativo. Num fim de semana. Para a
biblioteca. — Ele virou o celular para a mesa: uma tela azul, o logotipo
da Casa Amarela esticado na horizontal e um botão *Renovar*. — Só falta
ligar no sistema.

— Ligar como? — perguntou a Márcia.

— Isso eu deixo com vocês. Ele disse que é só uma API.

A Tainá abriu o caderno na última página escrita. Embaixo de *o que chega
do navegador até o PHP?* apareceu uma segunda linha: *e do aplicativo do
Kauã?*

## O fim de semana do Nonato

A discussão começou do jeito que discussão técnica começa na Vertexo: com
alguém dizendo que não precisava discutir.

— A gente faz em PHP puro — disse o Nonato. — Vocês acabaram de passar um
livro inteiro aprendendo PHP. Eu fiz o Sistema num fim de semana, e ele
está no ar há quinze anos.

— Com `mysql_query` e senha em MD5 — disse o Dedé.

— Com `mysql_query` e senha em MD5, e nenhum acervo perdido.

O Dedé foi até o quadro branco.

— Tudo bem. O que o aplicativo do Kauã precisa fazer?

— Ver os livros. Emprestar. Renovar. Devolver.

O Dedé escreveu quatro palavras — **livros, exemplares, leitores,
empréstimos** — e, ao lado de cada uma, as mesmas quatro letras.

— CRUD — disse a Tainá. — *Create, read, update, delete.*

— Quatro tabelas, quatro operações. Dezesseis endpoints. É a parte fácil.
— Ele fez um traço embaixo. — Agora o resto.

E escreveu, uma por linha: *rotas. ler JSON. responder JSON. validar cada
campo. senha do leitor. token do aplicativo. quem pode o quê. erro num
formato só. paginação. busca. e-mail de aviso. fila, para o e-mail não
travar a tela. cache. log. migração de banco. testes. documentação para o
Kauã. deploy.*

— Cada uma dessas — disse o Nonato — é um fim de semana.

— Então conta.

O Nonato contou as linhas em voz alta, contando junto as que o Dedé ia
lembrando no caminho. Deram vinte e seis. Depois ele se levantou, foi até
o calendário da parede — um calendário de farmácia, com os meses em
fileira — e contou os sábados até 31 de março, com o dedo.

— Vinte e cinco.

— Faltou um — disse a Tainá.

— Faltou o fim de semana em que dá errado — disse a Márcia. — Sempre tem
esse.

O Nonato sentou de novo, devagar.

— Em 2009 não tinha aplicativo.

## O meio-termo que ninguém pediu

— Laravel — disse o Dedé. — Tudo o que está no quadro vem pronto, e
testado por mais gente do que a gente vai conhecer na vida.

— E aí ninguém aqui sabe o que roda por baixo — respondeu o Nonato. —
Vira mágica. E mágica quebra na sexta à noite.

Foi a Tainá quem desempatou, sem perceber que estava desempatando.

— E se a gente fizer à mão primeiro? Pequeno. Só para ver o que ele faz.
Depois usa o de verdade.

O Dedé olhou para o quadro. O Nonato olhou para o calendário.

— Quanto é pequeno? — perguntou o Nonato.

— Quarenta linhas.

— Quarenta linhas eu leio.

A Vera, que tinha vindo só entregar a lista das onze regras e ficado pelo
pão de queijo, pegou a bolsa.

— Façam como quiserem. Na segunda às nove eu abro. Com ou sem aplicativo.

O plano ficou no quadro até o fim do projeto, na letra do Dedé, com uma
seta da Tainá do lado:

```text
1. entender o que o navegador (e o Kauã) manda  -> HTTP
2. desenhar a conversa antes do código          -> REST
3. escrever um framework pequeno, à mão         -> 40 linhas
4. usar o de verdade, sabendo o que ele faz     -> Laravel
```

É a ordem deste volume.

## O que você traz do volume 1

Tudo o que o Laravel vai supor que você sabe: tipos, arrays, funções,
closures, SQL escrito à mão, PDO, Composer, classes, interfaces, exceções,
tipagem estrita, enums, datas com fuso e erros que avisam. E um projeto
organizado do jeito que o framework vai organizar:

:::tree title="O que o volume 1 deixou pronto"
acervo/
  bin/                 importar-doacoes.php, atrasados.php
  config/app.php       fuso, prazo, banco — lidos do .env
  public/              vazia: é a porta da web, e a web começa aqui
  src/
    Acervo/            Livro, Exemplar, StatusExemplar
    Emprestimos/       Dinheiro, PrazoDeEmprestimo, StatusEmprestimo
    Circulacao/        exceções de domínio, CalendarioDaBiblioteca
    Importacao/        Csv, Importador
    Tempo/             Relogio, RelogioDoSistema, RelogioParado
    Registro.php       log com contexto
    Servicos.php       contêiner de fábricas, escrito à mão
  var/log/
  bootstrap.php        config, erros viram exceção, serviços
  .env, .env.example
  composer.json        psr-4 CasaAmarela\, phpstan nível 5
:::

E o banco `casa_amarela`, com `livros`, `exemplares`, `leitores` e
`emprestimos`, escrito em SQL puro. Cada peça do Laravel vai ser comparada
com uma coisa desta árvore — e, em algumas comparações, a árvore ganha.

Se você chegou direto a este volume: a **Biblioteca Comunitária Casa
Amarela** tem quatro mil títulos e um sistema em PHP de 2009, o
**Sistema**, que atende o balcão enquanto a **Vertexo Sistemas** constrói o
substituto. A verba vem de um edital cultural, com prestação de contas em
**31 de março**: se atrasar, a verba volta. **Dedé** explica, **Tainá**
pergunta e anota, **Vera** sabe as regras, **Márcia** guarda o prazo,
**Nonato** escreveu o Sistema, **Cléber** responde "ele processa" e **Seu
Juvenal** traz o próximo pedido.

## Como este volume é organizado

Os capítulos têm numeração própria, a partir do 1. Quando o texto citar um
capítulo do primeiro livro, a citação diz isso: "o capítulo 21 do volume
1". Sem a indicação, o capítulo é deste volume.

| Parte | Capítulos | O que acontece |
|---|---|---|
| 1 · A web por baixo do framework | 1–4 | HTTP, REST, quarenta linhas e a escolha do framework |
| 2 · Dentro do Laravel | 5–9 | projeto, configuração, rotas, requests, Blade |
| 3 · Eloquent sobre o SQL | 10–12 | migrations, Eloquent, relacionamentos |
| 4 · A API de verdade | 13–17 | CRUD, validação, resources, paginação, erros |
| 5 · Arquitetura e segurança | 18–22 | contêiner, services, middleware, Sanctum, Policies |
| 6 · Depois da resposta | 23–24 | filas, cache, logs e medição |
| 7 · Provar e publicar | 25–28 | testes, documentação, Git, CI e deploy |
| 8 · O sistema no ar | 29–31 | upload, e-mail e notificações, filas em produção |

Tabela: Oito partes, na ordem em que o problema aparece. O framework só
entra no capítulo 4, depois de você ter escrito à mão o que ele faz; a
última parte começa no dia seguinte ao deploy.

:::practice
Tenha o PHP 8.3 e o Composer instalados, conferidos com `php -v` e
`composer -V`. Se você chegou aqui pelo volume 1, já tem os dois. Se não,
os capítulos 2 e 16 do volume 1 fazem essa instalação passo a passo.
:::

Faltam vinte e cinco fins de semana. Na segunda às nove, a Vera abre.
