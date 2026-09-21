# PHP One — roteiro editorial

**Volume 3 da coleção Zero One.** 46 capítulos numerados em 10 partes, mais
a abertura. Segue a mesma filosofia dos volumes anteriores — o livro é dado,
o layout é o sistema — e a mesma régua editorial: ritmo variado (nem todo
capítulo tem cena, ilustração ou marco), capítulos densos em código real, e
**referência cruzada sempre por `@cap:<slug>`**, nunca "no capítulo 31"
digitado à mão.

---

## O projeto contínuo

**Biblioteca Comunitária Casa Amarela.** Um acervo de bairro com quatro mil
livros, oito mil exemplares e um sistema em PHP 5.4 escrito em 2009 por um
sobrinho que hoje mora em outro estado.

O domínio foi escolhido por permitir, sem inventar complexidade:

| Precisa de | O domínio entrega |
|---|---|
| CRUD | livros, exemplares, leitores |
| relacionamentos | livro → exemplares → empréstimos; livro ↔ autores (N:N) |
| regra de negócio | não emprestar exemplar indisponível; prazo; renovação; multa |
| autorização | leitor vê só os próprios empréstimos; bibliotecária vê tudo |
| filtros e paginação | acervo com busca por título, autor, assunto |
| filas | lembrete de devolução, aviso de reserva disponível |
| eventos | `EmprestimoRealizado`, `ExemplarDevolvido` |
| cache | os mais emprestados do mês |
| camada web | o painel da bibliotecária, em Blade |
| API | o aplicativo do leitor, consumido por terceiros |

O que o projeto **não** é: um ERP. Não há financeiro, não há estoque, não há
multiempresa. Uma biblioteca de bairro tem o tamanho certo para caber num
livro e ainda ter regras que discordam entre si.

### Entidades ao fim do livro

`Livro` · `Autor` · `Exemplar` · `Leitor` · `Usuario` · `Emprestimo` ·
`Reserva` · `Multa`

A distinção **livro × exemplar** é deliberada e aparece cedo: é o menor
exemplo honesto de modelagem que existe. "Temos *O Cortiço*" e "temos três
*O Cortiço*" são frases diferentes, e o sistema de 2009 confundia as duas.

---

## A história satélite

Camada narrativa secundária, em blocos `:::story` de no máximo 260 palavras,
presente em pouco mais da metade dos capítulos — nunca em todos, para não
virar fórmula.

**O elenco:**

- **Vera** — bibliotecária há 31 anos. Conhece todas as regras de empréstimo
  de cor e nunca escreveu nenhuma. Irônica, econômica nas palavras, e a
  pessoa que faz a pergunta que derruba o desenho.
- **Dedé** — o desenvolvedor que herdou "o Sistema". Já trabalhou com
  software o bastante para reconhecer os buracos, e é a voz que explica o
  porquê.
- **Tainá** — estagiária. Aprende junto com o leitor e faz as perguntas que
  o leitor faria.
- **Seu Juvenal** — presidente da associação de moradores. Quer tudo para
  ontem, pergunta "mas isso não é só um CRUD?" no capítulo 31, e é o
  personagem que traz o requisito novo no pior momento possível.

**O Sistema** (com maiúscula) é o quinto personagem: 14 mil linhas de PHP
5.4, `mysql_query` com concatenação de string, `include` de 40 arquivos,
senha em MD5 sem sal, e um arquivo chamado `funcoes2_NOVO_final.php`. Ele
não é vilão — ele funcionou por quinze anos. É o contraponto que dá sentido
a cada recurso moderno que o livro apresenta.

**O arco:** a equipe não reescreve tudo de uma vez. O Sistema continua no ar
durante o livro inteiro, e cada parte nova conversa com ele — o que produz o
humor e também a honestidade técnica.

---

# Parte 1 — PHP do zero

> A linguagem antes de qualquer framework.

---

## 1. O que vamos construir

**Objetivo.** Dar o destino antes da primeira linha: o que é uma API, o que
é um CRUD, por que a Casa Amarela precisa de um sistema novo — e deixar o
ambiente instalado e testado.

**O leitor aprende.** O vocabulário mínimo (recurso, verbo, status), a
diferença entre livro e exemplar, e o que PHP é hoje em contraste com a
reputação que ele carrega.

**Subcapítulos**
1. Uma biblioteca de bairro e um sistema de 2009
2. O que é uma API, e por que a Casa Amarela precisa de uma
3. Empréstimo é um verbo, não uma tabela
4. O PHP que você ouviu falar e o PHP de hoje
5. O que instalar: PHP 8.3, Composer e um editor
6. O mapa: da linguagem à produção

**Conceitos.** API, REST em uma frase, CRUD, cliente e servidor, versões do
PHP e ciclo de suporte.

**Projeto.** Nenhum código ainda: o documento de requisitos da Casa Amarela,
que vai ser consultado até o último capítulo.

**Erros comuns.** Confundir PHP com Laravel; instalar PHP pelo pacote errado
do sistema e ficar com 7.4; achar que "livro" e "exemplar" são a mesma
coisa.

**História.** A primeira reunião. Seu Juvenal pergunta quanto tempo leva.
Vera responde que o Sistema "funciona", e Dedé pergunta o que acontece
quando dois atendentes emprestam o mesmo exemplar ao mesmo tempo. Silêncio.

**Pré-requisitos.** Nenhum.

**Ao terminar.** Explicar o projeto para outra pessoa e rodar `php -v` com a
versão certa.

---

## 2. O primeiro programa

**Objetivo.** Escrever, salvar e rodar PHP; entender o que acontece entre o
`Enter` e a saída; e ler as três mensagens de erro que todo iniciante vê.

**O leitor aprende.** Tag de abertura, saída, servidor embutido, e o hábito
de ler o erro inteiro em vez de olhar só a primeira linha.

**Subcapítulos**
1. `php -v`, e o dia em que existem três PHP na mesma máquina
2. `<?php` e a tag que você não vai fechar
3. `echo`, `print` e a saída que ninguém formata
4. `php -S`: um servidor sem instalar Apache
5. Erro de sintaxe: a linha apontada e a linha anterior
6. Onde o PHP guarda as mensagens que você não viu

**Conceitos.** Interpretador, SAPI (CLI × servidor), `php.ini`,
`display_errors` × `error_log`, encerramento de arquivo sem `?>`.

**Projeto.** `ola.php` e uma página que imprime o nome da biblioteca.

**Erros comuns.** `?>` no fim do arquivo seguido de espaço em branco (e a
saída que quebra cabeçalhos meses depois); erro silencioso porque
`display_errors` está desligado; editar um arquivo e rodar outro.

**História.** Tainá edita o arquivo certo, salva, recarrega e não muda nada.
São dois servidores rodando, em portas diferentes, desde a terça.

**Pré-requisitos.** Cap. 1.

**Ao terminar.** Rodar um arquivo PHP pelo terminal e pelo navegador, e
reconhecer um `ParseError` pela forma.

---

## 3. Variáveis e tipos

**Objetivo.** Usar os tipos básicos com consciência e entender a conversão
automática que o PHP faz sem pedir licença.

**O leitor aprende.** Os tipos, `null` como afirmação de ausência, type
juggling, e por que dinheiro não é `float`.

**Subcapítulos**
1. `$` na frente, e por que isso ainda ajuda
2. Os oito tipos que o PHP conhece
3. `null` não é vazio, e vazio não é zero
4. Type juggling: a conversão que ninguém pediu
5. `var_dump` é o seu melhor amigo
6. Dinheiro não é float — e a multa da biblioteca prova

**Conceitos.** `int`, `float`, `string`, `bool`, `array`, `null`, `object`;
`gettype`, `var_dump`, `is_*`; `isset` × `empty` × `is_null`; ponto
flutuante binário.

**Projeto.** Os primeiros dados do acervo em variáveis soltas — de
propósito, para doer no capítulo 8.

**Erros comuns.** `if ($multa)` quando a multa é zero; `"0"` como valor
falso; comparar `float` com `==`; usar `empty` para checar existência.

**História.** A multa de R$ 0,00 que aparece no relatório como "pendente"
porque zero é falso.

**Pré-requisitos.** Cap. 2.

**Ao terminar.** Declarar e inspecionar variáveis; explicar por que a multa
é inteiro em centavos e não `float`.

---

## 4. Operadores

**Objetivo.** Calcular, comparar e combinar sem surpresa — com atenção aos
três pontos em que o PHP se comporta diferente do esperado.

**O leitor aprende.** `==` × `===`, `<=>`, `??`, `?->`, concatenação e
precedência.

**Subcapítulos**
1. `==` não é `===`, e a diferença já custou dinheiro
2. `<=>`: comparar devolvendo −1, 0 ou 1
3. `??` e `?->`: a ausência tratada sem escada
4. Concatenação com `.`, e por que não com `+`
5. Precedência: onde o parêntese é grátis
6. Atribuição composta e os atalhos que valem a pena

**Conceitos.** Comparação frouxa e estrita, *spaceship*, coalescência nula,
operador nullsafe, `.` × `+`, `**`, `%`, `intdiv`.

