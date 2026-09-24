---
title: "Encapsulamento"
number: 19
slug: encapsulamento
part: p3
kicker: "O relatório dizia que três exemplares estavam emprestados duas vezes. Seis lugares diferentes escreviam naquela coluna."
goal: >-
  Escolher o que fica público, escrever um objeto cujo estado inválido é
  impossível de alcançar por fora, usar `readonly` para o que não muda e
  reconhecer quando `static` virou variável global com outro nome.
---

:::story Seis lugares
O relatório de circulação de fevereiro acusou três exemplares emprestados
duas vezes ao mesmo tempo. Fisicamente impossível: o livro estava na
estante, e a Vera trouxe um deles para a reunião como prova.

Dedé procurou no Sistema quem escrevia na coluna `status` dos exemplares.

```text
$ grep -rn "status *=" *.php | wc -l
6
```

— Seis — disse ele.

— Seis funções?

— Seis lugares. A tela de empréstimo, a de devolução, a de renovação, o
importador, um script de correção que alguém rodou em 2019 e deixou na
pasta, e o relatório.

Tainá levou um tempo na última.

— O relatório escreve?

— O relatório corrige. Quando acha uma linha estranha, ele conserta.

— Conserta pra quê?

— Pra sair bonito.
:::

## `public` é uma permissão para sempre

O `Exemplar` que o projeto tem hoje não impede nada:

```php title="src/Acervo/Exemplar.php" numbered
<?php

namespace CasaAmarela\Acervo;

class Exemplar
{
    public function __construct(
        public int $tombo,
        public Livro $livro,
        public string $estado = 'bom',
    ) {}
}
```

Todas as propriedades são públicas, e público quer dizer que qualquer linha
de qualquer arquivo pode escrever qualquer coisa:

```php
$exemplar->estado = 'emprestadoo';
$exemplar->estado = 'sei lá';
$exemplar->tombo = -3;
```

Nenhum aviso. Três estados que não existem, um tombo negativo, e o objeto
segue circulando pelo programa como se estivesse inteiro.

Isso é a mesma doença da coluna `status` do Sistema, um andar acima. O
problema nunca foi a escrita em si — foi haver seis lugares com permissão
para escrever, e nenhum deles com a obrigação de conferir.

:::key
`public` não é "o padrão". É uma decisão, e ela é quase irreversível: no dia
em que você quiser fechar a propriedade, vai precisar encontrar e corrigir
todo mundo que aprendeu a escrever nela.

Comece fechado. Abrir depois custa uma linha; fechar depois custa uma
reunião.
:::

## `private`: a placa que o PHP fiscaliza

Troque uma palavra:

```php title="src/Acervo/Exemplar.php" numbered
    public function __construct(
        public int $tombo,
        public Livro $livro,
        private string $estado = 'bom',
    ) {}
```

E as tentativas de fora param de funcionar:

```php
$exemplar->estado = 'sei lá';
```

```text
Fatal error: Uncaught Error: Cannot access private property
CasaAmarela\Acervo\Exemplar::$estado
```

A leitura também para — `private` fecha a porta nos dois sentidos.

São três níveis, e no dia a dia você usa dois:

| | Quem alcança |
|---|---|
| `public` | qualquer código, de qualquer lugar |
| `protected` | a própria classe e as que herdarem dela |
| `private` | só a própria classe |

Tabela: `protected` é uma escolha para quem já decidiu que a classe vai ter
descendentes. Enquanto não tiver, `private` é a resposta certa.

:::pitfall
A visibilidade do PHP é fiscalizada pela linguagem, e por isso funciona — é
diferente da convenção de outras linguagens, em que um sublinhado na frente
do nome pede educadamente que ninguém mexa.

Mas ela vale por **classe**, não por objeto. Um método de `Exemplar` pode
ler o `estado` privado de *outro* `Exemplar` recebido como parâmetro. Isso
surpreende quem chega de fora e é o que torna possível escrever um
`equals()` honesto.
:::

## Invariante

Fechar a propriedade não adianta se o objeto puder nascer errado.

:::term Invariante
Uma afirmação sobre o objeto que precisa ser verdadeira **desde o
nascimento até o fim**, aconteça o que acontecer entre uma coisa e outra.

Não é validação de formulário, que acontece uma vez na entrada. É uma
promessa permanente da classe: se ela vale, nenhum código que receba esse
objeto precisa conferir de novo.
:::

O `Exemplar` da Casa Amarela tem três:

1. o tombo é um número positivo;
2. o estado é um dos cinco que o acervo reconhece;
3. um exemplar emprestado não pode ser emprestado de novo.

As duas primeiras são sobre o nascimento. A terceira é sobre a mudança.

## O construtor que recusa

