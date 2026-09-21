---
title: "Condicionais"
number: 5
slug: condicionais
part: p1
kicker: "Onze regras de empréstimo, quarenta segundos de fala, zero linhas escritas em trinta e um anos."
goal: >-
  Escrever decisões legíveis com `if`, `elseif` e `match`, usar cláusulas de
  guarda, e reconhecer o momento em que a escada de condições está pedindo
  um tipo novo.
---

:::story As onze condições
— Quando é que uma pessoa pode levar um livro? — perguntou Tainá, com o
caderno aberto.

Vera respondeu sem parar de etiquetar:

— Se ela for sócia. Se não tiver livro atrasado. Se não dever multa acima de
cinco reais. Se não estiver com três livros já. Se o exemplar não for da
referência. Se não for o último exemplar do título, aí só sai com
autorização. Se for menor de doze, o responsável assina. Se o livro chegou
essa semana, fica uma semana em exposição. Se for período de prova, o prazo
cai para sete dias. Se for da coleção do Seu Juvenal, não sai de jeito
nenhum, mas isso ninguém escreveu.

Pausa.

— E se for a Dona Marlene, sai. Porque ela sempre devolve.

Tainá contou os riscos no caderno. Eram onze.

— A senhora sabe tudo isso de cor?

— Faço isso há trinta e um anos.

— E onde está escrito?

Vera parou de etiquetar pela primeira vez.

— Em lugar nenhum.
:::

Aquelas onze condições são o primeiro retrato da regra de negócio. Por
enquanto, elas aparecem como uma escada de `if`; mais tarde, quando crescerem,
serão extraídas para nomes e objetos que possam ser testados.

## A regra que Vera guarda na cabeça

Isso não é particularidade de biblioteca. Em toda empresa existe pelo menos
uma regra que:

- é aplicada dezenas de vezes por dia;
- tem exceções que ninguém listou;
- mora na cabeça de uma ou duas pessoas;
- e some quando essas pessoas saem de férias.

O sistema costuma implementar a versão simplificada — a que alguém
conseguiu descrever numa reunião de uma hora — e o restante continua sendo
resolvido no balcão, por quem sabe.

:::note Na sua carreira
Extrair requisito de quem não sabe que tem requisito é uma habilidade
específica, e ela quase nunca é ensinada.

O que **não** funciona: "me manda a regra de empréstimo por escrito". A
pessoa vai escrever as três condições óbvias e esquecer as oito que ela
aplica no automático.

O que funciona:

1. **Peça para ela narrar um caso concreto**, do começo ao fim, com nome e
   data. O concreto puxa os detalhes que a abstração esconde.
2. **Pergunte pelas exceções em vez das regras**: "já aconteceu de você
   deixar levar mesmo com livro atrasado?". Aí vem a Dona Marlene.
3. **Leia a regra de volta, em voz alta**, e espere a correção. A Vera vai
   te corrigir num detalhe que ela não teria lembrado sozinha.
4. **Mostre o código rodando.** Nada extrai requisito como a pessoa vendo o
   sistema recusar alguém que ela deixaria passar.

Os passos 3 e 4 valem mais que os dois primeiros — e são os que a maioria
dos times pula, porque parecem retrabalho.
:::

## Toda decisão deixa um caminho

```php title="emprestimo.php" numbered
<?php

$disponivel = true;

if ($disponivel) {
    echo "Pode emprestar\n";
} else {
    echo "Exemplar indisponível\n";
}
```

Parênteses obrigatórios em volta da condição, chaves delimitando o bloco.
Quem vem de Python estranha as chaves; quem vem de Java se sente em casa.

Quando você omite o `else`, o caminho do "não" continua existindo — ele
apenas não faz nada. Ter consciência disso é o que separa o programa correto
do programa que só parece correto.