**Projeto.** Cálculo de dias de atraso e de multa por dia.

**Erros comuns.** `==` entre string e número em código de autenticação;
`$a + $b` com strings; ternário aninhado sem parênteses.

**História.** Dedé mostra no Sistema o `if ($senha == $hash)` que aceitava
qualquer senha para um hash que começava com `0e`.

**Pré-requisitos.** Cap. 3.

**Ao terminar.** Escolher entre `==` e `===` com critério e justificar em
uma frase.

---

## 5. Condicionais

**Objetivo.** Escrever decisões legíveis e reconhecer o caminho implícito de
todo `if` sem `else`.

**O leitor aprende.** `if`/`elseif`/`else`, `match`, cláusula de guarda e a
lista fechada de valores falsos.

**Subcapítulos**
1. `if` sem chaves é uma promessa que alguém vai quebrar
2. A escada de `elseif` e o conceito que está faltando
3. `match` não é `switch` — e não escorrega
4. Cláusula de guarda: tratar o caso ruim e sair
5. Ternário aninhado: o código que ninguém lê em voz alta
6. Truthiness: a lista fechada do que é falso em PHP

**Conceitos.** `match` com comparação estrita e `UnhandledMatchError`;
`switch` e *fall-through*; early return; conversão para booleano.

**Projeto.** A regra "pode emprestar?" na primeira versão, ainda ingênua.

**Erros comuns.** `switch` sem `break`; escada de seis degraus que pede um
enum; `if` aninhado três níveis.

**História.** A regra de empréstimo que Vera recita de cor em quarenta
segundos e que ninguém nunca escreveu. Tainá anota: são onze condições.

**Pré-requisitos.** Cap. 4.

**Ao terminar.** Escrever a decisão com guardas e escolher entre `if` e
`match` por intenção.

---

## 6. Repetições

**Objetivo.** Percorrer coleções e repetir sob condição, e enxergar onde o
N+1 nasce.

**O leitor aprende.** `foreach` como laço padrão, `break`/`continue`, o
acumulador, e as funções de array que substituem laço.

**Subcapítulos**
1. `foreach` é o laço; o resto é exceção
2. `for`, `while` e o laço que nunca termina
3. `break`, `continue` e o rótulo que quase ninguém deveria usar
4. Consulta dentro de laço: o N+1 nasce aqui
5. O acumulador: somar, contar e filtrar são o mesmo esqueleto
6. Quando o laço vira expressão

**Conceitos.** `foreach` por valor × por referência, `array_map`,
`array_filter`, `array_reduce`, `array_sum`.

**Projeto.** Relatório de empréstimos do mês, ainda sobre arrays na memória.

**Erros comuns.** `foreach ($x as &$item)` e a última posição contaminada;
modificar o array percorrido; `while` sem condição de saída.

**História.** O relatório que demorava quatro minutos porque consultava o
banco dentro do laço — 3.200 vezes.

**Pré-requisitos.** Cap. 5.

**Ao terminar.** Escrever laços idiomáticos e reconhecer a forma do N+1
antes de ter ORM.

---

## 7. Funções

**Objetivo.** Dar nome a um pedaço de trabalho e entender escopo, retorno e
funções de primeira classe.

**O leitor aprende.** Parâmetros, padrão, argumentos nomeados, escopo,
closures, arrow functions e callables.

**Subcapítulos**
1. Uma regra que mora em dez lugares muda em nove
2. Parâmetros, valor padrão e argumentos nomeados
3. Retorno: um tipo só, e o que fazer com o nada
4. Escopo: por que sua variável global não está lá dentro
5. Closures, `use` e arrow functions
6. Callables: passar comportamento como argumento
7. Função pura e a testabilidade que vem de graça

**Conceitos.** `function`, valores padrão, *named arguments*, `global` e por
que evitá-lo, `static` em função, `fn() =>`, `use ($x)` × `use (&$x)`,
`callable`, `array_map` com closure.

**Projeto.** `calcularMulta()` e `podeEmprestar()` extraídas para funções.

**Erros comuns.** Depender de `global`; função que faz duas coisas; closure
capturando por valor quando se esperava referência.

**História.** —

**Pré-requisitos.** Cap. 6.

**Ao terminar.** Extrair regra para função, escolher entre closure e método,
e explicar por que `global` é um sintoma.

---

## 8. Arrays

**Objetivo.** Entender a estrutura mais usada e mais mal usada do PHP.

**O leitor aprende.** Lista × mapa, cópia por valor, as funções que resolvem
quase tudo, e o momento em que o array pede uma classe.

**Subcapítulos**
1. Um array PHP é duas coisas ao mesmo tempo
2. Lista e mapa: o mesmo tipo, dois usos
3. Array não é banco de dados
4. As funções que resolvem 90%
5. Cópia por valor: o array que não é o mesmo array
6. Array aninhado de quatro níveis: hora de criar uma classe
7. Desempacotamento, spread e `list()`

**Conceitos.** *ordered hash map*, `array_column`, `array_key_exists` ×
`isset`, `usort`, `array_values`, `array_unique`, semântica de cópia,
`[$a, $b] = $par`, `...$itens`.

**Projeto.** O acervo como array de arrays — e a lista de tudo que está
errado nisso, que os capítulos 12 e 29 resolvem.

**Erros comuns.** `isset` em chave com valor `null`; ordenar com `sort` e
perder as chaves; array como objeto sem contrato.

**História.** O `$dados['livro']['exemplar'][3]['emprestimo']['leitor']` que
ninguém consegue depurar.

**Pré-requisitos.** Cap. 7.

**Ao terminar.** Escolher a função certa em vez de escrever laço, e
reconhecer quando o array virou um objeto disfarçado.

---

## 9. Strings

**Objetivo.** Trabalhar com texto sem cair nas armadilhas de codificação e
de montagem de comando.

**O leitor aprende.** Aspas, interpolação, heredoc, UTF-8 e formatação.

**Subcapítulos**
1. Aspas simples e duplas não fazem a mesma coisa
2. Interpolação, heredoc e o SQL que você **não** vai montar assim
3. `strlen` mente em português: bytes contra caracteres
4. UTF-8: o acento que vira losango
5. Buscar, trocar e comparar: as funções de sempre
6. `sprintf` e o formato que o recibo exige
7. Tudo que entra é texto até você provar o contrário

**Conceitos.** `'` × `"`, heredoc e nowdoc, `mb_*`, `strlen` × `mb_strlen`,
`str_contains`, `str_starts_with`, `trim`, `sprintf`, `number_format`,
`htmlspecialchars` (primeira aparição de escapar saída).

**Projeto.** Normalização de título e autor na entrada; formatação de multa
em reais.

**Erros comuns.** Concatenar SQL (primeira menção a injeção, retomada no
cap. 27); `strtoupper` em texto acentuado; comparar título sem normalizar.

**História.** A busca por "Machado de Assis" que não encontrava "MACHADO DE
ASSIS" — nem "Machado  de Assis", com dois espaços.

**Pré-requisitos.** Cap. 8.

**Ao terminar.** Manipular texto com as funções `mb_*`, formatar valores e
explicar por que nunca se monta SQL por concatenação.

---

# Parte 2 — Do script ao projeto

> O momento em que um arquivo vira trinta.

---

## 10. Do `include` ao Composer

**Objetivo.** Sair do copiar e colar entre arquivos e entrar no
gerenciamento de dependências.

**O leitor aprende.** `include`/`require`, o problema que eles não resolvem,
e o que o Composer é de fato.

**Subcapítulos**
1. Um arquivo vira dois, e dois viram trinta
2. `include`, `require` e o `require_once` que mascara o problema
3. O Composer não é só um instalador
4. `composer.json`, `composer.lock` e a diferença que importa
5. Versões semânticas e o `^` que você aceitou sem ler
6. `require` contra `require-dev`
7. A pasta `vendor` que você não versiona

**Conceitos.** Resolução de dependência, *lock file*, `^` × `~` × versão
fixa, PSR-4 em `composer.json`, `composer install` × `composer update`.

**Projeto.** `composer init` no projeto da Casa Amarela e a primeira
dependência de verdade (`ramsey/uuid` ou `nesbot/carbon`).

**Erros comuns.** Versionar `vendor/`; não versionar `composer.lock`; rodar
`composer update` em produção; `require_once` para resolver ordem de
carregamento.

**História.** O Sistema tem `funcoes.php`, `funcoes2.php` e
`funcoes2_NOVO_final.php`. Os três são incluídos. Dois definem a mesma
função com corpos diferentes.

**Pré-requisitos.** Cap. 9.

**Ao terminar.** Criar um projeto com Composer e explicar a diferença entre
`install` e `update` para alguém do time.

---

## 11. Namespaces e autoload

**Objetivo.** Organizar o código por endereço e nunca mais escrever
`require` de classe.

**O leitor aprende.** Namespace, `use`, PSR-4 e como o autoload encontra uma
classe.