```php title="src/Acervo/Exemplar.php" numbered
<?php

namespace CasaAmarela\Acervo;

class Exemplar
{
    private const ESTADOS = [
        'bom', 'emprestado', 'danificado', 'restauro', 'extraviado',
    ];

    public function __construct(
        public int $tombo,
        public Livro $livro,
        private string $estado = 'bom',
    ) {
        if ($tombo <= 0) {
            throw new \InvalidArgumentException(
                "Tombo inválido: {$tombo}"
            );
        }

        if (!in_array($estado, self::ESTADOS, true)) {
            throw new \InvalidArgumentException(
                "Estado desconhecido: {$estado}"
            );
        }
    }
}
```

Três coisas novas na mesma tela, e as três são curtas.

`private const ESTADOS` é uma **constante de classe**: um valor fixo que
pertence à classe em vez de a cada objeto. Escreve-se uma vez e lê-se com
`self::ESTADOS` — `self` quer dizer "esta classe aqui".

`throw` interrompe o método na hora e entrega o problema a quem chamou. É o
mesmo mecanismo do `PDOException`, agora partindo do seu código.
`InvalidArgumentException` é o tipo que o PHP oferece para dizer "o
argumento que você passou está fora do combinado".

A barra na frente de `\InvalidArgumentException` é a mesma do `\PDO`: a
classe mora na raiz, e este arquivo tem namespace.

```php
$exemplar = new Exemplar(-3, $livro);
```

```text
Fatal error: Uncaught InvalidArgumentException: Tombo inválido: -3
```

O objeto não existiu. Não existe, em lugar nenhum do programa, um `Exemplar`
com tombo negativo — e isso é uma afirmação sobre o sistema inteiro que cabe
em quatro linhas.

## Getter e setter não são obrigatórios

O reflexo de quem aprendeu orientação a objetos em curso é este:

```php
public function getEstado(): string { return $this->estado; }
public function setEstado(string $e): void { $this->estado = $e; }
```

Com esses dois métodos, a propriedade voltou a ser pública — com mais duas
linhas, um nome pior e a aparência de estar protegida. O `setEstado` aceita
`'sei lá'` exatamente como o `public` aceitava.

Pergunte duas coisas antes de escrever cada um:

**O lado de fora precisa disso?** Se ninguém chama, não escreva. Um método
público que não é chamado ainda é uma promessa que alguém pode cobrar
amanhã.

**A mudança tem nome?** Um exemplar não "tem o estado alterado para
emprestado". Ele **é emprestado**. O nome do método é o nome do
acontecimento, e é aí que a regra encontra onde morar.

## `readonly`: o dado que não muda de ideia

Tombo não muda. Depois que a etiqueta é colada no livro, aquele número é
daquele exemplar até o fim.

```php title="src/Acervo/Exemplar.php" numbered
    public function __construct(
        public readonly int $tombo,
        public readonly Livro $livro,
        private string $estado = 'bom',
    ) {
```

```php
$exemplar->tombo = 9;
```

```text
Fatal error: Uncaught Error: Cannot modify readonly property
CasaAmarela\Acervo\Exemplar::$tombo
```

`readonly` permite escrever uma vez, de dentro da classe, e recusa todo o
resto. Com ele, `public` deixa de ser perigoso: ler não quebra nada, e
escrever não é mais possível.

É a combinação que resolve a maioria dos casos: **público e `readonly` para
o que não muda, privado para o que muda**.

:::key
A pergunta que separa os dois é sempre a mesma, e não é técnica: *no mundo
real, isso muda?*

O tombo não muda. O livro daquele exemplar não muda. O estado muda o tempo
todo — e por isso ele é o único que precisa de uma porta com nome.
:::

## Uma porta para cada mudança

Falta a terceira invariante, que é sobre a mudança e não sobre o
nascimento.

```php title="src/Acervo/Exemplar.php" numbered
    public function estado(): string
    {
        return $this->estado;
    }

    public function disponivel(): bool
    {
        return $this->estado === 'bom';
    }

    public function emprestar(): void
    {
        if ($this->estado !== 'bom') {
            throw new \RuntimeException(
                "Exemplar {$this->tombo} não sai: {$this->estado}"
            );
        }

        $this->estado = 'emprestado';
    }

    public function devolver(string $estadoNaVolta = 'bom'): void
    {
        if ($this->estado !== 'emprestado') {
            throw new \RuntimeException(
                "Exemplar {$this->tombo} não está emprestado"
            );
        }

        if (!in_array($estadoNaVolta, self::ESTADOS, true)) {
            throw new \InvalidArgumentException(
                "Estado desconhecido: {$estadoNaVolta}"
            );
        }

        $this->estado = $estadoNaVolta;
    }
```

Agora a coluna tem uma porta só, e a porta confere:

```php
$exemplar->emprestar();
$exemplar->emprestar();
```

