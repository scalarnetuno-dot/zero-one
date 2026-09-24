---
title: "Eloquent"
number: 11
slug: eloquent
part: p3
kicker: "O cadastro de leitor aceitava um campo que o formulário não tinha. Quem descobriu isso virou bibliotecária-chefe em nove segundos."
goal: >-
  Usar o ORM sabendo qual consulta cada método produz, proteger o cadastro
  contra campos que ninguém pediu, converter valores na entrada e na saída
  do banco, e reconhecer quando um model virou depósito.
---

:::story Perfil admin
Tainá estava testando o cadastro público de leitor com `curl`, porque
formulário esconde campo e ela queria ver o que a API aceitava de verdade.

```text
$ curl -s -X POST localhost:8000/api/leitores \
       -H "Content-Type: application/json" \
       -d '{"nome":"Teste","documento":"11122233344",
            "perfil":"admin"}'
```

```text
{"id":4102,"nome":"Teste","documento":"11122233344",
 "perfil":"admin"}
```

Ela leu duas vezes.

— Dedé, o formulário de cadastro tem campo de perfil?

— Não. Perfil só a Vera muda, na tela dela.

— Então por que ele aceitou?

Dedé abriu o model. A segunda linha da classe era:

```php
protected $guarded = [];
```

— Isso quer dizer que nada é protegido.

— Isso quer dizer que eu sou administradora agora.
:::

## Eloquent não é SQL mágico

Cada método do Eloquent produz uma consulta, e você consegue escrever todas
elas à mão — foi o que os capítulos da Parte 2 do volume 1 fizeram.

Este capítulo inteiro segue uma regra: **nenhum método aparece sem a
consulta ao lado.**

```php
Livro::where('assunto', 'infantil')->orderBy('titulo')->get();
```

```sql
SELECT * FROM livros WHERE assunto = ? ORDER BY titulo ASC
```

O `?` não é enfeite: o Eloquent monta consulta preparada, sempre, pelo
motivo do capítulo @cap:pdo. O valor viaja separado do comando.

:::key
O ORM não poupa você de saber SQL. Ele poupa você de **escrever** o SQL
repetitivo — o `SELECT` de cinco colunas, o `INSERT` com oito campos, o
`JOIN` óbvio.

O SQL que importa continua sendo escrito por alguém. A diferença é que, com
o ORM, você só precisa escrever o que é interessante.
:::

## O model e as convenções

```php title="app/Models/Livro.php" numbered
<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Livro extends Model
{
    protected $fillable = [
        'titulo', 'autor', 'isbn', 'assunto', 'ano',
    ];
}
```

Seis linhas úteis, e o model já sabe ler e gravar. As convenções que ele
assumiu:

| Convenção | Valor assumido |
|---|---|
| tabela | plural do nome da classe |
| chave primária | `id` |
| datas | `created_at` e `updated_at` |

Tabela: Todas são ajustáveis, e a primeira precisa ser ajustada com
frequência num projeto em português.

:::pitfall
O pluralizador do Laravel fala inglês. Ele resolve `Livro` para `livros` por
acaso — porque acrescentar `s` funciona —, e erra o resto:

| Classe | O Laravel procura | A tabela se chama |
|---|---|---|
| `Livro` | `livros` | `livros` |
| `Exemplar` | `exemplars` | `exemplares` |
| `Leitor` | `leitors` | `leitores` |
| `Emprestimo` | `emprestimos` | `emprestimos` |

Tabela: Dois acertos e dois erros, e o erro aparece como
`Table 'casa_amarela.exemplars' doesn't exist` na primeira consulta.

A correção é uma linha, e vale declarar **em todos os models** de um projeto
em português — inclusive nos que dariam certo, para que ninguém precise
lembrar de quais são quais:

```php
protected $table = 'exemplares';
```
:::

## Active Record: o objeto que sabe se salvar

```php
$livro = new Livro();
$livro->titulo = 'Vidas Secas';
$livro->autor = 'Graciliano Ramos';
$livro->assunto = 'literatura';
$livro->save();
```

```sql
INSERT INTO livros (titulo, autor, assunto, updated_at, created_at)
VALUES (?, ?, ?, ?, ?)
```