**Subcapítulos**
1. Duas classes com o mesmo nome, e o dia em que elas se encontram
2. Namespace é endereço, não pasta — mas finja que é
3. `use`, apelidos e o `\` que muda tudo
4. PSR-4: a convenção que faz tudo funcionar
5. Autoload: quem encontrou essa classe?
6. `composer dump-autoload` e o que ele realmente faz
7. A estrutura de pastas que o resto do livro assume

**Conceitos.** `namespace`, FQCN, `use ... as`, resolução relativa ×
absoluta, `spl_autoload_register`, mapa de classes, `--optimize`.

**Projeto.** `src/` com `Acervo\`, `Emprestimo\`, e o `autoload` declarado.

**Erros comuns.** Nome de arquivo com caixa diferente do nome da classe (e o
deploy que quebra só no Linux); esquecer `use` e receber "class not found"
com o nome certo na mensagem.

**História.** Funciona no Windows da Tainá e quebra no servidor. `Livro.php`
× `livro.php`.

**Pré-requisitos.** Cap. 10.

**Ao terminar.** Criar uma classe nova que é encontrada sem nenhum
`require`.

---

## 12. Classes e objetos

**Objetivo.** Trocar o array associativo por um tipo com nome quando o
formato é conhecido.

**O leitor aprende.** Classe, objeto, construtor moderno, propriedades
tipadas e comparação.

**Subcapítulos**
1. Array associativo aceita qualquer chave; um objeto não
2. `class`, `new` e o `$this` sem mistério
3. Constructor property promotion: o construtor em uma linha
4. Propriedades tipadas e o estado que nasce válido
5. `__toString`, `__get` e os métodos mágicos que custam caro
6. Comparar objetos: `==` e `===` em duas linhas
7. Quando o objeto não vale a pena

**Conceitos.** Instância, `$this`, `static::` × `self::`, promoção de
propriedade, propriedade tipada e *uninitialized*, `__construct`,
`__toString`, clonagem rasa.

**Projeto.** `Livro`, `Exemplar` e `Leitor` como classes — a modelagem que o
capítulo 1 prometeu.

**Erros comuns.** Classe que é só `get`/`set`; método mágico como
substituto de desenho; comparar objetos com `==` sem saber o que isso faz.

**História.** Vera olha a tela e pergunta por que o sistema deixa cadastrar
um exemplar sem livro. Porque era um array.

**Pré-requisitos.** Cap. 11.

**Ao terminar.** Substituir um array de formato conhecido por uma classe e
justificar a troca.

---

## 13. Encapsulamento

**Objetivo.** Proteger a coerência do objeto e projetar a superfície
pública.

**O leitor aprende.** Visibilidade, invariante, `readonly` e o custo de
tornar algo público.

**Subcapítulos**
1. `public` não é conveniência: é uma permissão para sempre
2. `private`, `protected` e a placa que o PHP de fato fiscaliza
3. Getter e setter não são obrigatórios
4. Invariante: o que nunca pode deixar de ser verdade
5. `readonly`: o objeto que recusa mudar de ideia
6. `static`: ferramenta ou variável global disfarçada
7. A superfície pública é uma promessa

**Conceitos.** `public`/`protected`/`private`, `readonly`, propriedade
estática, `final`, invariante de classe, construtor que valida.

**Projeto.** `Exemplar` com estado (`disponivel`, `emprestado`, `perdido`)
que só muda por `emprestar()` e `devolver()`.

**Erros comuns.** Tudo público "porque é mais rápido"; validar no construtor
e esquecer os métodos; `static` guardando estado de requisição.

**História.** O relatório com três exemplares emprestados duas vezes —
porque havia seis lugares no Sistema que escreviam na coluna `status`.

**Pré-requisitos.** Cap. 12.

**Ao terminar.** Escrever uma classe cujo estado inválido é impossível de
alcançar por fora.

---

# Parte 3 — O PHP que o Laravel exige

> Nenhum recurso aparece por ser novo.

---

## 14. Herança, interfaces e traits

**Objetivo.** Escolher entre os três mecanismos de reúso do PHP com
critério.

**O leitor aprende.** `extends`, contrato por interface, `trait`, e por que
composição costuma ganhar.

**Subcapítulos**
1. `extends` é um parentesco que você não desfaz
2. Sobrescrever sem quebrar a promessa da classe de cima
3. Interface: o contrato que o Laravel vai pedir o tempo todo
4. Trait: o copiar e colar que o compilador faz por você
5. Conflito de trait e o `insteadof` que denuncia o desenho
6. Composição: "tem um" em vez de "é um"
7. Classe abstrata, interface ou nenhuma das duas

**Conceitos.** `abstract`, `interface`, `implements`, `trait`, `use` em
classe, `insteadof`/`as`, substituição de Liskov em linguagem simples,
herança múltipla que o PHP não tem.

**Projeto.** `Emprestavel` como interface; `RegistraHistorico` como trait;
a decisão explícita de **não** criar `LivroInfantil extends Livro`.

**Erros comuns.** Hierarquia de quatro níveis; trait com estado
compartilhado; herança para reaproveitar três métodos.

**História.** A proposta de `LivroInfantil`, `LivroDidatico`,
`LivroInfantilDidatico` — e a pergunta de Vera sobre o infantil didático
importado.

**Pré-requisitos.** Cap. 13.

**Ao terminar.** Justificar por escrito quando herda, quando compõe e quando
declara interface.

---

## 15. Exceções

**Objetivo.** Tratar falhas sem apagar a informação, e criar o vocabulário
de erro do domínio.

**O leitor aprende.** Hierarquia de `Throwable`, captura específica,
exceções próprias e encadeamento.

**Subcapítulos**
1. Erro, exceção e o `Throwable` que cobre os dois
2. `catch (Exception $e) {}` apaga a testemunha
3. Capturar o tipo, não o mundo
4. Exceções do domínio: `ExemplarIndisponivel`, não `RuntimeException`
5. `previous`: não perder a causa no caminho
6. `finally` e o recurso que precisa ser devolvido
7. Quando **não** capturar

**Conceitos.** `Throwable`, `Error` × `Exception`, hierarquia SPL,
`try`/`catch`/`finally`, exceção com dados anexados, `getPrevious`,
`set_exception_handler`.

**Projeto.** `ExemplarIndisponivel`, `LimiteDeEmprestimosAtingido`,
`LeitorComPendencia` — as três que viram status HTTP no capítulo 35.

**Erros comuns.** `catch (\Throwable $e) { return false; }`; exceção para
controle de fluxo previsível; mensagem de erro como única informação.

**História.** A importação noturna que "nunca dava erro" e perdia 214 linhas
por noite, porque alguém escreveu `catch { continue; }`.

**Pré-requisitos.** Cap. 14.

**Ao terminar.** Criar uma família de exceções de domínio com dados
anexados.

---

## 16. Tipagem estrita

**Objetivo.** Transformar anotação em conferência, antes de rodar e em
execução.

**O leitor aprende.** `strict_types`, tipos de parâmetro e retorno, union e
nullable, e análise estática.

**Subcapítulos**
1. `declare(strict_types=1)` e a linha que muda o arquivo inteiro
2. Union, nullable e o `mixed` que é uma desistência
3. Tipos de retorno: `void`, `never`, `static`
4. O que o PHP confere em execução — e o que não confere
5. PHPStan: o erro que aparece antes de rodar
6. Tipar código legado sem parar a empresa

**Conceitos.** Modo coercitivo × estrito, `?Tipo` e `Tipo|null`, `never`,
`static` como retorno, covariância de retorno, níveis do PHPStan, baseline.

**Projeto.** `strict_types` em todo arquivo novo; PHPStan nível 5 no `src/`.

**Erros comuns.** `strict_types` no arquivo que chama, achando que vale para
o que é chamado; `mixed` por comodidade; `?int` para evitar decidir.

**História.** O PHPStan encontra, no primeiro dia, 41 lugares em que o
Sistema soma uma data com uma string.

**Pré-requisitos.** Cap. 15.

**Ao terminar.** Declarar tipos com precisão e rodar análise estática na
própria máquina.

---

## 17. Enums, datas e objetos de valor

**Objetivo.** Fechar conjuntos de opções e representar valores com regra
própria.

**O leitor aprende.** `enum` puro e *backed*, comportamento dentro do enum,
datas imutáveis com fuso e objeto de valor para dinheiro.

**Subcapítulos**
1. String solta é um `if` esperando erro de digitação
2. `enum` puro e *backed enum*: o valor que vai ao banco
3. Métodos dentro do enum: comportamento junto da opção
4. Data sem fuso é informação incompleta
5. `DateTimeImmutable` e por que a versão mutável dá problema
6. Um objeto de valor para dinheiro, de uma vez por todas

**Conceitos.** `enum`, `enum: string`, `cases()`, `from`/`tryFrom`,
`interface` implementada por enum, `DateTimeImmutable`, `DateInterval`,
`DateTimeZone`, valor em centavos, `readonly` aplicado.

**Projeto.** `StatusExemplar`, `StatusEmprestimo`, `Dinheiro` e
`PrazoDeEmprestimo` — os tipos que atravessam o livro inteiro.

**Erros comuns.** `DateTime` mutável passado adiante e modificado por quem
recebeu; `from()` onde o certo é `tryFrom()`; guardar o **nome** do enum no
banco em vez do valor.

**História.** A devolução registrada às 23h de terça que aparece como
quarta-feira no relatório — e a multa de um dia que ninguém devia.

**Pré-requisitos.** Cap. 16.

**Ao terminar.** Substituir strings soltas por enums e explicar por que a
data do sistema é imutável e em UTC.

# Parte 4 — A web por baixo do framework

> Depois deste trecho, nenhuma parte do Laravel parece mágica.

---

## 18. O que é HTTP

**Objetivo.** Entender que requisição e resposta são texto, e ver o que o
PHP enxerga disso.

**O leitor aprende.** Anatomia da requisição, status, cabeçalhos,
superglobais e o conceito de *stateless*.

**Subcapítulos**
1. Uma requisição é texto; uma resposta também
2. Verbo, caminho, cabeçalho, corpo
3. Status: as cinco famílias e as sete que você vai usar
4. O que o PHP vê: `$_GET`, `$_POST`, `$_SERVER` — e por que você vai parar
   de usá-los
5. Cabeçalhos que decidem comportamento: `Content-Type`, `Accept`,
   `Authorization`
6. Stateless: o servidor que não lembra de você
7. Ler uma requisição inteira com `curl -v`

**Conceitos.** Método, URI, versão, cabeçalho, corpo; `2xx`–`5xx`;
superglobais; `php://input` e por que `$_POST` está vazio com JSON; cookie e
sessão em uma frase; `header()`.