```text
Fatal error: Uncaught RuntimeException:
Exemplar 2117 não sai: emprestado
```

Os três exemplares emprestados duas vezes do relatório de fevereiro deixam
de ser possíveis — não porque a equipe passou a tomar mais cuidado, mas
porque não existe mais um caminho que leve até lá.

E repare no `devolver`: ele aceita o estado da volta, porque livro volta
rasgado. O que ele não aceita é qualquer texto, e não aceita devolver o que
não saiu.

:::note Na sua carreira
"Seis lugares escrevem nessa coluna" é uma frase que você vai dizer, e a
resposta quase sempre é "então some um". Uma sétima tela precisa mudar o
estado, ninguém quer mexer nas seis existentes, e o prazo é terça.

O caminho que costuma funcionar não é pedir uma refatoração: é escrever a
porta, usá-la na tela nova, e migrar um dos seis a cada vez que alguém tiver
que abrir aquele arquivo por outro motivo. A conversa muda quando você
consegue dizer "hoje são quatro" numa reunião em que, mês passado, eram
seis.

Guarde o número. Dívida técnica sem número vira opinião, e opinião perde
para prazo todas as vezes.
:::

## `static`: ferramenta ou variável global disfarçada

Uma propriedade `static` pertence à classe, não ao objeto: existe uma só,
compartilhada por todos.

```php
class Exemplar
{
    public static int $emprestadosHoje = 0;
}
```

Isso não é um contador do acervo. É uma variável global com um nome mais
bonito — qualquer código pode somar, ninguém precisa dizer por quê, e o
valor não pertence a nenhum objeto em particular.

O teste que separa o uso legítimo do disfarce é curto: **o valor depende de
quem está usando o sistema agora?** Se depender, `static` é o lugar errado.

Um `static` que guarda a conversão de moeda do dia é discutível. Um que
guarda o usuário logado é um defeito esperando um servidor que atenda duas
requisições ao mesmo tempo — e é assim que, em produção, a Vera vê o nome da
Neide no canto da tela.

Métodos `static` têm o mesmo cheiro quando guardam estado, e são inofensivos
quando não guardam: uma função de conversão que só depende dos argumentos
pode ser `static` sem problema nenhum.

## A superfície pública é uma promessa

Tudo que é público é uma promessa a quem usa a classe: *isto vai continuar
existindo, com este nome e este comportamento*.

O `Exemplar` de agora promete cinco coisas — `tombo`, `livro`, `estado()`,
`disponivel()`, `emprestar()`, `devolver()` — e esconde uma: que o estado é
uma `string`. Amanhã ele pode virar outra coisa sem que uma linha de fora
mude, porque ninguém de fora tem como saber o que é.

Foi isso que o encapsulamento comprou. Não é organização; é liberdade de
mudar de ideia depois.

Existe uma palavra que faz a promessa oposta. `final` na frente de uma
classe diz que ninguém pode herdar dela, e na frente de um método, que
ninguém pode trocar o comportamento. Ela reduz o que você promete, e por
isso aumenta o que você pode mudar.

:::tree title="Onde estamos agora"
acervo/
  src/
    Acervo/
      Livro.php
      Exemplar.php   # readonly + estado privado com porta
    Leitores/
      Leitor.php
    Legado/
      Livro.php
  conexao.php
  listar.php
  emprestar.php
  recibo.php
:::

:::milestone
Fim da Parte 3. O projeto tem nome, dependências declaradas, classes com
endereço e objetos que recusam nascer errados. Um arquivo virou trinta — e
trinta arquivos com contrato é outra coisa que trinta arquivos soltos.
:::

:::summary
- `public` é permissão permanente: comece fechado, abra quando alguém
  precisar.
- `private` é fiscalizado pela linguagem e vale por classe, não por objeto.
- Invariante é o que precisa ser verdade do nascimento ao fim; o construtor
  é onde ela começa a valer.
- `throw` no construtor impede o objeto inválido de existir em qualquer
  lugar do programa.
- Getter e setter automáticos devolvem a propriedade ao público com mais
  linhas.
- `readonly` deixa `public` seguro para o que não muda.
- Mudança de estado passa por um método com nome de acontecimento, e o
  método confere antes.
- `static` que depende de quem está usando o sistema é variável global
  disfarçada.
- O que é público é promessa; o que é privado é liberdade de mudar depois.
:::

:::checkpoint
Você escolhe visibilidade com argumento, escreve uma classe cujo estado
inválido não tem caminho, usa `readonly` no que não muda, expõe mudanças por
métodos com nome de acontecimento e reconhece um `static` que está guardando
estado de requisição.
:::

:::exercise level=1
A classe `Leitor` tem `nome`, `documento` e `cadastroEm`. Decida a
visibilidade de cada um e justifique em uma frase.

