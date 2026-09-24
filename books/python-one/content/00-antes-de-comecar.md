---
title: "Antes de começar"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Um notebook de 2021, um post-it dizendo para não desligar, e um preço de tomate que dobra se alguém rodar a célula errada."
---

Esta é a pasta do computador do galpão, o `GALPAO-02`, que ninguém desliga
desde março de 2021:

```text
fechamento_FINAL_v7.ipynb
fechamento_FINAL_v7_BACKUP.ipynb
fechamento_NAO_USAR.ipynb
precos.py
precos_novo.py
precos2_NOVO_final.py
requirements.txt
SABIA_PRECOS_OFICIAL_FINAL.xlsx
```

O `requirements.txt` tem três linhas. Duas estão comentadas. Nenhuma fixa
versão. A planilha tem trinta e uma abas e é editada por duas pessoas ao
mesmo tempo. O notebook importa `pandas` para abrir essa planilha, calcular
a margem e cuspir o preço que a Dona Neuza cola na caixa.

E funciona.

Quatro anos de feira, duzentos produtores, o fechamento da manhã saindo
antes das sete. A Dona Neuza abre o galpão às seis, pesa, confere e fecha às
cinco. Nesses quatro anos o preço saiu errado um punhado de vezes, e todas
as vezes alguém rodou uma célula que tinha um comentário em vermelho pedindo
para não rodar.

Você vai substituir essa pasta. Não porque ela é ruim — porque ela só roda
naquele computador, na ordem em que o Cacá lembrava de executar as células, e
não tem mais para onde crescer.

## A cooperativa, a empresa e a data

A **Cooperativa Sabiá** reúne duzentos produtores de hortifrúti. A **Oficina
Leme** — vinte e oito pessoas, o tipo de software house que vive de sistema
que a planilha não aguenta mais — assinou o contrato para trocar o notebook
por um programa que outra empresa consiga chamar.

E existe uma data que ninguém pode empurrar.

A **Rede Bem-Te-Vi**, onze lojas, renova o fornecimento em **15 de abril**.
Sem um jeito de consultar preço e estoque sem abrir a planilha, eles compram
da cooperativa de baixo. O fornecimento é R$ 1,2 milhão no ano. O contrato
com a Leme é R$ 74 mil, preço fechado.

Nada disso é cenário. Prazo que não se move, orçamento pequeno em cima de
um contrato grande, requisito que chega na sexta e um computador de galpão
que precisa continuar fechando o dia enquanto o substituto é construído — é
isso que transforma escolha técnica em decisão. Optar entre duas formas de
escrever a mesma coisa só fica interessante quando uma delas custa a manhã
da Dona Neuza.

## Quem aparece

**Bia** tem seis anos de carreira, dois deles na Leme, e é a voz que
explica o porquê. Está no projeto porque foi a única que aceitou abrir o
notebook antes de estimar.

**Elias** está na Leme há oito anos. Responde olhando para a tela, em geral
sem parar de andar, e já aprendeu que resposta precisa vira tarefa com o
nome dele.

**Rafa** é estagiário, quarto período. Faz a pergunta que a sala inteira
estava evitando, porque é a única pessoa que não perde nada ao dizer que não
entendeu.

**Dona Neuza** comanda o galpão há trinta e um anos. Sabe de cor a margem de
cada produtor e nunca escreveu nenhuma. O comentário `# NÃO RODAR` foi ela
quem ditou. O Cacá só digitou.

**Helena** administra o prazo. O trabalho real dela é receber 15 de abril de
cima e reemitir a data para baixo em forma de sprint.

**Sérgio** é diretor da Leme. Nunca escreveu Python e não finge que
escreveu. Volta de palestra com uma caixa nova para o slide.

**Cacá** é o sobrinho que escreveu o notebook em 2021, aos vinte e três
anos, num fim de semana que virou quatro anos. Mudou de estado. Quando
alguém pergunta por que a margem está daquele jeito, a resposta da sala é
sempre a mesma: o Cacá sabe.

E o **GALPAO-02**, com o post-it, é o sistema em produção. Ele não é o
vilão. Cada coisa nova que aparecer aqui vai ser medida contra ele — e em
algumas dessas medições o notebook ganha.

## Como o código aparece

Código aparece assim, às vezes com o nome do arquivo:

```python title="preco.py"
preco = 19.90
print(f"R$ {preco:.2f}")
```

O que o terminal responde aparece sem nome de arquivo e sem realce:

```text
R$ 19.90
```

E quando o programa quebra — o que vai acontecer muito, de propósito — o
erro vem inteiro, do começo ao fim, porque as linhas do meio são as que
importam.

:::key
Comando de terminal aparece com `$` na frente. O `$` representa o prompt e
não faz parte do comando: não digite.
:::

Você não precisa instalar nada para começar a ler. Quando o primeiro
programa precisar rodar, a instalação vem junto, com o teste que confirma
que deu certo.

A data que ninguém pode empurrar é 15 de abril. Até lá, a Dona Neuza abre às
seis e o notebook fecha o dia.
