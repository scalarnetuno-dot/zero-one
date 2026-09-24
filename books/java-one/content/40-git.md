---
title: "Git"
number: 40
part: p9
kicker: "O código diz o que o sistema faz. O histórico diz por quê — e é a única parte que você não consegue reconstruir."
goal: >-
  Versionar o projeto com commits que explicam a intenção, trabalhar com
  ramos e *pull request*, e resolver um conflito sem pânico.
---

Este é o capítulo que deveria ter sido o primeiro e é o penúltimo, de
propósito: Git só faz sentido quando existe algo com história para contar.
O projeto da Aurora tem quarenta capítulos de decisões.

## Os quatro comandos do dia

```bash title="O ciclo inteiro" numbered
git status                      # o que mudou
git add src/main/java/...       # escolher o que vai
git commit -m "mensagem"        # registrar
git push                        # publicar
```

```bash title="Começando o projeto"
git init
echo "target/" > .gitignore
git add .
git commit -m "primeiro commit: esqueleto do catálogo"
git remote add origin git@github.com:aurora/catalog.git
git push -u origin main
```

:::pitfall
`target/`, `.idea/`, `*.class` e qualquer arquivo com senha **nunca** entram
no repositório. Um `.gitignore` esquecido no primeiro dia significa, seis
meses depois, um repositório de 400 MB com binários compilados. E um
`application.properties` com a senha do banco versionado significa que a
senha vazou — mesmo que você apague depois, ela continua no histórico para
sempre.
:::

## O commit é uma mensagem para o futuro

:::compare left="O que não ajuda" right="O que explica"
ajustes

correções

fix

wip

update final
---
corrige N+1 na
listagem de produtos

usa @EntityGraph para
carregar a categoria
junto: 4.032 consultas
viraram 1
:::

O primeiro grupo aparece em todo repositório do mundo e é inútil no dia em
que alguém precisa entender por que uma linha existe. O segundo responde à
única pergunta que o código não responde sozinho: **por quê**.

```text title="O formato que a maioria dos times adota"
tipo: resumo no imperativo, até 50 caracteres

Corpo opcional, explicando o motivo e o contexto — não o que
o diff já mostra. Quebre em 72 colunas.

Closes #42
```

| Tipo | Quando |
|---|---|
| `feat` | funcionalidade nova |
| `fix` | correção de defeito |
| `refactor` | muda a forma, não o comportamento |
| `test` | acrescenta ou corrige teste |
| `docs` | documentação |
| `chore` | build, dependência, configuração |

Tabela: A convenção *Conventional Commits*. Ela permite gerar o
*changelog* automaticamente — e, mais importante, obriga quem escreve a
classificar a própria mudança.

:::key
Um bom commit é **pequeno e coerente**: uma mudança, um motivo. Se a
mensagem precisa da palavra "e" duas vezes, são dois commits. O custo de
separar é de trinta segundos; o benefício é poder reverter um sem desfazer o
outro.
:::

## Ramos

```bash title="O fluxo de uma funcionalidade" numbered
git switch -c feat/busca-por-nome     # cria e entra no ramo

# ... trabalha, commita ...

git push -u origin feat/busca-por-nome
# abre o pull request na interface do GitHub

git switch main
git pull
git branch -d feat/busca-por-nome     # apaga o ramo local
```

:::diagram type="flowchart" caption="Um ramo por funcionalidade, revisão antes de entrar."
nodes:
  - { id: m,  type: start,   text: "main" }
  - { id: b,  type: process, text: "feat/busca-por-nome" }
  - { id: c,  type: process, text: "commits" }
  - { id: pr, type: decision,text: "revisão aprovada?" }
  - { id: mg, type: process, text: "merge em main" }
  - { id: fx, type: process, text: "ajusta e commita" }
edges:
  - { from: m,  to: b }
  - { from: b,  to: c }
  - { from: c,  to: pr }
  - { from: pr, to: mg, label: "sim" }
  - { from: pr, to: fx, label: "não" }
  - { from: fx, to: pr }
:::

O ramo protegido — `main` que só aceita alteração por *pull request*
aprovado, com os testes do capítulo 34 ao 37 passando — é a configuração mais
barata de qualidade que existe. São dois cliques na interface do GitHub.

## Conflito: o que é e como sair

```text title="A mensagem que assusta e não deveria"
Auto-merging ProductService.java
CONFLICT (content): Merge conflict in ProductService.java
Automatic merge failed; fix conflicts and commit the result.
```

```java title="O arquivo fica assim" numbered
<<<<<<< HEAD
    return repository.findAll(pageable)
            .map(ProductResponse::of);
=======
    return repository.findAll(spec, pageable)
            .map(ProductResponse::of);
>>>>>>> feat/busca-por-nome
```

Entre `<<<<<<<` e `=======` está a sua versão; entre `=======` e `>>>>>>>`, a
do outro ramo. Você apaga os marcadores e deixa o código correto — que pode
ser um dos dois, ou uma terceira coisa que junta os dois.