Depois responda: qual dos três você tornaria alterável, e por qual método?

:::answer
```php title="src/Leitores/Leitor.php" numbered
<?php

namespace CasaAmarela\Leitores;

class Leitor
{
    public function __construct(
        private string $nome,
        public readonly string $documento,
        public readonly string $cadastroEm,
    ) {}
}
```

`documento` é `readonly`: o CPF de uma pessoa não muda, e se foi digitado
errado o caso é de correção de cadastro, não de alteração de dado.

`cadastroEm` é `readonly` pelo mesmo motivo, mais forte: é um fato
histórico. Data de um acontecimento que já aconteceu não muda.

`nome` é o único que muda de verdade — casamento, correção de grafia, nome
social. Por isso ele fica privado e ganha uma porta com nome do
acontecimento, `corrigirNome()` ou `renomear()`, não `setNome()`. A porta é
o lugar de recusar nome vazio.
:::

:::exercise level=2
Escreva a classe `Multa` com `centavos` e `diasDeAtraso`, que:

1. recusa nascer com dias negativos;
2. recusa nascer com centavos negativos;
3. expõe `valorFormatado()` devolvendo algo como `R$ 7,20`;
4. expõe `perdoar()`, que zera o valor e não pode ser desfeito.

Depois diga qual invariante a `perdoar()` precisa respeitar.

:::answer
```php title="src/Emprestimos/Multa.php" numbered
<?php

namespace CasaAmarela\Emprestimos;

class Multa
{
    public function __construct(
        private int $centavos,
        public readonly int $diasDeAtraso,
    ) {
        if ($diasDeAtraso < 0) {
            throw new \InvalidArgumentException(
                "Dias de atraso negativos: {$diasDeAtraso}"
            );
        }

        if ($centavos < 0) {
            throw new \InvalidArgumentException(
                "Multa negativa: {$centavos}"
            );
        }
    }

    public function centavos(): int
    {
        return $this->centavos;
    }

    public function valorFormatado(): string
    {
        $reais = $this->centavos / 100;

        return 'R$ ' . number_format($reais, 2, ',', '.');
    }

    public function perdoar(): void
    {
        $this->centavos = 0;
    }
}
```

A invariante que a `perdoar()` precisa respeitar é a mesma do construtor:
**centavos nunca é negativo**. Zerar respeita.

É aqui que mora o erro mais comum de quem começa a validar: escrever as
conferências no construtor e esquecer que todo método que altera o estado
precisa deixar o objeto tão válido quanto o encontrou. Um `descontar(int
$centavos)` escrito sem cuidado leva a multa a menos vinte, e o construtor
não tem como impedir — ele já rodou.

`diasDeAtraso` é `readonly` porque é um fato do empréstimo, e perdoar a
multa não faz o atraso deixar de ter existido. Essa distinção aparece no
relatório da Casa Amarela: a Vera precisa saber quantos atrasos houve,
mesmo os perdoados.
:::

:::exercise level=3
Este código roda e imprime um número errado. Diga qual, por quê, e conserte
sem tirar o contador.

```php title="contador.php" numbered
<?php

class Exemplar
{
    public static int $emprestados = 0;

    public function __construct(
        public readonly int $tombo,
        private string $estado = 'bom',
    ) {}

    public function emprestar(): void
    {
        $this->estado = 'emprestado';
        self::$emprestados++;
    }
}

$a = new Exemplar(2117);
$b = new Exemplar(843);

$a->emprestar();
$a->emprestar();
$b->emprestar();

echo Exemplar::$emprestados, "\n";
```

:::answer
Imprime `3`. O acervo emprestou dois exemplares.

São dois defeitos, e eles se escondem um atrás do outro.

O primeiro é a falta da porta: `emprestar()` não confere o estado, então
chamar duas vezes no mesmo exemplar passa. Com a conferência do capítulo, a
segunda chamada seria recusada e o contador pararia em 2 — por acidente.

O segundo é o contador em si. `public static` significa que qualquer linha
de qualquer arquivo pode somar, subtrair ou zerar, e nada obriga esse número
a ter relação com a realidade. Ele é um total paralelo, que começa correto e
diverge no primeiro caminho que alguém esquecer de contar — exatamente a
coluna `quantidade` do capítulo @cap:o-que-vamos-construir, agora em
memória.

A correção que mantém o contador:

```php
    public function emprestar(): void
    {
        if ($this->estado !== 'bom') {
            throw new \RuntimeException('Exemplar indisponível');
        }

        $this->estado = 'emprestado';
        self::$emprestados++;
    }
```

E a correção que resolve de verdade é não guardar o total: contar as linhas
de `emprestimos` em aberto quando alguém perguntar. Número contado não
diverge da realidade — e um `static` que some em toda requisição nova nem
serve de total, porque ele zera junto com o processo.
:::
