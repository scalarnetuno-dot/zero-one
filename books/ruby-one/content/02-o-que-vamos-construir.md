---
title: "O que vamos construir"
number: 2
slug: o-que-vamos-construir
part: p1
kicker: "Nove canteiros, uma plataforma em dois lugares ao mesmo tempo, e uma página que o adendo já prometeu."
goal: >-
  Dizer o que o dia 3 de junho cobra do módulo de contratos, separar a
  pasta de produção da pasta em que você vai escrever, e terminar com o
  Ruby 3.4 instalado e conferido.
---

:::story A PT-118
A Marta pôs o adendo na mesa na segunda, 9 de março.

— A Serra Azul quer ver, na página, qual equipamento está em qual
contrato. O Rômulo já assinou. 3 de junho.

O Renato leu a cláusula sublinhada.

— Uma página. A lista da manhã. O que a Helena já confere.

— O sistema diz uma coisa — disse a Marta. — A planilha diz outra. Ontem a
plataforma PT-118 estava nos dois, em canteiros diferentes.

O Caio olhou o número do patrimônio.

— Doze metros. Serra Azul, Contagem. E também Serra Azul, Betim. O
contrato não pode estar nos dois.

— Então a gente faz um sistema novo, do lado — disse o Rômulo, da porta.

O Renato devolveu o papel.

— Não. A página nova tem de bater com a planilha até a planilha perder.
Outro sistema do lado são duas telas para a Helena conferir, e ela já
conferiu duas ontem.
:::

O módulo se chama Nortea Hub na conversa da sala. No repositório ele não é
outro projeto. É o pedaço de contratos do `nortea` que já está no ar, o
Rails de 2016, reescrito até a manhã conseguir confiar nele. A planilha
`patio_SEMANAL.xlsx` continua sendo a lista pela qual o caminhão sai,
enquanto a tela discordar.

## O que o dia 3 de junho confere

A Helena, e depois a Serra Azul, precisam de três respostas sobre cada
máquina contratada.

Qual equipamento. Qual contrato. Qual período.

Se o contrato foi cancelado, a máquina não pode continuar parecendo
ocupada, e também não pode parecer livre se outro contrato ainda a segura.
A multa de R$ 1.800 por dia nasce exatamente nesse desacordo: o canteiro
espera a plataforma, o pátio acha que ela está livre, ou o contrário.

A página que o adendo promete é essa consulta. Não é um pátio desenhado de
novo. Não é um segundo banco. É a tabela `contracts` dizendo uma coisa só,
a mesma que a planilha diria se alguém tivesse atualizado as duas.

A pasta em que você vai escrever se chama `patio`. Ela não é o `nortea`.
O sistema de produção continua no servidor, com o Ruby 3.3. O que cresce
na sua máquina, nos primeiros arquivos, é Ruby sem Rails: o bastante para
ler o que aquele sistema já faz, quando o arquivo dele entrar na mesa.

## Instalando

A linha deste livro é o Ruby 3.4, publicado no Natal de 2024, em
manutenção normal enquanto o 3.3 do servidor já caminha para a fase só de
segurança. O Ruby 4.0, Natal de 2025, também fala a sintaxe dos exemplos
daqui. Se o instalador oferecer os dois, fique no 3.4: é a linha em que
estas saídas foram pensadas.

No Windows, baixe o **Ruby+Devkit 3.4** em <https://rubyinstaller.org>. O
Devkit é o compilador que algumas gems precisam para instalar; sem ele, a
gem que tem código em C falha com uma mensagem que não fala de contrato.
Na instalação, deixe marcado o Ruby no PATH. PATH é a lista de pastas em
que o terminal procura um comando.

No macOS e no Linux, o `ruby` que já vem no sistema pode ser uma linha
antiga, às vezes a 2.6, que não recebe correção. Rode `ruby -v` antes de
confiar nele. Se não for 3.4, instale o 3.4 pela página
<https://www.ruby-lang.org/en/downloads/> e use esse, não o do sistema.