```bash
git add ProductService.java
git commit          # a mensagem de merge já vem pronta
```

:::pitfall
Conflito não é erro: é o Git dizendo que duas pessoas mudaram a mesma linha e
que ele não tem como adivinhar qual vale. Aceitar cegamente "a minha versão"
para se livrar da tela é como apagar o trabalho do colega sem ler — e
acontece o tempo todo. Leia os dois lados. Em caso de dúvida, chame a pessoa.
:::

## Desfazer, sem drama

```bash title="Os quatro desfazeres úteis" numbered
git restore ProductService.java     # descarta alteração não commitada
git restore --staged arquivo.java   # tira do "add"
git commit --amend                  # corrige o último commit (local!)
git revert a1b2c3d                  # desfaz criando outro commit
```

:::pitfall
`git reset --hard` apaga trabalho não commitado e não tem volta. E
`git push --force` reescreve a história do servidor: se alguém já tinha
puxado aquele ramo, o repositório dela passa a divergir do seu de um jeito
confuso. Em ramo compartilhado, desfaça com `revert`, que cria um commit novo
e preserva o histórico.
:::

## O histórico como ferramenta

```bash title="O que você vai usar quando algo quebrar" numbered
git log --oneline -20
git log -p ProductService.java    # a história de um arquivo
git blame ProductService.java     # quem escreveu cada linha
git bisect start                  # acha o commit que quebrou
```

`git blame` tem fama injusta de ferramenta de acusação. Na prática, ele é o
caminho mais rápido para **a mensagem de commit** que explica por que aquela
linha estranha existe — e é aí que a qualidade das mensagens deixa de ser
etiqueta e passa a ser economia de tempo.

:::story Funciona na minha máquina
O bug apareceu na quinta e só acontecia em homologação.

Carlos rodou local: funcionava. Rodou de novo: funcionava. Passou a manhã
comparando configuração, versão de Java, versão do PostgreSQL.

Às onze e meia, Marina pediu para ver o `git status` dele.

```text
On branch feat/filtros
Changes not staged for commit:
  modified:   src/main/resources/application.properties
  modified:   src/main/java/.../ProductSpecs.java
  modified:   src/main/java/.../SecurityConfig.java
```

Três arquivos alterados e não commitados. Funcionava na máquina do Carlos
porque a correção existia só na máquina do Carlos — em arquivos que ele tinha
mexido na terça e esquecido.

— Não é que funcione na sua máquina — disse Marina. — É que a sua máquina tem
um software que não existe em lugar nenhum. Nem no repositório.

No commit daquela tarde, Carlos escreveu a mensagem mais longa da vida dele.
Marina aprovou sem comentários.
:::

:::summary
- `status`, `add`, `commit`, `push` resolvem o dia; o resto é para quando
  algo dá errado.
- `.gitignore` no primeiro dia; senha nunca, em nenhum commit.
- A mensagem explica o **porquê**; o diff já mostra o quê.
- Um ramo por funcionalidade, `main` protegido por *pull request* e testes.
- Conflito é uma pergunta, não um erro. `revert` em ramo compartilhado,
  nunca `push --force`.
:::

:::checkpoint
Você versiona o projeto, escreve commits que explicam a intenção, trabalha em
ramos com revisão e resolve um conflito lendo os dois lados.
:::

:::milestone
Fim da Parte 9. O projeto tem histórico, documentação que se atualiza sozinha
e requisições versionadas. Tudo que faltava para outra pessoa assumir o
código — e é exatamente isso que a Parte 10 vai pedir de você.
:::

:::exercise level=1
Inicialize o repositório, crie o `.gitignore` e faça o primeiro commit com
uma mensagem que explique o que o projeto é.

:::answer
Um detalhe que quase ninguém faz e vale muito: escreva no corpo do primeiro
commit **por que** o projeto existe e qual problema ele resolve. É a
mensagem que mais gente vai ler, e a única que ninguém consegue reconstruir
depois.
:::

:::exercise level=2
Crie um ramo, altere uma linha, volte para `main`, altere a mesma linha de
outro jeito e provoque um conflito de propósito. Resolva-o.

:::answer
Fazer isso de propósito, com calma, em um projeto que não importa, é a
diferença entre ficar paralisado e resolver em dois minutos no dia em que
acontecer de verdade — que será numa sexta, com pressa.
:::

:::exercise level=3
Use `git bisect` para encontrar o commit que introduziu um defeito. Crie o
cenário: dez commits, um deles quebrando um teste.

:::answer
`git bisect start`, `git bisect bad`, `git bisect good <commit antigo>`, e o
Git faz uma busca binária — dez commits viram três ou quatro verificações.
Com um script de teste, `git bisect run ./mvnw test` acha o culpado sozinho.
É a ferramenta mais subestimada do Git e a que mais impressiona quando você
a usa na frente de alguém.
:::