**Projeto.** Um endpoint cru que recebe JSON e devolve JSON, sem framework.

**Erros comuns.** Esperar `$_POST` preenchido num `POST` com
`application/json`; verbo no caminho; `200` para tudo.

**História.** Tainá jura que o aplicativo não envia os dados. `curl -v`
mostra que envia — e que o Sistema lê `$_POST`.

**Pré-requisitos.** Cap. 17.

**Ao terminar.** Ler uma requisição e uma resposta inteiras e explicar cada
parte.

---

## 19. O que é uma API REST

**Objetivo.** Estabelecer o contrato que a API do livro vai cumprir até o
fim.

**O leitor aprende.** Recurso, verbo, idempotência, status e o que quebra um
cliente.

**Subcapítulos**
1. Recurso é substantivo; o verbo já existe no HTTP
2. `/emprestimos`, e não `/criarEmprestimo`
3. Idempotência: por que `PUT` pode ser repetido e `POST` não
4. O status certo diz metade da resposta
5. REST não é lei, é estilo — e o que fazer quando não cabe
6. O contrato: o que quebra um cliente que você não controla

**Conceitos.** Recurso e coleção, verbos seguros e idempotentes, `201` +
`Location`, `409`, `422`, subrecurso (`/livros/12/exemplares`), ações que
não são CRUD (`POST /emprestimos/7/renovacao`).

**Projeto.** O desenho completo dos endpoints da Casa Amarela, escrito antes
da primeira rota.

**Erros comuns.** `GET` que altera estado; `/produtos/baratos` como caminho;
`200` com corpo de erro dentro.

**História.** Seu Juvenal quer um botão "renovar tudo". Dedé explica por que
isso não é `PUT /emprestimos` — e por que também não é `GET`.

**Pré-requisitos.** Cap. 18.

**Ao terminar.** Desenhar os endpoints de um domínio novo e defender cada
escolha.

---

## 20. Um framework de quarenta linhas

**Objetivo.** Construir à mão o mínimo de um framework, para que o Laravel
deixe de ser mágica.

**O leitor aprende.** Front controller, roteador, contêiner ingênuo e
middleware — antes de qualquer um desses nomes virar configuração.

**Subcapítulos**
1. O problema: um arquivo `.php` por página
2. Front controller: tudo entra por `index.php`
3. Um roteador em vinte linhas
4. Um contêiner ingênuo, e por que ele já ajuda
5. Middleware: a cebola antes de ter nome
6. O que ainda falta — e é exatamente o que o Laravel traz
7. O que você acabou de entender sobre todo framework PHP

**Conceitos.** Front controller, reescrita de URL, tabela de rotas,
*dispatch*, resolução de dependência por reflexão, *pipeline* de middleware,
separação entre framework e aplicação.

**Projeto.** `mini/` — o micro-framework que atende três rotas da
biblioteca. É descartado no capítulo 22 e citado até o fim do livro.

**Erros comuns.** Confundir roteador com `switch` gigante; achar que
framework é biblioteca; supor que o Laravel faz algo fundamentalmente
diferente disso.

**História.** Dedé escreve o roteador em vinte minutos. Tainá pergunta por
que não usar isso e pronto. A resposta ocupa o capítulo seguinte.

**Pré-requisitos.** Cap. 19.

**Ao terminar.** Explicar o ciclo de uma requisição em qualquer framework
PHP, apontando onde cada peça entra.

---

## 21. O que é o Laravel

**Objetivo.** Situar o framework: do que ele é feito, o que decide por você
e quando não é a escolha certa.

**O leitor aprende.** As peças internas, o ciclo de requisição, e o custo da
convenção.

**Subcapítulos**
1. Framework é código que chama o seu
2. As peças: Symfony HTTP, Illuminate, Eloquent, Blade
3. O ciclo de uma requisição, do `index.php` à resposta
4. Convenção sobre configuração: o que isso custa
5. Laravel, Symfony ou nenhum dos dois
6. O que o framework decide por você — e como discordar

**Conceitos.** Kernel HTTP, service providers, bootstrap, *facades* em uma
frase, ecossistema (Sanctum, Horizon, Telescope) sem virar catálogo.

**Projeto.** Nenhum código: o mapa das camadas que o livro vai preencher.

**Erros comuns.** Achar que Laravel é PHP; escolher framework por
popularidade sem nomear o atrito; recusar convenção e reescrever o que já
vinha pronto.

**História.** —

**Pré-requisitos.** Cap. 20.

**Ao terminar.** Descrever o ciclo de uma requisição Laravel e apontar, em
cada etapa, o equivalente no micro-framework do capítulo anterior.

---

# Parte 5 — Dentro do Laravel

---

## 22. O primeiro projeto

**Objetivo.** Ter o Laravel rodando, entender o que veio dentro e fazer a
primeira rota responder.

**O leitor aprende.** Criação do projeto, estrutura de pastas, `.env` e as
opções de ambiente local.

**Subcapítulos**
1. `composer create-project` e o que veio dentro
2. A rota que responde em dois minutos
3. `artisan serve`, Sail, Valet ou Docker: escolha uma
4. O primeiro erro de permissão em `storage/`
5. `.env`, `.env.example` e a chave que nunca entra no Git
6. Um passeio pelas pastas que importam

**Conceitos.** Esqueleto da aplicação, `public/index.php` como front
controller (retomada do cap. 20), `APP_KEY`, permissões de `storage/` e
`bootstrap/cache/`.

**Projeto.** `casa-amarela/` criado, rodando, com `GET /saude`.

**Erros comuns.** Versionar `.env`; rodar sem `APP_KEY`; usar Docker no
primeiro dia "porque é profissional" e travar duas horas.

**História.** Seu Juvenal vê a página de boas-vindas do Laravel e pergunta
se o sistema já está pronto.

**Pré-requisitos.** Cap. 21.

**Ao terminar.** Criar um projeto Laravel e explicar o papel de cada pasta
de topo.

---

## 23. Configuração, ambiente e Artisan

**Objetivo.** Configurar sem espalhar `env()` pelo código e usar o Artisan
como modelo mental, não como lista de comandos.

**O leitor aprende.** `config()` × `env()`, cache de configuração,
ambientes, `tinker` e comandos próprios.

**Subcapítulos**
1. `config()` e `env()`: a diferença que derruba produção
2. `config:cache` e o dia em que a variável sumiu
3. Ambientes: local, teste, produção
4. Artisan é um `make`, um inspetor e um controle remoto
5. `tinker`: o REPL que conhece o seu projeto
6. Um comando próprio, e quando isso é a resposta certa

**Conceitos.** `config/*.php`, `env()` só dentro de `config/`, `php artisan
config:cache`, `APP_ENV`, `about`, `route:list`, `tinker`, `make:command`,
agendamento (`schedule:run`) em uma seção curta.

**Projeto.** `config/biblioteca.php` com prazo de empréstimo, limite por
leitor e valor da multa. Comando `biblioteca:multas` que fecha o dia.

**Erros comuns.** `env()` em service ou controller (e o valor nulo depois do
`config:cache`); segredo com valor padrão permissivo; comando que faz o
trabalho em vez de chamar o service.

**História.** O deploy de sexta em que o `config:cache` rodou antes de o
`.env` ser atualizado.

**Pré-requisitos.** Cap. 22.

**Ao terminar.** Ler configuração do jeito certo e escrever um comando
Artisan que delega a regra ao service.

---

## 24. Rotas e controllers

**Objetivo.** Mapear URLs para código mantendo os controllers pequenos.

**O leitor aprende.** Arquivos de rota, parâmetros, model binding, nome de
rota e os formatos de controller.