Feche o terminal se ele já estava aberto, abra de novo, e confira:

```text
$ ruby -v
ruby 3.4.0 (2024-12-25) [x64-mingw-ucrt]
```

O trecho entre parênteses e o nome da plataforma mudam conforme o mês e o
sistema. A resposta precisa começar com `ruby 3.4`. Se o comando não
existir, o terminal não viu a instalação: feche, abra, tente de novo
antes de instalar por cima.

:::warning O terminal que já estava aberto
Um terminal guarda o PATH do momento em que foi aberto. Instalar o Ruby
não atualiza essa cópia. O sintoma é `ruby` desconhecido numa janela e
reconhecido na janela ao lado.
:::

:::pitfall
`ruby` pode existir duas vezes na mesma máquina. O servidor da Nortea
responde 3.3. A sua, se você seguiu o instalador, responde 3.4. Os dois se
chamam Ruby.

No Windows, `where.exe ruby` lista os caminhos. No macOS e no Linux,
`which ruby` mostra qual arquivo o terminal vai chamar. Descubra o seu
agora. "Eu instalei" com o terminal chamando o Ruby do sistema é uma manhã
inteira num erro que não está no arquivo.
:::

:::practice
Rode `ruby -v`. Se a resposta começar com `ruby 3.4`, crie a pasta e entre
nela:

```text
$ mkdir patio
$ cd patio
```

Não rode `bundle install`. Não copie o `Gemfile` da Nortea. A pasta
`patio` começa vazia: ainda não existe um programa.
:::

:::summary
- O Hub é o módulo de contratos do Rails que já está no ar, não um segundo
  sistema ao lado da planilha.
- O dia 3 de junho confere equipamento, contrato e período. Cancelado não
  pode continuar ocupando, nem liberar o que outro contrato segura.
- A sua máquina fica no Ruby 3.4. O servidor está no 3.3.
- `ruby -v` confirma a linha. A pasta `patio` começa vazia.
:::

:::milestone
Você tem o Ruby 3.4 instalado, a pasta `patio` criada, e as três respostas
que a Helena vai conferir em 3 de junho. Ainda não há programa. É daqui
que o arquivo começa.
:::

:::exercise level=1
A Helena liga às 6h10: "a PT-118 saiu para Contagem. O canteiro de Betim
está pedindo a mesma". Escreva, em duas linhas, o que ela precisa que o
sistema responda, e o que ela não precisa saber para receber a resposta.

:::answer
Ela precisa saber qual contrato segura a PT-118 agora, e em qual canteiro.
Se houver dois, os dois números. Se não houver nenhum, "livre".

Ela não precisa saber se a resposta saiu de `start_date` ou de
`started_at`, nem qual arquivo Rails montou a frase. A conferência dela é
a plataforma no caminhão.
:::

:::exercise level=2
O Rômulo insiste num sistema novo, em outro servidor, "para não mexer no
legado". A planilha e a tela já discordam sobre a PT-118. O que a Helena
passaria a conferir na manhã seguinte, se o sistema novo nascesse do lado?

:::answer
Três listas: a planilha, a tela de 2016 e a tela nova. O caminhão continua
saindo pela planilha enquanto qualquer uma discordar.

O adendo pede uma consulta que bata com o pátio. Um terceiro lugar aumenta
o número de lugares em que a PT-118 pode estar escrita, sem apagar os dois
que já discordam.
:::

:::exercise level=3
Sem olhar de novo o calendário: em 9 de março de 2026, o Ruby 3.3 do
servidor ainda recebe que tipo de correção, e até quando? E o que muda em
1º de abril?

:::answer
Até 1º de abril de 2026 ele ainda está na manutenção normal: defeito comum
e segurança. A partir dessa data, até 31 de março de 2027, só segurança.

No dia 3 de junho, portanto, um defeito que não seja de segurança não ganha
correção do time do Ruby nessa linha. A Serra Azul não espera por isso. A
data dela é a do adendo, não a do calendário do Ruby.
:::