```php
$livro->ano = 1938;
$livro->save();
```

```sql
UPDATE livros SET ano = ?, updated_at = ? WHERE id = ?
```

O mesmo método faz as duas coisas, e o objeto decide qual pela existência da
chave. Isso é o padrão **Active Record**: o registro e o comportamento no
mesmo objeto.

É conveniente e tem um custo que aparece em dois pontos. O objeto carrega
uma dependência do banco para todo lugar aonde for — e testar a regra que
vive dentro dele exige banco. É a razão de este livro manter a regra de
negócio em serviços, e usar o model para o que ele faz bem: ir e voltar da
tabela.

## Buscar, e o `null` que escapa

| Método | SQL | Quando não acha |
|---|---|---|
| `find(12)` | `WHERE id = ?` | devolve `null` |
| `findOrFail(12)` | `WHERE id = ?` | lança, e vira `404` |
| `first()` | `LIMIT 1` | devolve `null` |
| `firstOrFail()` | `LIMIT 1` | lança, e vira `404` |
| `value('titulo')` | `SELECT titulo ... LIMIT 1` | devolve `null` |

Tabela: Os quatro primeiros diferem numa coisa só, e é a mais importante.

```php
$livro = Livro::find($id);

echo $livro->titulo;
```

```text
Attempt to read property "titulo" on null
```

O `find` devolveu `null` e o erro aparece na linha seguinte — ou trinta
linhas depois, ou na view. A versão com `OrFail` falha no lugar certo, com a
resposta certa:

```php
$livro = Livro::findOrFail($id);
```

```text
404 Not Found
```

:::key
Use `find` quando `null` for **uma resposta possível** que você vai tratar
ali mesmo. Use `findOrFail` quando a ausência for um erro.

Na prática, dentro de um controller com route model binding do capítulo
@cap:rotas-e-controllers, você raramente escreve qualquer um dos dois: o
framework já buscou.
:::

E o método que parece inofensivo e não é:

```php
Livro::all();
```

```sql
SELECT * FROM livros
```

Quatro mil linhas na memória para mostrar vinte. Numa tabela de empréstimos
com anos de histórico, é a consulta que derruba o servidor numa terça à
tarde. O `paginate(20)` existe para isso.

## Mass assignment

Volta ao `perfil=admin`.

```php
Leitor::create($request->all());
```

O `create` recebe um array e preenche o registro com ele. A pergunta é:
**quais campos ele aceita?**

```php
protected $fillable = ['nome', 'documento', 'telefone'];
```

Com `$fillable`, ele aceita esses três e **ignora em silêncio** qualquer
outro. O `perfil` que a Tainá mandou é descartado.

A alternativa, `$guarded`, é a lista do que **não** pode ser preenchido — e
`$guarded = []` quer dizer "nada é proibido", que é exatamente o que o model
do Leitor dizia.

:::pitfall
`$guarded = []` aparece em tutorial porque tira um obstáculo de quem está
aprendendo. Ele transforma toda coluna da tabela num campo público de
formulário.

O dano depende do que existe na tabela: `perfil`, `saldo`, `aprovado`,
`id_da_empresa`. Em qualquer sistema com mais de um nível de acesso, essa
linha é uma escalada de privilégio esperando alguém curioso.

A regra: **`$fillable` sempre, com a lista escrita à mão.** Escrever a lista
é o momento em que você decide, campo a campo, o que o mundo de fora pode
preencher.
:::

E existe uma proteção a mais, que transforma o descarte silencioso em erro:

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    Model::preventSilentlyDiscardingAttributes(
        ! $this->app->isProduction()
    );
}
```

Em desenvolvimento, mandar um campo que não está no `$fillable` passa a
lançar exceção. É como você descobre, na sua máquina, que o formulário está
enviando um campo que o model ignora — em vez de descobrir pela ausência do
dado, três semanas depois.

## Casts: o tipo certo dos dois lados

O banco guarda texto, número e data. O seu código quer enums e objetos de
valor. O `casts()` é a tradução, nos dois sentidos:

```php title="app/Models/Exemplar.php" numbered
protected function casts(): array
{
    return [
        'estado' => StatusExemplar::class,
        'adquirido_em' => 'immutable_date',
    ];
}
```

```php
$exemplar = Exemplar::find(1);

