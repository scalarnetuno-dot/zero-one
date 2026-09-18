---
title: "Encapsulamento"
number: 10
part: p2
kicker: "Esconder o atributo não é cerimônia: é o que impede o objeto de existir em estado impossível."
goal: >-
  Proteger o estado de um objeto com `private`, expor o que for necessário
  com métodos, e validar no construtor para que o objeto nunca nasça inválido.
---

A classe `Product` do capítulo anterior tem um problema sério:

```java
teclado.preco = -500;
teclado.estoque = -3;
```

Compila, roda e cria um produto com preço negativo. O erro não está na linha
que escreveu o absurdo — está na classe, que permitiu.

## `private`: fechar a porta

```java title="Product.java" numbered
public class Product {
    private String nome;
    private double preco;
    private int estoque;

    public Product(String nome, double preco, int estoque) {
        this.nome = nome;
        this.preco = preco;
        this.estoque = estoque;
    }
}
```

Com `private`, a linha `teclado.preco = -500;` deixa de compilar:
`preco has private access in Product`. O dado passou a ser assunto interno da
classe — e agora a classe pode garantir que ele faça sentido.

## Validar onde o objeto nasce

```java title="Um objeto que se recusa a existir errado" numbered
public Product(String nome, double preco, int estoque) {
    if (nome == null || nome.isBlank()) {
        throw new IllegalArgumentException("nome é obrigatório");
    }
    if (preco < 0) {
        throw new IllegalArgumentException("preço negativo");
    }
    this.nome = nome;
    this.preco = preco;
    this.estoque = Math.max(estoque, 0);
}
```

`throw` interrompe a criação e avisa quem chamou. O capítulo 13 cuida das
exceções em detalhe; aqui basta a ideia: **é mais barato recusar o objeto do
que consertá-lo depois**.

:::key
Se o construtor termina, o objeto é válido. Essa garantia atravessa o
programa inteiro: nenhum método precisa checar se o preço é negativo, porque
não existe produto com preço negativo. Você trocou mil verificações espalhadas
por uma, no lugar certo.
:::

## Getters e setters, com critério

```java title="Ler sempre, escrever quando faz sentido" numbered
public String getNome() {
    return nome;
}

public double getPreco() {
    return preco;
}

public void reajustar(double percentual) {
    if (percentual <= -100) {
        throw new IllegalArgumentException("reajuste inválido");
    }
    this.preco = preco * (1 + percentual / 100);
}
```

Repare no que **não** existe: `setPreco`. Em vez de um método que aceita
qualquer número, a classe expõe a operação real do negócio — reajustar. O
nome carrega a regra.

:::pitfall
Gerar `get` e `set` para todos os atributos por reflexo transforma a classe
em um formulário sem regras — e devolve exatamente o problema que o `private`
resolveu. A pergunta antes de cada `set` é: *alguém de fora tem o direito de
mudar isso sozinho?* Quase sempre a resposta é não.
:::

:::compare left="Setter genérico" right="Operação com nome"
p.setEstoque(
    p.getEstoque() - 1);
---
p.baixarEstoque(1);
:::

A coluna da direita pode recusar a baixa se o estoque for zero. A da esquerda
já gravou o `-1` antes de alguém perguntar.

:::story A Black Friday do estagiário
O campo era público. Estava assim desde o primeiro dia e nunca tinha
incomodado ninguém.

Na véspera da Black Friday, um estagiário recebeu a tarefa mais simples da
lista: aplicar 30% de desconto em uma categoria. Ele escreveu um laço que
percorria os produtos e fazia `p.preco = p.preco * 0.7`.

Funcionou perfeitamente. Rodou três vezes, porque o script travou no meio e
ele reexecutou por precaução.

Às 00h07, a loja vendia monitores por R$ 411,00. Às 00h09, por R$ 287,70. Às
00h11, por R$ 201,39.

Marina desligou o serviço às 00h14 e, na retrospectiva da semana, escreveu no
quadro uma frase que virou regra da equipe:

> "Se um atributo pode ser alterado por qualquer linha do sistema, mais cedo
> ou mais tarde ele será — três vezes seguidas."

O estagiário não errou. O estagiário fez exatamente o que a classe permitia.
:::

:::art caption="`public` não é conveniência: é uma permissão que você concede para sempre."
src="public-nao-e-conveniencia-e-uma-permissao-que-voce-concede-para-sempre.png"
Charge editorial minimalista: etiqueta de preço de loja pendurada em um
monitor, com três valores riscados em sequência e um quarto valor absurdo
escrito embaixo. Ao lado, um estagiário de expressão inocente segurando um
laptop com um script rodando. Atrás, uma desenvolvedora sênior com a mão
sobre uma grande chave geral de energia, prestes a desligá-la. Fundo branco,
poucos elementos, humor seco, composição limpa, estética editorial de
tecnologia.
:::