:::diagram type="flowchart" caption="Toda decisão tem dois caminhos, mesmo quando você escreve só um."
nodes:
  - { id: ini, type: start,    text: "Início" }
  - { id: d1,  type: decision, text: "disponível?" }
  - { id: sim, type: process,  text: "empresta" }
  - { id: nao, type: process,  text: "(nada)" }
  - { id: fim, type: start,    text: "Fim" }
edges:
  - { from: ini, to: d1 }
  - { from: d1,  to: sim, label: "sim" }
  - { from: d1,  to: nao, label: "não" }
  - { from: sim, to: fim }
  - { from: nao, to: fim }
:::

Numa API, esse caminho vazio vira um defeito visível: o cliente pede um
recurso que não existe e recebe `200` com corpo vazio.

### As chaves não são opcionais

O PHP permite omitir as chaves quando o bloco tem uma linha só. E permitir
isso já custou muito dinheiro ao mundo:

:::compare left="O que parece" right="O que o PHP lê" lang="php"
if ($ok)
    liberar();
    registrar();
---
if ($ok) {
    liberar();
}
registrar();
:::

`registrar()` roda sempre, porque a indentação não significa nada para o
interpretador.

:::key
**Use chaves sempre**, inclusive em bloco de uma linha. É a regra de estilo
mais fácil de justificar numa revisão, está na PSR-12, e qualquer formatador
automático vai colocá-las por você.
:::

Existe ainda a sintaxe alternativa, com `:` e `endif`:

```php
<?php if ($disponivel): ?>
    <span class="livre">Disponível</span>
<?php else: ?>
    <span class="preso">Emprestado</span>
<?php endif; ?>
```

Ela existe para ser usada **dentro de HTML**, onde uma chave solta no meio
da marcação fica ilegível. Em código PHP puro, não use. No capítulo
@cap:blade ela some de vez, substituída por `@if`.

## Comece com uma escada

```php title="situacao.php" numbered
<?php

$dias_atraso = 9;

if ($dias_atraso <= 0) {
    $situacao = 'em dia';
} elseif ($dias_atraso <= 7) {
    $situacao = 'atrasado';
} elseif ($dias_atraso <= 30) {
    $situacao = 'notificado';
} else {
    $situacao = 'suspenso';
}

echo $situacao, "\n";
```

A ordem importa: o primeiro teste verdadeiro vence e os demais nem são
avaliados. Por isso a escada vai do caso mais restritivo ao mais geral — na
ordem inversa, `<= 30` engoliria todos os casos acima.

Repare em `elseif`, junto. Existe também `else if`, separado, que funciona
em código PHP puro e **quebra** na sintaxe alternativa com `endif`. Use
sempre a forma junta.

## Quando chega a décima segunda regra

Dedé implementou as onze regras da Vera como uma escada de `if`. Levou uma
tarde e ficou com oitenta e três linhas.

```php title="podeEmprestar.php (a versão que não sobreviveu)" numbered
<?php

function podeEmprestar(array $leitor, array $exemplar): bool
{
    if (!$leitor['socio']) {
        return false;
    } elseif ($leitor['atrasados'] > 0) {
        return false;
    } elseif ($leitor['multa'] > 500) {
        return false;
    } elseif ($leitor['emprestimos'] >= 3) {
        return false;
    } elseif ($exemplar['referencia']) {
        return false;
    } elseif ($exemplar['ultimo'] && !$leitor['autorizado']) {
        return false;
    }
    // ... mais cinco
    return true;
}
```

Funcionou. Passou uma semana em produção sem reclamação.

Na terça seguinte, a Vera avisou que em janeiro o limite sobe de três para
cinco livros, porque é período de férias escolares.

Dedé abriu o arquivo. A regra do limite estava na quarta condição. Para
acrescentar "exceto em janeiro", ele precisava:

- saber que a quarta condição era a do limite (não há nome, só um número);
- decidir se a exceção entra ali dentro ou vira uma condição nova;
- e garantir que a ordem continuasse correta em relação às outras dez.