$exemplar->estado;              // StatusExemplar::Bom
$exemplar->estado->rotulo();    // 'Disponível'
$exemplar->adquirido_em;        // DateTimeImmutable
```

A coluna continua sendo `VARCHAR(20)` com `'bom'` dentro. O que muda é que
nenhum ponto do seu código volta a comparar string solta — a lição do
capítulo @cap:enums-datas-e-valores passa a valer também na fronteira do
banco.

Para o `Dinheiro`, que não é enum nem data, a conversão é uma classe:

```php title="app/Casts/DinheiroCast.php" numbered
<?php

declare(strict_types=1);

namespace App\Casts;

use App\Emprestimos\Dinheiro;
use Illuminate\Contracts\Database\Eloquent\CastsAttributes;

class DinheiroCast implements CastsAttributes
{
    public function get($model, $chave, $valor, $atributos): ?Dinheiro
    {
        return $valor === null
            ? null
            : Dinheiro::emCentavos((int) $valor);
    }

    public function set($model, $chave, $valor, $atributos): ?int
    {
        return $valor?->centavos;
    }
}
```

```php
'multa_em_centavos' => DinheiroCast::class,
```

Agora `$emprestimo->multa_em_centavos` devolve um `Dinheiro`, com
`formatado()` e `mais()` — e a soma com um inteiro de dias, que o capítulo
@cap:enums-datas-e-valores fechou, continua fechada depois de passar pelo
banco.

## Accessor: valor calculado com cara de coluna

```php title="app/Models/Emprestimo.php" numbered
use Illuminate\Database\Eloquent\Casts\Attribute;

protected function diasDeAtraso(): Attribute
{
    return Attribute::make(
        get: fn (): int => max(
            0,
            $this->devolver_ate->diffInDays(now(), absolute: false),
        ),
    );
}
```

```php
$emprestimo->dias_de_atraso;   // 3
```

Parece coluna e não é: é calculado a cada leitura. Vale a pena quando o
valor é derivado de outros que já estão na tabela — e é exatamente a razão
de não existir uma coluna `dias_de_atraso`, pelo motivo do capítulo
@cap:duas-tabelas-conversando: número calculado não diverge da realidade.

## Scope: a consulta que ganha nome

```php title="app/Models/Emprestimo.php" numbered
use Illuminate\Database\Eloquent\Builder;

public function scopeEmAberto(Builder $q): void
{
    $q->whereNull('devolvido_em');
}

