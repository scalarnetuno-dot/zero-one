---
title: "Herança, interfaces e traits"
number: 20
slug: heranca-interfaces-e-traits
part: p4
kicker: "O quadro tinha três caixas quando a Vera chegou. Tinha dez quando ela saiu, e ela não desenhou nenhuma."
goal: >-
  Escolher entre herança, interface, trait e composição com um critério que
  você consegue defender — e reconhecer, antes de desenhar a terceira
  caixa, quando a hierarquia vai explodir.
---

:::story E o infantil didático importado
No quadro havia uma caixa escrita `Livro` e três setas saindo dela:
`LivroInfantil`, `LivroDidatico`, `LivroReferencia`.

— Infantil não sai por catorze dias, sai por sete — explicou Dedé. —
Referência não sai.

Vera estava ali por outro motivo, esperando a Tainá para conferir uma lista,
e olhou o quadro do jeito que se olha uma placa de trânsito nova.

— E o infantil didático?

Dedé desenhou uma quarta caixa.

— E o importado? Importado não sai, seja lá o que for.

A quarta caixa ganhou uma quinta ao lado.

— E o infantil didático importado — disse Vera, sem entonação de pergunta.

Tainá contou as caixas.

— Oito.

— Dez — disse Vera. — Você esqueceu os de referência.
:::

:::art caption="Toda hierarquia de classes cabe no quadro até a bibliotecária chegar."
src="toda-hierarquia-de-classes-cabe-no-quadro-ate-a-bibliotecaria-chegar.png"
Charge editorial minimalista em fundo branco: um quadro branco onde começa
um diagrama limpo — uma caixa "Livro" com três setas para "Infantil",
"Didático" e "Referência" — que, na metade direita, degenera em caixas cada
vez menores e mais apertadas: "InfantilDidático", "InfantilImportado",
"InfantilDidáticoImportado", com setas cruzadas escapando pela borda. O
desenvolvedor, marcador na mão, já está sem espaço e escreve na moldura.
Encostada no batente, uma bibliotecária mais velha, de óculos e braços
cruzados, dita a próxima combinação sem mudar de expressão. Uma estagiária
conta as caixas nos dedos. Poucos elementos, humor seco, estética de
revista de tecnologia.
:::

## `extends` é um parentesco que você não desfaz

Herança é o mecanismo mais antigo dos três e o mais fácil de escrever:

```php title="src/Acervo/LivroInfantil.php" numbered
<?php

namespace CasaAmarela\Acervo;

class LivroInfantil extends Livro
{
    public function prazoEmDias(): int
    {
        return 7;
    }
}
```

`extends` diz: esta classe começa com tudo que a de cima tem — propriedades,
métodos, construtor — e acrescenta ou troca o que quiser.

O problema não aparece na primeira caixa. Aparece na terceira.

Infantil, didático e importado são três características **independentes**:
um livro pode ter qualquer combinação delas. Como cada classe só pode
estender uma outra — o PHP não tem herança múltipla, e `extends` aceita um
nome só —, cobrir todas as combinações exige uma classe por combinação.

| Características | Classes necessárias |
|---|---|
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |

Tabela: Cada característica nova **dobra** o quadro. Foi o que a Vera fez em
quarenta segundos sem saber o que era uma classe.

:::key
Herança serve bem para variação num **eixo só**, quando as opções são
exclusivas: ou é uma, ou é outra, nunca as duas.

Se duas características podem aparecer juntas, elas não são subclasses. São
dados.
:::

## O que uma subclasse promete

Existe uma regra mais importante que a contagem de caixas, e ela é fácil de
enunciar: **onde o pai é aceito, o filho tem que servir**.

Se uma função recebe um `Livro` e o programa passa um `LivroReferencia`, a
função não pode quebrar. Ela não sabe, e não deveria precisar saber, qual
dos dois chegou.

Veja o que acontece quando a regra é quebrada:

```php title="src/Acervo/LivroReferencia.php" numbered
<?php

namespace CasaAmarela\Acervo;

class LivroReferencia extends Livro
{
    public function prazoEmDias(): int
    {
        throw new \RuntimeException('Referência não sai daqui');
    }
}
```

Parece razoável: referência não sai mesmo. Mas agora toda função que recebia
um `Livro` e perguntava o prazo ganhou um jeito novo de morrer — e a única
forma de se proteger é conferir o tipo antes:

```php
if ($livro instanceof LivroReferencia) {
    continue;
}
```

Esse `if` vai aparecer em cinco lugares, e o sexto vai faltar. A herança que
prometia remover condicionais acabou de espalhar uma.

:::pitfall
O teste "**é um**" é o que se ensina primeiro e o que mais erra. Um livro de
referência *é um* livro, na linguagem comum — e mesmo assim não serve como
um.

O teste que funciona é outro: *se eu trocar o pai pelo filho, alguma coisa
que funcionava para de funcionar?* Se a resposta for sim, a herança está
mentindo, e a mentira vai cobrar num `if` que alguém esqueceu.
:::

## Interface: o contrato sem o parentesco

Nem toda coisa que se comporta igual precisa ser parente.

Durante a migração, a Casa Amarela tem dois acervos no ar ao mesmo tempo: o
do Sistema, que continua atendendo o balcão, e o novo. O relatório de
circulação precisa contar exemplares dos dois.

As duas classes não têm nada em comum por dentro — uma lê `tombo` e a outra
lê `cod_exemplar` — e precisam responder às mesmas três perguntas.

```php title="src/Circulacao/Emprestavel.php" numbered
<?php

namespace CasaAmarela\Circulacao;

interface Emprestavel
{
    public function identificacao(): string;

    public function disponivel(): bool;

    public function prazoEmDias(): int;
}
```

Uma interface é uma lista de assinaturas sem nenhum corpo. Ela não diz como
se faz; diz o que precisa existir.

```php title="src/Acervo/Exemplar.php" numbered
<?php

namespace CasaAmarela\Acervo;

use CasaAmarela\Circulacao\Emprestavel;

class Exemplar implements Emprestavel
{
    // ... construtor do capítulo anterior

    public function identificacao(): string
    {
        return "tombo {$this->tombo}";
    }

    public function disponivel(): bool
    {
        return $this->estado === 'bom';
    }

    public function prazoEmDias(): int
    {
        return $this->livro->classificacao->prazoEmDias();
    }
}
```

O PHP cobra o contrato inteiro, na hora de carregar a classe:

```text
Fatal error: Class Exemplar contains 1 abstract method and must
therefore be declared abstract or implement the remaining methods
(Emprestavel::prazoEmDias)
```

E o código que usa não precisa saber de qual acervo veio o item:

```php title="relatorio.php" numbered
<?php

use CasaAmarela\Circulacao\Emprestavel;

function contarDisponiveis(array $itens): int
{
    $total = 0;

    foreach ($itens as $item) {
        if ($item instanceof Emprestavel && $item->disponivel()) {
            $total++;
        }
    }

    return $total;
}
```

:::key
Interface é o mecanismo que o Laravel vai usar para quase tudo, e o motivo é
este: ela deixa você escrever código contra **o que uma coisa faz** em vez
de contra **o que ela é**.

Uma classe pode implementar quantas interfaces quiser. O limite de um só
vale para `extends`.
:::

## Classe abstrata: contrato com parte do como

Uma interface não guarda código. Quando as implementações compartilham um
pedaço de verdade, existe o meio-termo:

```php title="src/Circulacao/ItemDeAcervo.php" numbered
<?php

namespace CasaAmarela\Circulacao;

abstract class ItemDeAcervo implements Emprestavel
{
    abstract public function prazoEmDias(): int;

    public function prazoDescrito(): string
    {
        $dias = $this->prazoEmDias();

        return $dias === 1 ? '1 dia' : "{$dias} dias";
    }
}
```