Ele acrescentou um `&&` na quarta condição. Duas semanas depois, alguém
descobriu que leitores suspensos passaram a pegar cinco livros em janeiro.

## O código ficou parecido com o balcão

**A escada não tem nomes.** Onze condições anônimas, distinguidas por
posição. Quando a décima segunda chega, ninguém sabe onde ela entra sem ler
as onze.

**A função devolve `bool` e perde o motivo.** `false` significa onze coisas
diferentes, e quem chama não consegue dizer ao leitor por que ele foi
recusado. É o mesmo defeito do capítulo @cap:variaveis-e-tipos, agora em
escala.

**E a estrutura escondeu a mudança.** Um `&&` acrescentado no meio de uma
escada de onze degraus é invisível numa revisão de código — a linha continua
com o mesmo formato, e nenhuma outra linha mudou.

:::pitfall
Uma escada com mais de quatro degraus é sinal de que falta um conceito. No
capítulo @cap:enums-datas-e-valores essa situação vira um `enum` com um
método; no @cap:services, cada regra vira um método com nome próprio e uma
exceção específica.

Quando você se pegar escrevendo o sexto `elseif`, pare e pergunte que tipo
está faltando. A resposta quase nunca é "mais um `elseif`".
:::

:::art caption="A regra de negócio mais completa da empresa costuma morar na cabeça de uma pessoa só."
Charge editorial minimalista em fundo branco: uma bibliotecária mais velha
atrás de um balcão de madeira, etiquetando livros sem olhar, enquanto fala.
Saindo da fala dela, um fluxograma enorme se desenha no ar, com dezenas de
losangos de decisão e setas que se cruzam, ocupando metade do quadro. De pé
na frente do balcão, uma estagiária com um caderno pequeno demais,
escrevendo rápido. Poucos elementos, humor seco, estética de revista de
tecnologia.
:::

## Guardas para proteger a regra

**Primeiro: cláusulas de guarda com nome.**

:::compare left="Aninhado" right="Cláusula de guarda" lang="php"
if ($leitor !== null) {
    if ($leitor->ativo) {
        if (!$leitor->temMulta()) {
            emprestar($leitor);
        }
    }
}
---
if ($leitor === null) {
    return;
}
if (!$leitor->ativo) {
    return;
}
emprestar($leitor);
:::

Trate o caso ruim, saia, e deixe o caminho feliz encostado na margem
esquerda. O lado esquerdo cresce para a direita a cada regra nova — e, com
onze regras, a chamada principal fica a quarenta e quatro espaços da
margem.

:::key
Se o corpo principal da sua função está com três níveis de indentação, quase
sempre faltam guardas no começo. Indentação profunda não é problema
estético: é um relatório de quantas condições o leitor precisa manter na
cabeça ao mesmo tempo.
:::

**Segundo: cada regra com nome e motivo.** A versão que o capítulo
@cap:services vai construir tem esta forma:

```php title="para onde isso vai" numbered
<?php

if (!$leitor->ehSocio()) {
    throw new LeitorNaoSocio($leitor->id);
}

if ($leitor->temAtrasos()) {
    throw new LeitorComPendencia($leitor->id);
}

if ($leitor->atingiuLimite($this->limiteVigente($data))) {
    throw new LimiteDeEmprestimosAtingido($leitor->id);
}
```

Agora a décima segunda regra entra num lugar óbvio, o motivo da recusa chega
ao leitor, e o limite virou uma pergunta com data — que é exatamente onde a
exceção de janeiro mora.

## `match` não é `switch`

O PHP tem `switch` desde sempre, com dois defeitos clássicos: comparação
frouxa e *fall-through*. Esquecer um `break` faz a execução escorregar para
o caso seguinte, silenciosamente.

Desde o PHP 8 existe `match`, que resolve os dois:

```php title="match.php" numbered
<?php

$rotulo = match ($status) {
    'disponivel' => 'Livre',
    'emprestado' => 'Com leitor',
    'reservado', 'transito' => 'Indisponível',
    default => 'Desconhecido',
};
```

| | `switch` | `match` |
|---|---|---|
| Comparação | `==` | `===` |
| Escorrega | sim, sem `break` | não |
| Devolve valor | não | sim |
| Caso não previsto | ignora | erro, sem `default` |

Tabela: Não há caso em que `switch` seja melhor, exceto quando um braço
precisa de várias instruções — e aí, quase sempre, o que falta é uma função.

`match` também funciona sem argumento, como escada de condições:

```php title="match_condicional.php" numbered
<?php

$situacao = match (true) {
    $dias <= 0 => 'em dia',
    $dias <= 7 => 'atrasado',
    $dias <= 30 => 'notificado',
    default => 'suspenso',
};
```

Mesmo resultado da escada, em cinco linhas em vez de nove — e como
expressão, o que evita a variável ser atribuída em quatro lugares.

:::key
A ausência de `default` no `match` é funcionalidade, não esquecimento.
Quando o capítulo @cap:enums-datas-e-valores transformar `status` num enum,
um `match` sem `default` passa a falhar **na hora** em que alguém
acrescentar um valor novo sem tratar o caso. É um lembrete automático,
entregue pela linguagem.
:::

## O que é verdadeiro

A regra completa cabe numa frase: **vazio é falso, zero é falso, `null` é
falso, `"0"` é falso, todo o resto é verdadeiro.**

| Falso | Verdadeiro |
|---|---|
| `false`, `null` | `true` |
| `0`, `0.0`, `-0.0` | qualquer outro número |
| `""` e `"0"` | qualquer outra string, inclusive `"0.0"` |
| `[]` | array com qualquer item |

Tabela: `"0.0"` é verdadeiro e `"0"` é falso. É o item mais arbitrário da
lista, e o motivo de o capítulo @cap:variaveis-e-tipos insistir em comparar
explicitamente.

E o ternário aninhado sem parênteses não existe mais:

```text
PHP Fatal error: Unparenthesized `a ? b : c ? d : e` is not
supported.
```

Antes do PHP 8 ele era avaliado da esquerda para a direita — ao contrário de
praticamente toda outra linguagem — e produzia resultados que ninguém
previa. A linguagem preferiu quebrar o código existente a continuar
respondendo errado.

:::summary
- Chaves sempre; a sintaxe alternativa com `endif` é só para HTML.
- Todo `if` sem `else` deixa um caminho implícito — saiba qual é.
- `elseif` junto, e escada longa é sintoma de tipo faltando.
- Escada anônima esconde mudança: cada regra merece nome e motivo.
- Cláusula de guarda mantém o caminho feliz na margem esquerda.
- `match` é expressão, compara com `===`, não escorrega e recusa o caso não
  previsto.
- Vazio, zero, `null` e `"0"` são falsos; o resto é verdadeiro.
:::

:::milestone
O programa agora decide. As onze regras da Vera ainda estão espalhadas numa
escada — mas, pela primeira vez em trinta e um anos, elas existem em algum
lugar além da cabeça dela.
:::

:::exercise level=1
Escreva uma condição que imprima `"Devolver hoje"`, `"Em dia"` ou
`"Atrasado"` conforme os dias restantes para a devolução.

:::answer
```php
$situacao = match (true) {
    $dias_restantes < 0 => 'Atrasado',
    $dias_restantes === 0 => 'Devolver hoje',
    default => 'Em dia',
};
```
A ordem é o que faz funcionar: `< 0` precisa vir antes, senão `=== 0` nunca
seria alcançado por um número negativo — e, pior, `default` pegaria o
atraso e diria "Em dia".
:::

:::exercise level=2
Reescreva o trecho abaixo com cláusulas de guarda, mantendo as mensagens.