## Os quatro níveis de acesso

| Modificador | Enxerga |
|---|---|
| `private` | só a própria classe |
| (nenhum) | classes do mesmo pacote |
| `protected` | mesmo pacote + subclasses |
| `public` | todo mundo |

Tabela: Do mais fechado ao mais aberto. A regra prática: comece em `private` e
abra só quando doer.

O nível sem modificador — chamado *package-private* — é o mais esquecido e um
dos mais úteis: ele permite que classes do mesmo pacote conversem sem expor
nada ao resto do mundo.

:::trivia
Java é uma das poucas linguagens em que o nível padrão não é `public` nem
`private`, e sim "do pacote". A decisão vem da ideia de que um pacote é uma
unidade de confiança — classes vizinhas colaboram. Na prática, quase ninguém
usa de propósito: a maioria dos atributos sem modificador está assim por
esquecimento, e é por isso que o capítulo 9 mostrou `Product` daquele jeito.
:::

## Imutabilidade: a versão radical

E se nada puder mudar depois de criado?

```java title="Product imutável" numbered
public class Product {
    private final String nome;
    private final double preco;

    public Product(String nome, double preco) {
        this.nome = nome;
        this.preco = preco;
    }

    public Product comPreco(double novoPreco) {
        return new Product(nome, novoPreco);
    }
}
```

`final` no atributo significa "atribuído uma vez, no construtor, e nunca
mais". Para mudar o preço, você cria outro produto. Parece desperdício e é o
padrão preferido em código moderno: objeto imutável não tem estado
inconsistente, não precisa de cópia defensiva e é seguro entre threads — que é
exatamente a situação de uma API atendendo cem requisições ao mesmo tempo.

:::tip
Essa classe inteira, com validação, `equals`, `hashCode` e `toString`, vira
**uma linha** no capítulo 12. Mas a linha só faz sentido para quem viu as
quinze.
:::

## Onde isso vai aparecer no projeto

A entidade `Product` do capítulo 20 vai precisar de getters — porque o JPA e
o Jackson leem os dados por eles. O que muda é a intenção: getters existem
para as ferramentas e para a leitura; as mudanças de estado continuam
passando por métodos com nome de regra.

:::tree title="Onde estamos agora"
java-one/
  Product.java    # private + construtor que valida
  Category.java
  Loja.java       # main
:::

:::summary
- `private` fecha o atributo; o construtor garante que o objeto nasça válido.
- Getter para ler; operação com nome de regra em vez de setter genérico.
- Quatro níveis de acesso: comece em `private` e abra quando doer.
- `final` nos atributos cria objeto imutável — o padrão preferido em API.
:::

:::checkpoint
Você protege atributos, valida no construtor, escolhe entre setter e operação
com nome, e sabe explicar por que imutabilidade ajuda em um servidor.
:::

:::milestone
`Product` agora se defende: preço negativo e nome vazio não passam do
construtor. Essa validação vai migrar para anotações no capítulo 25, mas a
regra continua a mesma.
:::

:::exercise level=1
Torne todos os atributos de `Category` privados e escreva apenas os getters.
Depois tente alterar `nome` de fora e leia a mensagem do compilador.

:::answer
`nome has private access in Category`. O erro acontece na **compilação**, não
em produção — a troca que este livro defende desde o capítulo 3.
:::

:::exercise level=2
Escreva `baixarEstoque(int quantidade)` em `Product`. Ele deve recusar
quantidade negativa e recusar baixa maior que o estoque disponível.

:::answer
```java
public void baixarEstoque(int quantidade) {
    if (quantidade <= 0) {
        throw new IllegalArgumentException("quantidade inválida");
    }
    if (quantidade > estoque) {
        throw new IllegalStateException("estoque insuficiente");
    }
    this.estoque -= quantidade;
}
```
Dois tipos diferentes de exceção, de propósito: `IllegalArgumentException` é
culpa de quem chamou; `IllegalStateException` é uma situação do objeto. Essa
distinção vai virar, no capítulo 26, a diferença entre um `400` e um `409` na
resposta HTTP.
:::

:::exercise level=3
Reescreva `Product` como classe imutável e ajuste `baixarEstoque` para
devolver um novo produto. Depois liste uma vantagem e uma desvantagem da
versão imutável em uma API.

:::answer
Vantagem: nenhum método consegue deixar o objeto pela metade, e duas threads
podem lê-lo sem trava. Desvantagem: cada alteração cria um objeto, o que em
laços muito grandes gera pressão de memória — e, no caso do JPA (capítulo
20), a ferramenta *precisa* de um objeto mutável para acompanhar mudanças.
Saber onde a imutabilidade não cabe é parte de saber usá-la.
:::