**Subcapítulos**
1. O arquivo de rotas é o índice da aplicação
2. `web.php` e `api.php`: dois mundos, dois middlewares
3. Parâmetros, restrições e route model binding
4. Nome de rota: a URL que muda sem quebrar nada
5. Controller invocável, resource controller e o que cada um comunica
6. O controller não precisa saber de tudo
7. `route:list`: a única documentação que nunca mente

**Conceitos.** `Route::get`, grupos, prefixo, `name()`, `where()`, binding
implícito e explícito, `Route::apiResource`, `__invoke`, ordem das rotas.

**Projeto.** Todas as rotas da API desenhadas no capítulo 19, agora
registradas — devolvendo dados fixos por enquanto.

**Erros comuns.** Rota com caminho fixo depois da rota com parâmetro; lógica
dentro do arquivo de rotas; controller que já nasce com oito dependências.

**História.** O `route:list` do Sistema seria impossível: as rotas eram
nomes de arquivo, e havia 137.

**Pré-requisitos.** Cap. 23.

**Ao terminar.** Registrar um conjunto de rotas REST com nomes e binding, e
justificar o formato de controller escolhido.

---

## 25. Requests e responses

**Objetivo.** Entrar e sair da aplicação com objetos, não com superglobais.

**O leitor aprende.** O objeto `Request`, formas de devolver resposta,
status, cabeçalhos e upload.

**Subcapítulos**
1. `Request` é um objeto, não quatro superglobais
2. `input()`, `query()`, `validated()`: pegar o dado certo
3. Devolver array, model ou `JsonResponse` — o que muda
4. Status, cabeçalho e o corpo vazio do `204`
5. Upload de arquivo sem confiar no nome que veio
6. Content negotiation: a mesma rota, duas respostas

**Conceitos.** PSR-7 em uma menção, `Request` do Laravel, `response()`,
`response()->json()`, `Responsable`, `abort()`, `expectsJson()`,
`Storage::putFile`.

**Projeto.** Upload da capa do livro; `204` na devolução; `201` com
`Location` no empréstimo.

**Erros comuns.** Usar `$_POST` dentro do Laravel; devolver `200` em
criação; aceitar o nome do arquivo enviado pelo cliente como caminho.

**História.** O upload que aceitava `../../.env` como nome de arquivo — no
Sistema, em 2009, e por doze anos.

**Pré-requisitos.** Cap. 24.

**Ao terminar.** Receber dados e devolver respostas com status e cabeçalhos
corretos.

---

## 26. Blade, quando a tela ainda é a resposta

**Objetivo.** Montar a parte web que a bibliotecária usa, sem transformar o
livro num curso de front-end.

**O leitor aprende.** Blade, layout, componentes, escape e formulários.

**Subcapítulos**
1. Nem tudo é API: o painel da Vera
2. Blade é PHP, com menos cerimônia
3. Layout, componente e o `@include` que envelhece mal
4. `{{ }}` escapa; `{!! !!}` é uma decisão de segurança
5. Formulário, CSRF e o token que você não vê
6. Quando parar: o limite entre Blade e front-end de verdade

**Conceitos.** `view()`, `@extends`/`@section`, componentes de classe e
anônimos, `@csrf`, XSS e escape automático, `old()`, `@error`.

**Projeto.** Painel de empréstimos: listagem, formulário de empréstimo e
devolução. É a única parte web do livro — a API segue sendo o foco.

**Erros comuns.** `{!! !!}` em dado vindo do usuário; lógica de negócio na
view; montar SPA dentro do Blade e ficar no pior dos dois mundos.

**História.** Vera não quer aplicativo. Ela quer uma tela com um campo de
busca e um botão, igual à do Sistema, "que funcionava".

**Pré-requisitos.** Cap. 25.

**Ao terminar.** Entregar uma tela funcional e explicar por que o resto do
livro continua sendo API.

---

# Parte 6 — Banco de dados

> Eloquent é ferramenta sobre banco, não substituto de saber banco.

---

## 27. Banco de dados e SQL

**Objetivo.** Aprender o suficiente de SQL para entender o que o ORM gera.

**O leitor aprende.** Tabelas, chaves, restrições, consultas, `JOIN`,
índices e transações.

**Subcapítulos**
1. Arquivo não resolve concorrência
2. Tabela, chave primária, chave estrangeira
3. O tipo da coluna é uma decisão de negócio
4. `NOT NULL` por padrão, nulo por exceção
5. `SELECT`, `INSERT`, `UPDATE`, `DELETE` — e o `WHERE` que você escreve
   primeiro
6. `JOIN`: a pergunta que envolve duas tabelas
7. Índice: por que a busca fica lenta
8. Transação: tudo ou nada

**Conceitos.** DDL × DML, PK/FK, `UNIQUE`, `CHECK`, `DECIMAL` × `FLOAT`,
`DATETIME` e fuso, `INNER`/`LEFT JOIN`, `GROUP BY`, plano de execução,
ACID, `BEGIN`/`COMMIT`/`ROLLBACK`, normalização até a 3FN em uma seção
curta, injeção de SQL e *prepared statements*.

**Projeto.** O esquema completo da Casa Amarela, escrito em SQL puro antes
de existir migration.

**Erros comuns.** `UPDATE` sem `WHERE`; `FLOAT` para multa; chave
estrangeira sem índice; concatenar valor no SQL.

**História.** Dedé roda `EXPLAIN` na consulta de busca do Sistema. Quatro
milhões de linhas lidas para devolver três.

**Pré-requisitos.** Cap. 26.

**Ao terminar.** Escrever e ler SQL de CRUD e de `JOIN`, e explicar o que um
índice faz.

---

## 28. Migrations, seeders e factories

**Objetivo.** Versionar o esquema e ter dados de desenvolvimento
reprodutíveis.

**O leitor aprende.** Migration como histórico, alteração segura, seeders e
factories.

**Subcapítulos**
1. Migration não é backup
2. `up`, `down` e a migration que você não consegue desfazer
3. O estado do banco mora numa tabela
4. Alterar coluna sem derrubar a aplicação
5. Seeder: o dado que todo ambiente precisa
6. Factory: o dado de mentira que parece de verdade
7. Quem roda migration em produção, e quando

**Conceitos.** `make:migration`, `Schema::create`/`table`, `migrate`,
`rollback`, `fresh`, tabela `migrations`, `down` honesto, expansão e
contração, `db:seed`, `factory()`, estados de factory, Faker em pt_BR.

**Projeto.** Todas as tabelas do capítulo 27 como migrations; seeder de
assuntos e de usuário administrador; factories de `Livro`, `Exemplar`,
`Leitor` e `Emprestimo`.

**Erros comuns.** Editar migration já aplicada em produção; `migrate:fresh`
no ambiente errado; seeder com dado de teste indo para produção; factory que
não representa o caso real.

**História.** O `migrate:fresh --seed` rodado com o `.env` de homologação
apontando para o banco de produção. São 11h40 de uma quinta.

**Pré-requisitos.** Cap. 27.

**Ao terminar.** Criar o esquema por migration, popular o ambiente e gerar
dados falsos convincentes.

---

## 29. Eloquent

**Objetivo.** Usar o ORM sabendo o SQL que ele produz.

**O leitor aprende.** Active Record, consultas, mass assignment, casts,
scopes e os sinais de model gigante.

**Subcapítulos**
1. Eloquent não é SQL mágico
2. Active Record: o objeto que sabe se salvar
3. `find`, `first`, `firstOrFail` e o `null` que escapa
4. Mass assignment: `$fillable` existe por um motivo
5. Casts, accessors e mutators
6. Scopes: a consulta que ganha nome
7. Ver o SQL gerado antes de confiar nele
8. Model gigante: os sinais e a saída

**Conceitos.** `Model`, convenções de nome, `$fillable`/`$guarded`, `$casts`
(inclusive para enum do cap. 17), `Attribute` accessors, *query scopes*,
`toSql()`, `DB::listen`, `Model::preventSilentlyDiscardingAttributes()`,
coleções do Eloquent.

**Projeto.** Models `Livro`, `Exemplar`, `Leitor`, `Emprestimo` com casts
para os enums e o objeto `Dinheiro`.

**Erros comuns.** `$guarded = []` com campo `is_admin` na tabela; lógica de
negócio de 300 linhas dentro do model; `all()` numa tabela de milhões;
`update` em massa ignorando eventos.

**História.** O cadastro de leitor que aceitava `perfil=admin` no corpo da
requisição, porque o model estava com `$guarded = []`.

**Pré-requisitos.** Cap. 28.

**Ao terminar.** Escrever consultas com Eloquent e mostrar o SQL
correspondente.

---

## 30. Relacionamentos

**Objetivo.** Modelar as ligações do domínio e evitar o N+1.

**O leitor aprende.** Tipos de relacionamento, tabela pivô, eager loading e
cascata.

**Subcapítulos**
1. A chave estrangeira mora do lado que tem muitos
2. `hasMany`, `belongsTo` e o nome que o Laravel adivinha
3. Muitos-para-muitos e a tabela do meio com atributos
4. `hasManyThrough` e polimórfico: quando compensa
5. N+1: cem consultas escondidas atrás de um ponto
6. `with`, `load` e `preventLazyLoading`
7. Apagar em cascata: a operação sem desfazer