`abstract class` não pode ser instanciada: `new ItemDeAcervo()` é erro.
`abstract public function` não tem corpo — quem herdar é obrigado a
escrever.

A diferença cabe numa linha: **interface diz o quê; classe abstrata diz o
quê e um pedaço do como**. E a classe abstrata gasta o seu único `extends`,
o que é um preço real.

## Trait: o copiar e colar que o compilador faz

O terceiro mecanismo é o mais literal dos três. Um `trait` é um bloco de
código que é **copiado para dentro** das classes que o usam.

```php title="src/Circulacao/RegistraHistorico.php" numbered
<?php

namespace CasaAmarela\Circulacao;

trait RegistraHistorico
{
    private array $historico = [];

    public function registrar(string $evento): void
    {
        $this->historico[] = date('Y-m-d H:i:s') . ' ' . $evento;
    }

    public function historico(): array
    {
        return $this->historico;
    }
}
```

```php title="src/Acervo/Exemplar.php" numbered
class Exemplar implements Emprestavel
{
    use \CasaAmarela\Circulacao\RegistraHistorico;
```

:::pitfall
Este `use` **não é** o `use` do topo do arquivo.

No topo, fora de qualquer classe, `use` importa um nome — é um apelido e não
carrega nada. Dentro do corpo de uma classe, `use` copia um trait para
dentro dela.

Mesma palavra, dois trabalhos sem relação nenhuma. É a escolha de vocabulário
mais infeliz do PHP moderno, e você vai ler código dos dois tipos no mesmo
arquivo.
:::

Quando dois traits trazem um método com o mesmo nome, o PHP não escolhe por
você:

```text
Fatal error: Trait method RegistraAuditoria::registrar has not been
applied as Exemplar::registrar, because of collision with
RegistraHistorico::registrar
```

A saída é declarar quem ganha, e opcionalmente dar um apelido ao perdedor:

```php
    use RegistraHistorico, RegistraAuditoria {
        RegistraHistorico::registrar insteadof RegistraAuditoria;
        RegistraAuditoria::registrar as registrarAuditoria;
    }
```

Funciona. E é o melhor aviso que o PHP consegue dar de que os dois traits
queriam ser a mesma coisa, ou que a classe está fazendo dois trabalhos.

:::key
O trait do exemplo trouxe uma propriedade junto: `$historico`. Ela passa a
ser uma propriedade da classe, como qualquer outra — e não aparece no corpo
da classe, onde alguém procuraria.

Trait com estado é a forma mais fácil de uma classe ganhar propriedades que
ninguém lembra de ter declarado. Prefira trait sem estado; quando precisar
de estado compartilhado, o mecanismo certo é o da próxima seção.
:::

## Composição: "tem um" em vez de "é um"

O quadro da Vera tinha dez caixas porque três características viraram
tipos. Elas não são tipos. São dados:

```php title="src/Acervo/Classificacao.php" numbered
<?php

namespace CasaAmarela\Acervo;

final class Classificacao
{
    public function __construct(
        public readonly bool $infantil = false,
        public readonly bool $didatico = false,
        public readonly bool $referencia = false,
        public readonly bool $importado = false,
    ) {}

    public function emprestavel(): bool
    {
        return !$this->referencia && !$this->importado;
    }

    public function prazoEmDias(): int
    {
        return $this->infantil ? 7 : 14;
    }
}
```

E o `Livro` **tem uma** classificação:

```php title="src/Acervo/Livro.php" numbered
<?php

namespace CasaAmarela\Acervo;

class Livro
{
    public function __construct(
        public readonly string $titulo,
        public readonly int $ano,
        public readonly Classificacao $classificacao,
    ) {}
}
```

```php
$vidasSecas = new Livro('Vidas Secas', 1938, new Classificacao(
    didatico: true,
));

echo $vidasSecas->classificacao->prazoEmDias(), "\n";
```

```text
14
```