```php
if ($exemplar !== null) {
    if ($exemplar->status === 'disponivel') {
        if ($leitor->emprestimosAbertos() < 3) {
            emprestar($exemplar, $leitor);
        } else {
            echo "Limite atingido";
        }
    } else {
        echo "Indisponível";
    }
} else {
    echo "Exemplar não encontrado";
}
```

:::answer
```php
if ($exemplar === null) {
    echo "Exemplar não encontrado";
    return;
}

if ($exemplar->status !== 'disponivel') {
    echo "Indisponível";
    return;
}

if ($leitor->emprestimosAbertos() >= 3) {
    echo "Limite atingido";
    return;
}

emprestar($exemplar, $leitor);
```
Mais linhas e menos indentação — e cada motivo de recusa fica ao lado da sua
condição, em vez de num `else` a doze linhas de distância. O `echo` aqui é
provisório: no capítulo @cap:excecoes cada um desses vira uma exceção com
nome.
:::

:::exercise level=3
A Vera avisou que, em janeiro, o limite sobe de três para cinco livros — mas
não vale para leitor suspenso. Implemente isso de duas formas: acrescentando
à escada do capítulo e extraindo uma função. Depois diga qual você deixaria
no projeto, e o que a sua escolha custa.

:::answer
**Forma 1 — na escada:**

```php
} elseif ($leitor['emprestimos'] >= (
    (int) date('n') === 1 && !$leitor['suspenso'] ? 5 : 3
)) {
    return false;
}
```

Funciona. Cabe numa linha. E tem três problemas: a regra de janeiro ficou
escondida dentro de uma condição de limite, `date('n')` lê o relógio do
servidor no meio de uma regra de negócio, e a expressão agora tem duas
condições que não têm relação uma com a outra.

**Forma 2 — extraindo:**

```php
function limiteDeEmprestimos(
    array $leitor,
    DateTimeImmutable $data,
): int {
    if ($leitor['suspenso']) {
        return 0;
    }

    $ferias = (int) $data->format('n') === 1;

    return $ferias ? 5 : 3;
}
```

Eu deixaria a segunda, por três motivos concretos.

**A regra ganhou nome.** Quando a Vera disser em março que julho também é
férias, a pessoa que for mexer procura por `limiteDeEmprestimos` e encontra
uma função de oito linhas — não a quarta condição de uma escada de onze.

**A data entra por parâmetro.** Isso permite testar janeiro em qualquer dia
do ano, sem mexer no relógio da máquina. É a mesma regra do capítulo
@cap:funcoes, e ela paga sozinha no capítulo @cap:testes.

**O leitor suspenso ficou explícito**, retornando zero. Na forma 1, ele
estava escondido num operador ternário dentro de uma comparação — que é
exatamente onde o defeito real apareceu na história deste capítulo.

**O que isso custa:** um arquivo a mais, uma função a mais, e uma indireção
a mais para quem está lendo o fluxo principal. Em um sistema de três telas,
esse custo é real e pode não valer a pena. Em um sistema que vai crescer por
anos, com uma regra que já mudou duas vezes em duas semanas, ele se paga na
terceira mudança.

A pergunta honesta, que vale para toda decisão de arquitetura deste livro,
não é "qual é mais elegante". É: **quantas vezes essa regra vai mudar?** Se
a resposta for "nunca mais", a escada está boa.
:::

:::story A piada final
Na quinta, Tainá mostrou para a Vera a tela nova recusando um empréstimo,
com a mensagem *"Leitor com pendência: 1 livro atrasado"*.

Vera leu, concordou com a cabeça, e olhou para a fila.

— A Dona Marlene tá com um atrasado.

— Então o sistema vai recusar.

Vera olhou para a tela. Olhou para a Dona Marlene. Olhou para a tela de
novo.

— Põe uma exceção aí.

Tainá anotou no caderno, na seção "para perguntar depois", logo abaixo de
*"e se o livro tiver dois autores?"*:

> *"regra nº 12: a Dona Marlene"*
:::