**Conceitos.** `hasOne`/`hasMany`/`belongsTo`/`belongsToMany`,
`withPivot`, `withTimestamps`, `hasManyThrough`, `morphMany`, `with()`
× `load()`, `withCount`, `Model::preventLazyLoading()`, `onDelete('cascade')`
× exclusão lógica.

**Projeto.** `Livro ↔ Autor` (N:N), `Livro → Exemplar → Emprestimo`,
`Leitor → Emprestimo`; a listagem do acervo carregando autores e contagem de
exemplares disponíveis.

**Erros comuns.** N+1 na serialização (quando o resource toca o
relacionamento); `belongsToMany` sem `withPivot` e o dado que some; cascade
apagando histórico de empréstimo.

**História.** A listagem do acervo levava 4 segundos. `DB::listen` mostra
143 consultas para 47 livros.

**Pré-requisitos.** Cap. 29.

**Ao terminar.** Modelar os dois tipos de relacionamento e provar, contando
consultas, que o eager loading funcionou.

# Parte 7 — A API de verdade

---

## 31. O CRUD completo

**Objetivo.** Ligar rotas, controllers, models e banco, e ter o CRUD do
acervo funcionando de ponta a ponta.

**O leitor aprende.** As cinco operações com status corretos, transação de
negócio e o inventário honesto do que ainda está errado.

**Subcapítulos**
1. As cinco rotas e o que cada uma promete
2. Criar: `201`, `Location` e o recurso de volta
3. Ler um: `404` é uma resposta, não uma falha
4. `PUT` e `PATCH` não são a mesma coisa
5. Apagar: `204`, e a pergunta sobre apagar de verdade
6. Uma operação de negócio, um `commit`
7. "É só um CRUD": o que ainda está errado neste capítulo

**Conceitos.** `apiResource`, binding implícito e `404` automático,
`DB::transaction`, exclusão lógica (`SoftDeletes`) × exclusão física,
resposta de criação.

**Projeto.** CRUD de `Livro` e de `Exemplar`; a primeira versão de
`POST /emprestimos`, ainda com regra dentro do controller — de propósito.

**Erros comuns.** `200` em criação; `PUT` que se comporta como `PATCH` e
apaga campos; duas escritas sem transação; apagar livro com histórico.

**História.** Seu Juvenal: "mas isso não é só um CRUD?". Dedé lista as sete
regras de empréstimo que Vera recitou no capítulo 5 e pergunta em qual das
cinco rotas elas caberiam.

**Pré-requisitos.** Cap. 30.

**Ao terminar.** Entregar um CRUD completo e apontar, por escrito, os cinco
defeitos que os próximos capítulos corrigem.

---

## 32. Validation e Form Requests

**Objetivo.** Recusar entrada inválida na borda e deixar o controller
pequeno.

**O leitor aprende.** Regras de validação, Form Request, `PATCH` parcial e o
limite entre validação e regra de negócio.

**Subcapítulos**
1. Validação não é regra de negócio
2. Regras onde o dado entra, não onde ele é usado
3. Form Request: o controller que volta a ter quatro linhas
4. `sometimes`, `nullable` e o `PATCH` que apaga campo
5. Regra própria, e quando ela já existe
6. `422`, `errors` e o campo que o cliente precisa destacar
7. Validar também o que sai

**Conceitos.** `$request->validate()`, `FormRequest`, `rules()`,
`authorize()` (e por que ele volta no cap. 40), `Rule::unique()->ignore()`,
`Rule::enum()`, regra de objeto, mensagens e atributos personalizados,
`prepareForValidation` como ponto de normalização.

**Projeto.** `StoreLivroRequest`, `UpdateLivroRequest`,
`RealizarEmprestimoRequest`; normalização de ISBN e de título.

**Erros comuns.** Validar no controller e no service com regras diferentes;
`unique` no `PUT` acusando o próprio registro; `nullable` usado como se
fosse "opcional".

**História.** O ISBN cadastrado com hífen, sem hífen e com espaço — três
registros do mesmo livro no acervo.

**Pré-requisitos.** Cap. 31.

**Ao terminar.** Mover toda a validação de forma para Form Requests e
explicar o que **não** vai para lá.

---

## 33. API Resources

**Objetivo.** Separar o formato da resposta da estrutura da tabela.

**O leitor aprende.** `JsonResource`, coleções, campos condicionais e
controle do que sai.

**Subcapítulos**
1. O model não é o JSON
2. `Resource` e `ResourceCollection`
3. `whenLoaded`: o relacionamento que só aparece se foi carregado
4. Campo interno que não pode sair, nunca
5. Envelope, `meta` e a paginação que vem junto
6. Versionar a resposta sem versionar o mundo

**Conceitos.** `JsonResource::toArray`, `ResourceCollection`,
`whenLoaded`, `when`, `additional`, `$wrap`, `preserveKeys`, contrato
público × esquema interno.

**Projeto.** `LivroResource`, `ExemplarResource`, `EmprestimoResource`;
`LeitorResource` que nunca expõe documento nem e-mail para outro leitor.

**Erros comuns.** `return $livro` e a coluna interna que aparece na semana
seguinte; resource que dispara N+1 ao tocar relacionamento não carregado;
dois formatos de resposta na mesma API.

**História.** A coluna `observacao_interna`, criada para a equipe, aparecendo
no aplicativo do leitor por onze dias.

**Pré-requisitos.** Cap. 32.

**Ao terminar.** Controlar exatamente o que sai de cada endpoint e provar
com o teste do capítulo 44.

---

## 34. Paginação, filtros e buscas

**Objetivo.** Tornar a listagem utilizável e segura para volumes reais.

**O leitor aprende.** Os três paginadores, ordenação estável, filtros
opcionais e busca por texto.

**Subcapítulos**
1. Listagem sem limite é uma negação de serviço que você publicou
2. `paginate`, `simplePaginate` e `cursorPaginate`
3. Ordenação estável: o desempate que ninguém lembra
4. Filtro opcional sem escada de `if`
5. Busca por texto: `LIKE`, acento e o índice que não é usado
6. Ordenar por campo do cliente sem abrir o banco para ele
7. O teto é do servidor

**Conceitos.** `paginate()` e o `meta` gerado, cursor × offset, `when()` no
query builder, escopos de filtro, objeto de filtro tipado, `LIKE '%x%'` e
índice, `FULLTEXT`, lista de permissão para `sort`.

**Projeto.** `GET /livros?busca=&assunto=&disponivel=&sort=&page=` com teto
de 100 por página.

**Erros comuns.** `?per_page=999999` aceito; `orderBy($request->sort)` sem
lista de permissão; `if ($request->preco_min)` ignorando zero; paginação sem
desempate perdendo registros.

**História.** A busca por "acafrao" que não encontra "Açafrão" — e a
descoberta de que metade do acervo foi cadastrada sem acento, em teclados
comprados numa licitação.

**Pré-requisitos.** Cap. 33.

**Ao terminar.** Entregar uma listagem paginada, filtrável e ordenável sem
abrir brecha.

---

## 35. Erros padronizados

**Objetivo.** Fazer toda resposta de erro da API ter a mesma cara e nunca
vazar detalhe interno.

**O leitor aprende.** O handler de exceções, tradução de exceção de domínio
para status, e o que nunca sai no corpo.

**Subcapítulos**
1. Três formatos de erro na mesma API é pior que um formato errado
2. O handler e o `render` que você sobrescreve
3. Exceção de domínio vira status numa linha
4. O `404` do route model binding: útil e genérico demais
5. `500` não vaza *stack trace*, nome de tabela nem query
6. Código de incidente: o número que o suporte pede
7. `401` e `403` não são a mesma coisa

**Conceitos.** `bootstrap/app.php` → `withExceptions`, `renderable`,
`ValidationException`, `ModelNotFoundException`,
`AuthenticationException`, `AuthorizationException`, `HttpException`,
`APP_DEBUG` em produção, correlação de requisição.

**Projeto.** Formato único `{tipo, mensagem, campos?, incidente?}` para toda
a API; as três exceções do capítulo 15 mapeadas para `409`.

**Erros comuns.** `APP_DEBUG=true` em produção; `try/catch` repetido em cada
controller; `404` para erro de permissão sem decidir que é isso que se quer.

**História.** O leitor liga dizendo "deu erro". O log tem 4.200 linhas e
nenhum identificador. Quarenta minutos depois, Tainá escolhe o traceback
errado.

**Pré-requisitos.** Cap. 34.

**Ao terminar.** Padronizar o erro da API inteira e explicar a diferença
entre `401`, `403`, `404`, `409` e `422`.

---

# Parte 8 — Arquitetura e segurança

---

## 36. Service Container e injeção de dependência

**Objetivo.** Entender o mecanismo que monta os objetos e por que ele existe.

**O leitor aprende.** Autowiring, amarrações, providers e substituição em
teste.