Dez caixas viraram uma classe e quatro campos. E quando o Seu Juvenal
chegar com os livros sonoros — que saem por vinte e um dias, porque a Dona
Marlene demora —, o custo é **uma linha**, não dobrar o quadro.

:::term Composição
Montar um comportamento juntando objetos, em vez de herdando deles. "O livro
tem uma classificação" no lugar de "o livro é um livro infantil".

A troca é sempre a mesma: você escreve uma linha a mais para delegar, e
ganha o direito de mudar de ideia sem mexer na árvore.
:::

Quatro booleanos não são a última palavra em modelagem — no dia em que a
Casa Amarela tiver quinze marcas, isso vira uma lista. O que já está certo
é a direção: crescer somando campo, não somando classe.

## Como escolher

| Você quer | Use |
|---|---|
| que classes sem parentesco respondam às mesmas chamadas | interface |
| contrato mais um pedaço de implementação comum | classe abstrata |
| repetir um bloco de código sem estado em classes diferentes | trait |
| variar comportamento em mais de um eixo | composição |
| variar num eixo só, com opções exclusivas | herança |

Tabela: Na dúvida entre herança e composição, comece por composição. Trocar
composição por herança depois é uma tarde; o caminho inverso é um mês.

:::note Na sua carreira
Numa entrevista, "qual a diferença entre classe abstrata e interface?" é
pergunta de decorar. A versão que separa quem entendeu é a seguinte, e você
pode fazê-la a si mesmo antes de desenhar qualquer hierarquia:

*Se amanhã aparecer uma combinação que eu não previ, eu acrescento um campo
ou eu acrescento uma classe?*

Quem responde "um campo" está compondo. Quem responde "uma classe" está numa
árvore que vai dobrar — e vale dizer isso na reunião **antes** da terceira
caixa, porque depois da oitava a conversa já não é mais técnica, é sobre
prazo.
:::

:::tree title="Onde estamos agora"
acervo/
  src/
    Acervo/
      Livro.php            # tem uma Classificacao
      Classificacao.php    # final, readonly
      Exemplar.php         # implements Emprestavel, use RegistraHistorico
    Circulacao/
      Emprestavel.php      # interface
      RegistraHistorico.php  # trait
    Leitores/
      Leitor.php
    Emprestimos/
      Multa.php
    Legado/
      Livro.php
  relatorio.php
:::

:::summary
- `extends` copia tudo da classe de cima e gasta o único parentesco que a
  classe tem.
- Características independentes dobram a árvore: três viram oito classes.
- A regra da subclasse é servir no lugar do pai; se ela lança onde o pai
  respondia, a herança está mentindo.
- Interface é contrato sem código; uma classe implementa quantas quiser.
- Classe abstrata é contrato com parte da implementação, e custa o
  `extends`.
- Trait é código copiado para dentro da classe; conflito de nome é erro
  fatal, resolvido com `insteadof`.
- O `use` do topo do arquivo importa nome; o `use` dentro da classe copia
  trait.
- Composição troca "é um" por "tem um", e cresce somando campo em vez de
  classe.
:::

:::checkpoint
Você sabe dizer por que o quadro da Vera chegou a dez caixas, declara e
implementa uma interface, reconhece um trait que trouxe estado escondido, e
consegue justificar por escrito — em duas frases — quando herda, quando
compõe e quando declara contrato.
:::

:::exercise level=1
A Casa Amarela empresta, além de livros, três leitores de tela doados por
uma ONG. Eles têm patrimônio em vez de tombo, saem por trinta dias e não
podem ser renovados.

Decida: `LeitorDeTela extends Exemplar`, `LeitorDeTela implements
Emprestavel`, ou nenhuma das duas? Justifique em duas frases.

:::answer
`implements Emprestavel`.

Um leitor de tela não é um exemplar de livro: não tem tombo, não tem
`Livro` dentro, não tem estado de conservação de papel. Herdar de `Exemplar`
traria tudo isso junto e obrigaria a classe a fingir que tem um livro.