public function scopeVencidos(Builder $q): void
{
    $q->whereDate('devolver_ate', '<', now());
}
```

```php
Emprestimo::emAberto()->vencidos()->count();
```

```sql
SELECT COUNT(*) FROM emprestimos
WHERE devolvido_em IS NULL AND date(devolver_ate) < ?
```

O prefixo `scope` some na chamada, e os dois se combinam em qualquer ordem.

O ganho é o de sempre: a definição de "em aberto" passa a morar num lugar
só. No dia em que empréstimo cancelado também contar como fechado, a
mudança é uma linha — e não uma busca por `whereNull('devolvido_em')` em
dezessete arquivos.

## Ver o SQL antes de confiar

```php
Livro::where('assunto', 'infantil')->orderBy('titulo')->toSql();
```

```text
select * from `livros` where `assunto` = ? order by `titulo` asc
```

Para ver tudo que a requisição fez, com os valores e o tempo:

```php title="app/Providers/AppServiceProvider.php" numbered
if ($this->app->environment('local')) {
    DB::listen(function ($consulta): void {
        Log::debug($consulta->sql, [
            'valores' => $consulta->bindings,
            'ms' => $consulta->time,
        ]);
    });
}
```

:::key
Ligue isso no primeiro dia de qualquer projeto com ORM e olhe o log depois
de abrir três telas.

É a forma mais rápida de descobrir que a listagem de empréstimos está
fazendo duzentas e uma consultas — e esse número tem nome, tem causa
conhecida e é o assunto do próximo capítulo.
:::

## Model gigante: os sinais

O model começa com seis linhas e, se ninguém disser nada, chega a
trezentas. Três sinais de que isso aconteceu:

**Ele tem método que não fala com o banco.** Cálculo de multa, regra de
limite, decisão de prazo. Nada disso precisa de tabela para existir, e tudo
isso passa a precisar quando mora ali.

**Ele importa coisas que não são dados.** Um model que usa `Mail`, `Http` ou
`Storage` deixou de representar uma linha e virou um processo.

**Ele tem um método que você não consegue testar sem banco.** Este é o
sinal mais confiável, porque é verificável: se para conferir a regra da
multa você precisa inserir um empréstimo, a regra está no lugar errado.

A saída não é quebrar o model em cinco. É **tirar de lá o que não é
persistência**: a regra vai para o serviço ou para o objeto de valor, e o
model fica com colunas, casts, escopos e relações.

:::note Na sua carreira
"Model gordo ou controller gordo?" é uma discussão sem fim, e ela é a
pergunta errada. As duas respostas juntam duas coisas que mudam por motivos
diferentes: a forma de guardar e a regra do negócio.

O teste que resolve, e que você pode aplicar em qualquer projeto: **se a
Casa Amarela trocasse o MySQL por outra coisa, quanto do código precisaria
mudar?** Tudo que precisasse mudar é persistência. O resto é regra, e regra
não devia estar num arquivo que só existe por causa de uma tabela.

Não é um argumento sobre pureza: é sobre onde o teste fica barato.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/
    Models/
      Livro.php        # $table, $fillable
      Exemplar.php     # cast do enum
      Leitor.php       # $fillable sem perfil
      Emprestimo.php   # scopes, accessor, cast de Dinheiro
    Casts/
      DinheiroCast.php
    Providers/
      AppServiceProvider.php  # DB::listen e a proteção de atributos
:::

:::summary
- Todo método do Eloquent produz uma consulta, e ela é preparada.
- O pluralizador fala inglês: declare `$table` em projeto português.
- Active Record põe registro e comportamento no mesmo objeto — cômodo para
  persistir, caro para testar regra.
- `find` devolve `null`; `findOrFail` lança e vira `404`.
- `all()` traz a tabela inteira para a memória.
- `$fillable` é a lista do que o mundo de fora pode preencher;
  `$guarded = []` é escalada de privilégio esperando alguém curioso.
- `preventSilentlyDiscardingAttributes` transforma descarte em erro fora de
  produção.
- Casts convertem nos dois sentidos: enum, data imutável e objeto de valor.
- Accessor é valor calculado; scope é consulta com nome, e os dois moram num
  lugar só.
- `toSql()` e `DB::listen` mostram o que foi realmente executado.
- Model que tem regra sem banco, que chama serviço externo ou que não se
  testa sem tabela deixou de ser model.
:::

:::checkpoint
Você escreve consultas com Eloquent e mostra o SQL correspondente, protege o
cadastro com `$fillable`, converte enum e objeto de valor com casts, dá nome
a uma consulta com scope, e reconhece pelos três sinais quando a regra vazou
para dentro do model.
:::

:::exercise level=1
Escreva o SQL que cada chamada produz:

```php
Livro::where('ano', '>=', 2000)->count();
Exemplar::where('estado', 'bom')->pluck('tombo');
Leitor::orderBy('nome')->paginate(20);
Emprestimo::whereNull('devolvido_em')->latest()->first();
```

:::answer
```sql
SELECT COUNT(*) FROM livros WHERE ano >= ?
```

```sql
SELECT tombo FROM exemplares WHERE estado = ?
```

```sql
SELECT COUNT(*) FROM leitores;
SELECT * FROM leitores ORDER BY nome ASC LIMIT 20 OFFSET 0
```

```sql
SELECT * FROM emprestimos
WHERE devolvido_em IS NULL
ORDER BY created_at DESC LIMIT 1
```

Três observações que separam quem leu de quem entendeu.

O `pluck` traz **só a coluna pedida**, não a linha inteira — é a diferença
entre trazer oito mil linhas completas e trazer oito mil números.

O `paginate` faz **duas** consultas: uma conta o total, para saber quantas
páginas existem, e outra traz a página. É a causa mais comum de uma
listagem lenta em tabela grande, e a razão de existir o `simplePaginate`,
que dispensa a contagem.

E o `latest()` ordena por `created_at`, não por `id`. Num banco em que os
registros foram importados fora de ordem, os dois resultados diferem.
:::

:::exercise level=2
O model `Leitor` tem `$guarded = []` e a tabela tem as colunas `nome`,
`documento`, `telefone`, `perfil` e `bloqueado_em`.

Corrija o model e escreva o que muda no controller de cadastro público e no
controller da tela da Vera, que **precisa** poder mudar o perfil.

:::answer
```php title="app/Models/Leitor.php" numbered
class Leitor extends Model
{
    protected $table = 'leitores';