**Subcapítulos**
1. O `new` espalhado pelo código é o problema
2. O Service Container não é decoração: ele monta o grafo
3. Autowiring: como ele adivinha o que a sua classe quer
4. `bind`, `singleton` e `scoped`
5. Service Provider: onde as amarrações moram
6. Interface no construtor, implementação no provider
7. Trocar a implementação no teste sem tocar no código

**Conceitos.** IoC, reflexão (retomada do contêiner ingênuo do cap. 20),
`app()`, `bind` × `singleton` × `scoped`, contextual binding, `register` ×
`boot`, *facades* e o que elas escondem, `$this->app->instance()` em teste.

**Projeto.** `EnviadorDeAviso` como interface, com implementação real e
implementação falsa; `NotificacaoServiceProvider`.

**Erros comuns.** `new` dentro do controller; `singleton` guardando estado
de requisição; usar o container como *service locator* (`app('x')` no meio
do código).

**História.** Dedé abre o contêiner de vinte linhas do capítulo 20 ao lado
do do Laravel. Tainá reconhece a reflexão.

**Pré-requisitos.** Cap. 35.

**Ao terminar.** Declarar dependência por construtor e trocar a
implementação sem alterar quem usa.

---

## 37. Services: onde a regra de negócio mora

**Objetivo.** Decidir onde cada regra vive — e quantas camadas o projeto
realmente precisa.

**O leitor aprende.** Service como fronteira de transação, o limite do
model, e quando repositório é burocracia.

**Subcapítulos**
1. Controller com 800 linhas começa com vinte
2. A regra que envolve duas entidades não cabe no model
3. Um método público do service é uma transação
4. O service não conhece HTTP
5. Repository: quando ajuda e quando é burocracia
6. Nem todo projeto precisa de todas as camadas
7. Service sem propósito: como reconhecer

**Conceitos.** Camadas `Route → Controller → Service → Model → DB`, fronteira
transacional, exceção de domínio como saída, abstração prematura, *action
class* como alternativa ao service gordo, quando o model basta.

**Projeto.** `EmprestimoService` com `realizar()`, `renovar()` e
`devolver()` — as onze condições do capítulo 5, finalmente num lugar só.

**Erros comuns.** Service que só repassa para o model; repositório criado
"porque é boa prática" sobre um ORM que já é repositório; `commit` dentro de
método privado.

**História.** Vera lê o método `realizar()` em voz alta e corrige uma regra
que a equipe tinha entendido errado desde o capítulo 5. Levou dezoito
segundos — e só foi possível porque a regra cabia numa tela.

**Pré-requisitos.** Cap. 36.

**Ao terminar.** Mover a regra do controller para o service e defender, para
cada camada, por que ela existe naquele projeto.

---

## 38. Middleware

**Objetivo.** Tratar o que vale para muitas rotas sem repetir código.

**O leitor aprende.** A pipeline, tipos de middleware, ordem e limites.

**Subcapítulos**
1. A cebola: o que acontece antes e depois da sua rota
2. Global, de grupo e de rota
3. Ordem importa mais do que parece
4. Throttle: o limite que protege de você mesmo
5. Um middleware próprio, e quando ele não é a resposta
6. O que não colocar ali dentro

**Conceitos.** Pipeline (retomada do cap. 20), `handle($request, $next)`,
terminable middleware, `throttle`, grupos `web`/`api`, middleware com
parâmetro, correlação de requisição.

**Projeto.** `RegistraRequisicao` (identificador de correlação),
`throttle` na rota de login, `ForcaJson` na API.

**Erros comuns.** Consulta ao banco em middleware global; regra de negócio
em middleware; ordem errada fazendo autenticação rodar depois da
autorização.

**História.** O middleware de log que gravava o corpo da requisição —
incluindo o campo `senha` — por três meses.

**Pré-requisitos.** Cap. 37.

**Ao terminar.** Escrever um middleware e explicar por que uma dada regra
não pertence a ele.

---

## 39. Autenticação com Sanctum

**Objetivo.** Responder "quem é você" com segurança.

**O leitor aprende.** Hash de senha, tokens, sessão × token, e as respostas
que não entregam informação.

**Subcapítulos**
1. Senha nunca é guardada
2. `bcrypt`, `argon2` e o custo que é proposital
3. Sessão e token: dois problemas diferentes
4. Sanctum: token pessoal e SPA no mesmo pacote
5. Login, logout e o token que continua valendo
6. Revogar de verdade
7. A resposta que não diz se o e-mail existe

**Conceitos.** `Hash::make`/`check`, fator de custo, `HasApiTokens`,
`createToken`, habilidades do token, `auth:sanctum`, expiração,
`tokens()->delete()`, ataque de tempo, HTTPS como pré-requisito.

**Projeto.** `POST /auth/login`, `POST /auth/logout`, `GET /eu`; o `Usuario`
com papéis `leitor`, `atendente`, `admin`.

**Erros comuns.** MD5 ou SHA-256 para senha; mensagem que distingue "usuário
não existe" de "senha errada"; token sem expiração; senha no log.

**História.** O Sistema guardava senha em MD5 sem sal. Dedé roda um
dicionário e quebra 60% das contas em quatro minutos — na máquina dele, no
horário do almoço.

**Pré-requisitos.** Cap. 38.

**Ao terminar.** Implementar login com token e explicar por que a resposta
de erro é genérica e por que ela demora o mesmo tempo nos dois casos.

---

## 40. Autorização: Gates e Policies

**Objetivo.** Responder "o que você pode" — inclusive quando o recurso é de
outra pessoa.

**O leitor aprende.** Gate, Policy, verificação de propriedade e escopo de
listagem.

**Subcapítulos**
1. Autenticação diz quem; autorização diz o quê
2. Gate para a regra solta, Policy para o recurso
3. `authorize`, `can` e o `403` que sai sozinho
4. O recurso é dele? A camada que nenhum middleware resolve
5. Listagem com escopo: o filtro que o cliente não escolhe
6. Papel não é permissão
7. Testar permissão é obrigatório, porque ninguém testa à mão

**Conceitos.** `Gate::define`, `make:policy`, descoberta automática de
policy, `authorize()` no controller e no Form Request, `@can` no Blade,
`before()` para o admin, *broken object level authorization*, escopo de
consulta por papel.

**Projeto.** `EmprestimoPolicy` (leitor vê e renova só os próprios),
`LivroPolicy` (atendente cadastra, admin apaga), escopo automático na
listagem.

**Erros comuns.** Confiar no `leitor_id` que veio no filtro; `403` que
confirma a existência do recurso; papel gravado no token e revogado só no
próximo login.

**História.** O leitor que descobre `?leitor_id=3` e liga animado dizendo
que "consegue ver os livros de todo mundo".

**Pré-requisitos.** Cap. 39.

**Ao terminar.** Proteger recurso por propriedade e por papel, com teste
para cada caso.

# Parte 9 — Depois da resposta

---

## 41. Events, jobs e filas

**Objetivo.** Tirar da requisição o trabalho que não precisa acontecer antes
da resposta.

**O leitor aprende.** Evento e listener, job, fila, worker, retentativa e
idempotência.

**Subcapítulos**
1. O que não precisa acontecer antes da resposta
2. Event e listener: desacoplar sem esconder
3. Job: a unidade de trabalho que pode falhar e voltar
4. Driver de fila: `sync`, `database`, `redis`
5. Worker, supervisor e o processo que precisa reiniciar no deploy
6. Retentativa, `backoff` e `failed_jobs`
7. Job precisa ser idempotente
8. Quando o evento vira espaguete invisível

**Conceitos.** `Event`/`Listener`, `ShouldQueue`, `dispatch`, filas
nomeadas, `queue:work` × `queue:listen`, `--max-time`, `tries`, `retryUntil`,
`failed()`, `queue:retry`, idempotência, `Bus::batch` em menção, Horizon em
uma linha.

**Projeto.** `EmprestimoRealizado` → envio de comprovante; job diário
`AvisarDevolucaoProxima`; `ReservaDisponivel` quando um exemplar volta.

**Erros comuns.** Enviar e-mail dentro do controller; job que depende de
objeto não serializável; worker antigo rodando código velho depois do
deploy; listener que faz o trabalho e também dispara outro evento.

**História.** O aviso de devolução enviado 1.400 vezes para a mesma pessoa,
porque o job não era idempotente e o worker reiniciou no meio.

**Pré-requisitos.** Cap. 40.

**Ao terminar.** Mover trabalho para a fila e explicar o que acontece quando
ele falha na terceira tentativa.

---

## 42. Cache, logs e o que se mede

**Objetivo.** Tornar a aplicação observável e rápida, nessa ordem.

**O leitor aprende.** Cache com invalidação, log estruturado e medição antes
de otimização.

**Subcapítulos**
1. Uma fila existe porque esperar custa caro; um cache também
2. `Cache::remember` e a pergunta difícil: quando invalidar
3. Cache de configuração, rota e view — e o deploy que esquece
4. Log não é `dd()`
5. Níveis, canais e o log estruturado que dá para procurar
6. O que nunca entra no log
7. Medir antes de otimizar: query lenta, N+1 e o tempo que some