O que ele tem em comum com um exemplar é o **comportamento** — identifica-se,
está disponível ou não, tem prazo. É exatamente o que a interface descreve,
e por isso o relatório de circulação consegue contar os dois sem saber a
diferença.
:::

:::exercise level=2
Escreva a `Classificacao` com um quinto caso: livro sonoro, que sai por
vinte e um dias.

A regra da Casa Amarela é: referência e importado não saem; entre os que
saem, vale o prazo mais longo aplicável — sonoro (21) antes de comum (14),
e infantil (7) só quando o livro não for sonoro.

Escreva `prazoEmDias()` e explique por que a ordem das condições importa.

:::answer
```php title="src/Acervo/Classificacao.php" numbered
    public function prazoEmDias(): int
    {
        if ($this->sonoro) {
            return 21;
        }

        if ($this->infantil) {
            return 7;
        }

        return 14;
    }
```

A ordem importa porque as condições **não são exclusivas**: um livro
infantil sonoro satisfaz as duas. Quem escrevesse o `infantil` primeiro
devolveria 7 para ele, contrariando a regra da Vera.

É a mesma armadilha da hierarquia de classes, agora dentro de um método — e
é por isso que ela é preferível aqui: uma regra ambígua num `if` é uma linha
para corrigir, e a mesma ambiguidade numa árvore de classes é uma classe
`LivroInfantilSonoro` para apagar, com tudo que já dependia dela.

Um detalhe que vale escrever num comentário ou num teste: a regra "vale o
prazo mais longo" e a ordem das condições precisam concordar. Se amanhã
alguém acrescentar um caso de 30 dias no fim da fila, ele nunca vai ser
alcançado.
:::

:::exercise level=3
Você recebe este código para revisar. Ele funciona, tem testes passando e
foi escrito por alguém experiente.

```php
abstract class Relatorio
{
    use ConectaBanco;
    use FormataMoeda;
    use EnviaEmail;
    use GeraPdf;

    abstract public function consultar(): array;

    public function executar(): void
    {
        $linhas = $this->consultar();
        $pdf = $this->gerarPdf($linhas);
        $this->enviar($pdf);
    }
}

class RelatorioDeCirculacao extends Relatorio { /* ... */ }
class RelatorioDeMultas extends Relatorio { /* ... */ }
```

Aponte os dois problemas estruturais e proponha a mudança mínima que
melhora sem reescrever tudo.

:::answer
**Primeiro problema: a classe abstrata virou depósito.** Ela faz quatro
coisas sem relação — fala com o banco, formata dinheiro, manda e-mail e gera
PDF — e todo relatório herda as quatro, use ou não. Um relatório que só
imprime na tela carrega o envio de e-mail junto, e ninguém consegue testar a
consulta sem arrastar o resto.

**Segundo problema: os traits escondem dependências.** Olhando
`RelatorioDeCirculacao`, não há nada que diga que ele precisa de uma conexão
de banco e de um servidor de e-mail configurado. Isso está três arquivos
acima, dentro de traits, e só aparece quando quebra.

**A mudança mínima** não é apagar a hierarquia. É tirar os dois traits mais
pesados — `EnviaEmail` e `ConectaBanco` — e passar o que eles fazem como
objetos recebidos no construtor:

```php
abstract class Relatorio
{
    use FormataMoeda;

    public function __construct(
        private readonly Banco $banco,
        private readonly Correio $correio,
    ) {}

    abstract public function consultar(): array;
}
```

O que se ganha é visível na primeira linha: agora a classe **declara** de
que ela depende. O que se perde é a conveniência de não passar nada — e essa
conveniência era o que fazia o teste precisar de um banco de verdade.

`FormataMoeda` pode ficar: é um trait sem estado, sem dependência externa, e
o custo dele é zero. Nem todo trait é problema; o problema é trait que traz
mundo junto.
:::