    protected $fillable = ['nome', 'documento', 'telefone'];

    protected function casts(): array
    {
        return ['bloqueado_em' => 'immutable_datetime'];
    }
}
```

O cadastro público não muda **uma linha** — e é esse o ponto. Ele já fazia
`Leitor::create($dados)`, e agora os campos a mais são descartados.

A tela da Vera não usa atribuição em massa para o perfil. Ela atribui
direto, o que ignora o `$fillable` de propósito:

```php
$leitor->perfil = $request->enum('perfil', Perfil::class);
$leitor->save();
```

Isso parece contornar a proteção e é exatamente o desenho correto: o
`$fillable` protege contra **o que vem de fora em bloco**. A atribuição
direta é uma decisão escrita no código, num controller que só quem tem a
permissão da Vera alcança.

`bloqueado_em` fica fora dos dois: ele muda por uma ação com nome — bloquear
um leitor — e não por formulário.
:::

:::exercise level=3
Este model chegou para revisão. Ele funciona.

```php
class Emprestimo extends Model
{
    protected $guarded = [];

    public function calcularMulta(): float
    {
        $dias = (strtotime('now')
              - strtotime($this->devolver_ate)) / 86400;

        if ($dias <= 0) {
            return 0;
        }

        $valor = $dias * 0.8;

        if ($this->leitor->perfil === 'estudante') {
            $valor = $valor / 2;
        }

        Mail::to($this->leitor->email)
            ->send(new AvisoDeMulta($valor));

        return $valor;
    }
}
```

Aponte os problemas por categoria — segurança, correção, desenho — e diga
onde cada pedaço deveria morar.

:::answer
**Segurança.** `$guarded = []` de novo, agora numa tabela que tem
`multa_em_centavos` e `devolvido_em`. Um cliente poderia registrar um
empréstimo já devolvido, sem multa.

**Correção.** Três defeitos, todos já vistos:

A diferença de datas em segundos dividida por 86.400 ignora fuso e os dias
de mudança de horário, e devolve `float` com casas decimais.

O valor em `float` acumula erro a cada soma — a conta é em centavos.

E `0.8` está solto, divergindo de `config/biblioteca.php`, que existe desde
o capítulo @cap:configuracao-ambiente-e-artisan.

**Desenho.** Dois problemas, e o segundo é grave.

O cálculo não precisa de banco para existir. Ele é regra, e está num arquivo
que só existe por causa de uma tabela — então testar "meia multa para
estudante" exige inserir empréstimo, leitor e exemplar.

E o método **envia e-mail**. Um método chamado `calcularMulta` que manda
mensagem para o leitor é uma surpresa: qualquer relatório que percorra
duzentos empréstimos para somar multas acabou de disparar duzentos e-mails.

**Onde cada pedaço vai.**

A conta de dias e o valor vão para um serviço — `CalculadoraDeMultas` — que
recebe as datas e a configuração e devolve `Dinheiro`. Ele se testa sem
banco.

A regra do estudante vai junto, porque é regra de negócio, e vira um caso de
teste explícito.

O envio do aviso sai daqui inteiro. Ele é uma consequência de um
acontecimento — a multa foi registrada —, não parte de calcular um número.

E o model fica com `$fillable`, os casts, os scopes e as relações. Umas
quinze linhas.
:::