**Conceitos.** Drivers de cache, `remember`, `forget`, tags, invalidação por
evento × por tempo, `config:cache`/`route:cache`/`view:cache`, canais de log
do Monolog, níveis, contexto estruturado, `DB::listen`, Telescope e
Debugbar em desenvolvimento, `slow query log`.

**Projeto.** Cache dos "mais emprestados do mês", invalidado pelo evento de
devolução; log estruturado com identificador de correlação do capítulo 38.

**Erros comuns.** Cache sem estratégia de invalidação; `dd()` esquecido em
produção; log com token ou documento; otimizar a consulta errada por não ter
medido.

**História.** A página do acervo ficou rápida e passou a mostrar um livro
emprestado como disponível — por seis horas, que era o TTL.

**Pré-requisitos.** Cap. 41.

**Ao terminar.** Instrumentar a aplicação e decidir o que cachear com base
em medição.

---

# Parte 10 — Provar e publicar

---

## 43. Testes: o que estamos tentando provar

**Objetivo.** Escrever testes rápidos sobre a regra de negócio, sem banco e
sem HTTP.

**O leitor aprende.** Pest/PHPUnit, estrutura do teste, dublês e uso de
factory como fixture.

**Subcapítulos**
1. Teste não prova que está certo; prova que continua funcionando
2. Pest ou PHPUnit: escolha uma e siga
3. Arrumar, agir, afirmar
4. Testar a regra sem banco e sem HTTP
5. Dublês: fake, stub, spy, mock — e por que o fake ganha
6. Factory como fixture
7. O teste que reproduz o defeito de ontem

**Conceitos.** `php artisan test`, sintaxe do Pest, *data providers* /
`dataset`, `expect()`, `Mockery`, `spy`, `partialMock`, injeção como
pré-requisito de testabilidade (retomada do cap. 36), cobertura como mapa e
não como nota.

**Projeto.** Testes unitários de `EmprestimoService` com repositório falso:
limite por leitor, exemplar indisponível, leitor com pendência, cálculo de
multa nas bordas.

**Erros comuns.** Teste sem `assert`; mock verificando chamada em vez de
resultado; meta de cobertura virando jogo; teste que depende do relógio.

**História.** A regra de estoque negativo volta por outro caminho, seis
meses depois. Havia correção; não havia teste.

**Pré-requisitos.** Cap. 42.

**Ao terminar.** Testar as onze condições de empréstimo em menos de um
segundo.

---

## 44. Testes de feature, HTTP e banco

**Objetivo.** Verificar o contrato da API e as garantias que só o banco dá.

**O leitor aprende.** Testes HTTP, isolamento de banco, autenticação e
autorização em teste, e fakes de infraestrutura.

**Subcapítulos**
1. `getJson()`, `postJson()` e o contrato verificado
2. `RefreshDatabase`: isolamento sem `TRUNCATE`
3. `actingAs` e o teste de rota protegida
4. Testar `403` é testar o que ninguém testa à mão
5. `assertDatabaseHas` e o que ele prova de verdade
6. Fake de fila, e-mail e evento
7. Suíte lenta: diagnosticar antes de culpar o banco

**Conceitos.** `assertStatus`, `assertJsonPath`,
`assertJsonValidationErrors`, `assertJsonMissing`, `RefreshDatabase` ×
`DatabaseTransactions`, SQLite em memória e onde ele mente, `Queue::fake`,
`Mail::fake`, `Event::fake`, `--parallel`, `--profile`.

**Projeto.** Suíte de feature cobrindo o CRUD, o fluxo de empréstimo, os
`422`, os `403` por papel e por propriedade, e um teste que garante que
`observacao_interna` nunca aparece na resposta.

**Erros comuns.** Repetir na camada HTTP o que já foi testado no service;
SQLite em memória escondendo diferença de tipo; teste dependente de ordem
por falta de isolamento; `Queue::fake` mascarando job que nunca funcionou.

**História.** A esteira vermelha por três dias num teste que passava em toda
máquina local — faltava `ORDER BY`, no teste e no código.

**Pré-requisitos.** Cap. 43.

**Ao terminar.** Ter uma suíte que falha quando o contrato muda, e saber
dizer quanto tempo ela pode levar.

---

## 45. Documentação da API

**Objetivo.** Publicar uma documentação que nasce do código e não
desatualiza.

**O leitor aprende.** OpenAPI, geração a partir do projeto, documentação de
erro e política de depreciação.

**Subcapítulos**
1. Documentação que não nasce do código começa a mentir
2. OpenAPI: o esquema que gera tudo o mais
3. Gerar a partir das rotas, requests e resources
4. Documentar o erro é documentar metade do contrato
5. Exemplos que a pessoa clica e executa
6. Versionar e marcar o que vai sair
7. Expor ou não a documentação em produção

**Conceitos.** OpenAPI 3, `scramble` ou atributos PHP para descrever
endpoints, esquema de segurança (Sanctum) no documento, `deprecated`,
geração de cliente a partir do esquema, teste que compara o esquema com a
suíte.

**Projeto.** `/docs` e `openapi.json` gerados; os quatro formatos de erro do
capítulo 35 descritos; o plano de transição de um campo renomeado.

**Erros comuns.** Documento mantido à mão num wiki; documentar só o caminho
feliz; expor documentação de API administrativa sem autenticação.

**História.** A integração do aplicativo demorou três semanas porque a única
documentação era "pergunta pro Dedé".

**Pré-requisitos.** Cap. 44.

**Ao terminar.** Publicar documentação executável e explicar como um campo
sai do ar sem quebrar quatro clientes.

---

## 46. Git, CI e o dia do deploy

**Objetivo.** Sair do "funciona na minha máquina" e colocar a aplicação no
ar com o que uma API de verdade exige — e fechar o projeto.

**O leitor aprende.** Histórico legível, esteira automatizada, migração em
produção, health check e a lista antes de publicar.

**Subcapítulos**
1. `.gitignore` antes do primeiro `git add`
2. Segredo que entrou no histórico se resolve trocando o segredo
3. Commit que conta uma história
4. A esteira: Pint, PHPStan, testes
5. Migration em produção é um passo separado
6. `artisan down`, cache de config e o worker que precisa reiniciar
7. Health check: vivo não é o mesmo que pronto
8. A lista antes de publicar
9. O último pedido da Casa Amarela

**Conceitos.** `.gitignore` do Laravel, ramos e revisão, `pint`, PHPStan na
esteira, GitHub Actions com MySQL de serviço, ordem do deploy
(`down` → `migrate` → `config:cache` → `queue:restart` → `up`), zero
downtime em uma seção honesta, `/saude` × `/pronto`, `APP_DEBUG=false`,
HTTPS, backup **testado**, Docker apenas onde agrega.

**Projeto.** Esteira completa; script de deploy; e o requisito final — uma
regra nova que o leitor implementa sozinho, atravessando validação, service,
policy, evento, fila e teste.

**Erros comuns.** `.env` versionado; `APP_DEBUG=true` em produção; migration
rodando em cinco contêineres ao mesmo tempo; deploy sem `queue:restart`;
backup que nunca foi restaurado.

**História.** Última cena. Vera imprime a ficha de empréstimo de papel pela
última vez e a guarda no bolso do avental. Seu Juvenal pergunta quanto tempo
leva para fazer "um sisteminha" para a horta comunitária.

**Pré-requisitos.** Cap. 45.

**Ao terminar.** Colocar a aplicação no ar com checklist cumprido — e
implementar um requisito novo de ponta a ponta, sozinho.

---

# Notas de produção

**Volume.** 46 capítulos. Média-alvo de 1.700 a 2.000 palavras por capítulo
— a mesma régua do Python One, acima da do Java One.

**Ritmo.** Regra explícita para não repetir o defeito do volume 1:
`:::story` em torno de 24 dos 46 capítulos, `:::art` em 8, `:::checkpoint`
ao fim de cada parte (10), `:::milestone` nos marcos reais (cap. 22, 31, 40,
46), e **de 2 a 4 exercícios** por capítulo, nunca 3 fixos.

**Referências.** Todo apontamento para outro capítulo usa `@cap:<slug>`, com
`slug:` declarado no front matter. Alvo inexistente é erro de build.

**Código.** Máximo de 70 colunas (`code.max_line_chars`), 40 nos blocos
`:::compare`. PHP 8.3 com `declare(strict_types=1)` em todo arquivo a partir
do capítulo 16. Laravel 11+ (estrutura sem `app/Http/Kernel.php`,
`bootstrap/app.php` como ponto de configuração).

**Blocos recorrentes.** `:::anatomy` para requisição HTTP (cap. 18),
assinatura de método (cap. 7), migration (cap. 28) e JWT/token (cap. 39);
`:::http` em todos os capítulos da Parte 7; `:::tree` para a estrutura do
Laravel (cap. 22) e do projeto (cap. 11); `:::compare` para
legado × moderno, que é o recurso visual mais característico deste volume.

**O que este livro não cobre, e diz que não cobre.** Livewire, Inertia,
Vue/React, Octane, multitenancy, GraphQL, microsserviços, Kubernetes. Cada
um ganha uma linha no fechamento do capítulo 46, com a indicação de onde
procurar.
