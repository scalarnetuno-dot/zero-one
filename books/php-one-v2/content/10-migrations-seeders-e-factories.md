---
title: "Migrations, seeders e factories"
number: 10
slug: migrations-seeders-e-factories
part: p3
kicker: "Onze e quarenta de uma quinta-feira. O terminal escreveu Dropping all tables e ele leu o endereço do banco na linha de cima."
goal: >-
  Versionar o esquema do banco em arquivos que contam a história das
  mudanças, alterar coluna sem derrubar a aplicação, e ter dados de
  desenvolvimento que qualquer pessoa da equipe consegue reproduzir.
---

:::story Dropping all tables
Dedé ia recriar o banco de homologação para testar a migração do acervo do
zero. Rodou o comando de sempre.

```text
$ php artisan migrate:fresh --seed

  Dropping all tables ................................ 214ms DONE
```

Ele olhou a linha acima da saída enquanto ela rolava. O terminal aberto era
o da sessão da manhã, aquela em que ele tinha entrado no servidor para
conferir uma coisa.

```text
DB_HOST=db.casaamarela.org.br
```

Ficou uns dois segundos sem falar.

— Tainá.

— Oi.

— Quanto tempo de backup a gente tem?

Ela procurou. Rotina diária, três da manhã.

— De ontem, às três.

— Então perdemos a manhã.

— A manhã e os oitocentos exemplares que a Vera catalogou ontem à tarde.
:::

## Migration não é backup

Uma migration descreve **a estrutura**: quais tabelas existem, com quais
colunas e quais restrições. Ela não guarda nem uma linha de dado.

Isso parece óbvio e é a confusão mais cara que existe, porque um comando com
nome amigável — `migrate:fresh` — apaga tudo e recria o esqueleto vazio, e
sai do jeito que entrou: sem erro nenhum.

:::key
As migrations recriam o **banco**. O backup recria o **sistema**.

São duas garantias diferentes, e a segunda é a única que responde por uma
quinta-feira de manhã.
:::

:::art caption="O comando era o de sempre. O terminal era o de produção."
src="o-comando-era-o-de-sempre-o-terminal-era-o-de-producao.png"
Charge editorial minimalista em fundo branco: um desenvolvedor de trinta
e poucos anos, de moletom, congelado diante do notebook, a mão ainda no
teclado, enquanto a tela mostra "Dropping all tables ... DONE" com um
visto verde. Atrás do notebook, uma estante de biblioteca desenhada em
traço fino se esvazia: os livros se desfazem em pontilhado, da prateleira
de cima para baixo. Ao lado, uma estagiária olha para um relógio de
parede marcando 3h, com uma etiqueta "backup". Poucos elementos, humor seco, estética de revista de tecnologia.
:::

## O esquema vira arquivo

```text
$ php artisan make:migration create_livros_table
```

```text
   INFO  Migration [database/migrations/
   2026_01_14_103211_create_livros_table.php] created successfully.
```

O nome começa com a data e a hora, e é isso que dá a **ordem**. A tabela de
exemplares precisa existir depois da de livros, porque aponta para ela — e
quem garante isso é o carimbo no nome do arquivo.

```php title="..._create_livros_table.php" numbered
<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('livros', function (Blueprint $t) {
            $t->id();
            $t->string('titulo', 200);
            $t->string('autor', 150);
            $t->char('isbn', 13)->nullable()->unique();
            $t->string('assunto', 40);
            $t->smallInteger('ano')->nullable();
            $t->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('livros');
    }
};
```

É o `CREATE TABLE` do capítulo @cap:duas-tabelas-conversando, escrito em
PHP. Lado a lado:

```sql
CREATE TABLE livros (
  id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  titulo  VARCHAR(200) NOT NULL,
  autor   VARCHAR(150) NOT NULL,
  isbn    CHAR(13)     NULL,
  assunto VARCHAR(40)  NOT NULL,
  ano     SMALLINT     NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  UNIQUE KEY livros_isbn_unique (isbn)
) ENGINE=InnoDB;
```

`$t->id()` é a chave primária com incremento. `$t->timestamps()` cria as
duas colunas de data que o esquema escrito à mão não tinha — e elas entram
agora por duas razões: o Eloquent as mantém sozinho, e "quando este exemplar
entrou no acervo" é uma pergunta que a Vera vai fazer.

A chave estrangeira cabe numa linha:

```php
$t->foreignId('livro_id')->constrained();
```

O nome da coluna termina em `_id`, então o Laravel deduz a tabela `livros` e
a coluna `id`. É convenção fazendo o trabalho — e quando o nome não seguir o
padrão, `constrained('livros')` diz explicitamente.

## O estado do banco mora numa tabela

```text
$ php artisan migrate
```

```text
   INFO  Running migrations.

  2026_01_14_103211_create_livros_table .......... 34ms DONE
  2026_01_14_103245_create_exemplares_table ...... 41ms DONE
  2026_01_14_103302_create_leitores_table ........ 28ms DONE
  2026_01_14_103330_create_emprestimos_table ..... 52ms DONE
```

O Laravel guarda o que já rodou numa tabela chamada `migrations`:

```text
mysql> SELECT * FROM migrations;
+----+------------------------------------+-------+
| id | migration                          | batch |
+----+------------------------------------+-------+
|  1 | 2026_01_14_103211_create_livros... |     1 |
|  2 | 2026_01_14_103245_create_exempl... |     1 |
+----+------------------------------------+-------+
```

É por isso que rodar `migrate` duas vezes não faz nada na segunda: ele
compara a pasta com a tabela e roda só o que falta.

A coluna `batch` agrupa o que subiu junto, e é o que o `rollback` usa —
`migrate:rollback` desfaz o último lote inteiro, não a última migration.

| Comando | O que faz |
|---|---|
| `migrate` | roda o que ainda não rodou |
| `migrate:status` | mostra o que rodou e o que falta |
| `migrate:rollback` | desfaz o último lote |
| `migrate:fresh` | **apaga todas as tabelas** e roda tudo de novo |

Tabela: Os três primeiros são seguros em qualquer ambiente. O quarto é o da
história.

## `down()` honesto

Todo `up()` tem um `down()`, e a tentação é preenchê-lo por obrigação.

```php
public function down(): void
{
    Schema::table('livros', function (Blueprint $t) {
        $t->dropColumn('assunto');
    });
}
```

Isso desfaz a estrutura e **apaga os dados daquela coluna**. Se a migration
já rodou em produção, o `down` é uma perda de dados com cara de
arrependimento.

:::pitfall
Existem migrations que não têm volta honesta: as que juntam duas colunas em
uma, as que convertem formato, as que apagam registro duplicado.

Para essas, o `down` certo é recusar:

```php
public function down(): void
{
    throw new RuntimeException(
        'Esta migration não pode ser desfeita: restaure o backup.'
    );
}
```

É mais honesto que um `down` que finge. Quem rodar o `rollback` recebe a
verdade em vez de um banco que parece voltado e perdeu metade de uma coluna.
:::

## Alterar coluna sem derrubar a aplicação

A associação pediu que o assunto do livro deixasse de ser texto livre e
passasse a apontar para uma tabela de assuntos.

A tentação é uma migration que troca a coluna. O problema é o intervalo: se
a aplicação está no ar, existe um momento em que o código antigo procura a
coluna velha num banco que já mudou.

O caminho que não derruba tem duas etapas, e leva dois deploys.

**Expandir.** Uma migration acrescenta a coluna nova, sem mexer na velha. O
código passa a **escrever nas duas** e a ler da nova quando ela estiver
preenchida. Nada quebra, porque nada foi removido.

**Contrair.** Depois que todo o dado foi convertido e nenhum código lê mais
a coluna velha, uma segunda migration a remove.

| Etapa | Migration | Código |
|---|---|---|
| 1 | cria `assunto_id` | escreve nas duas, lê a nova |
| 2 | — | converte o histórico |
| 3 | remove `assunto` | lê e escreve só a nova |

Tabela: Três passos para o que parecia um. É o preço de não ter janela de
manutenção — e é o procedimento padrão em qualquer sistema que não pode
parar.

:::pitfall
Nunca edite uma migration que já rodou em produção.

Ela está registrada na tabela `migrations`, então o Laravel não vai rodá-la
de novo — e a sua máquina, onde você apagou o banco e recriou, fica com um
esquema diferente do de produção sem que nada avise.

A alteração de uma tabela existente é sempre uma migration **nova**.
:::

## Seeder: o dado que todo ambiente precisa

Existe dado que não é de teste: a lista de assuntos do acervo, o usuário
administrador inicial, os estados possíveis. Sem ele o sistema não funciona
em lugar nenhum.

```php title="database/seeders/AssuntoSeeder.php" numbered
<?php

declare(strict_types=1);

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class AssuntoSeeder extends Seeder
{
    public function run(): void
    {
        $assuntos = [
            'literatura', 'didatico', 'infantil',
            'referencia', 'historia', 'ciencias',
        ];

        foreach ($assuntos as $nome) {
            DB::table('assuntos')->updateOrInsert(['nome' => $nome]);
        }
    }
}
```

O `updateOrInsert` é a diferença entre um seeder que pode rodar duas vezes e
um que duplica tudo na segunda. Seeder de dado essencial precisa ser
repetível — ele vai rodar em todo deploy de ambiente novo, e mais de uma vez
na vida de alguém distraído.

## Factory: o dado de mentira que parece de verdade

Para desenvolver e testar, você precisa de acervo. Quatro mil livros
digitados à mão não é uma opção.

```php title="database/factories/LivroFactory.php" numbered
<?php

declare(strict_types=1);

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

class LivroFactory extends Factory
{
    public function definition(): array
    {
        return [
            'titulo' => fake()->sentence(3),
            'autor' => fake()->name(),
            'isbn' => fake()->unique()->isbn13(),
            'assunto' => fake()->randomElement([
                'literatura', 'didatico', 'infantil',
            ]),
            'ano' => fake()->numberBetween(1890, 2026),
        ];
    }

    public function infantil(): static
    {
        return $this->state(fn (): array => [
            'assunto' => 'infantil',
            'ano' => fake()->numberBetween(2000, 2026),
        ]);
    }
}
```

```php
Livro::factory()->count(200)->create();

Livro::factory()->infantil()->count(30)->create();

Livro::factory()->create(['titulo' => 'Dom Casmurro']);
```

O `infantil()` é um **estado**: uma variação nomeada do padrão. Ele existe
para que um teste sobre a regra de sete dias possa pedir exatamente o caso
de que precisa, sem montar o livro campo a campo.

Para os nomes saírem em português, uma linha no `.env`:

```text
APP_FAKER_LOCALE=pt_BR
```

:::pitfall
Uma factory que só produz o caso feliz é uma armadilha lenta.

Se todo `Livro` gerado tem ISBN, ano e assunto preenchidos, nenhum teste vai
exercitar o livro antigo sem ISBN — que existe às centenas no acervo real da
Casa Amarela, porque o ISBN só passou a ser usado nos anos 1970.

A factory precisa refletir a **variedade** dos dados de verdade, não a
versão idealizada deles. Uma boa pergunta na hora de escrever: *qual é o
registro mais estranho que existe hoje em produção?*
:::

## Quem roda migration em produção

A pergunta tem uma resposta técnica curta e uma resposta de processo, e a
segunda é a que importa.

A técnica: `php artisan migrate --force`. O `--force` existe porque, em
`production`, o comando pergunta antes — e num passo automatizado não há
ninguém para responder.

A de processo é uma lista:

1. **O comando roda no deploy**, não à mão. Mão erra de terminal.
2. **`migrate:fresh` não existe em produção.** A forma de garantir isso não
   é disciplina: é o usuário do banco de produção não ter permissão de
   apagar tabela.
3. **Backup antes**, e conferido — um backup que ninguém nunca restaurou não
   é um backup, é um arquivo.
4. **O terminal de produção tem cara diferente.** Prompt vermelho, nome do
   ambiente visível. Custa cinco minutos e resolve a categoria inteira de
   erro da história deste capítulo.

:::note Na sua carreira
Você vai apagar alguma coisa importante em algum momento. Praticamente todo
mundo que trabalha com sistema em produção por tempo suficiente tem uma
história dessas.

O que separa as pessoas não é ter ou não ter a história: é o que aconteceu
depois. Avisar na hora, com o horário exato do que foi perdido, é a diferença
entre uma manhã ruim e uma tarde catastrófica — porque a equipe consegue
parar o que estiver escrevendo por cima e restaurar com precisão.

Esconder por vinte minutos para "tentar resolver sozinho" é o que transforma
oitocentos exemplares em oitocentos exemplares mais tudo que foi gravado
enquanto ninguém sabia.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  database/
    migrations/
      ..._create_livros_table.php
      ..._create_exemplares_table.php
      ..._create_leitores_table.php
      ..._create_emprestimos_table.php
    seeders/
      DatabaseSeeder.php
      AssuntoSeeder.php
    factories/
      LivroFactory.php
      ExemplarFactory.php
      LeitorFactory.php
:::

:::summary
- Migration versiona estrutura, não dado; `migrate:fresh` apaga tudo e não
  reclama.
- O carimbo de data no nome do arquivo é o que define a ordem de execução.
- A tabela `migrations` registra o que já rodou, agrupado em lotes; o
  `rollback` desfaz um lote inteiro.
- `down` que finge desfazer é pior que `down` que recusa.
- Alteração de coluna em sistema no ar é feita em duas etapas: expandir e,
  depois, contrair.
- Nunca edite migration que já rodou em produção; a correção é uma migration
  nova.
- Seeder carrega dado essencial e precisa ser repetível.
- Factory gera dado de desenvolvimento, e precisa representar a variedade do
  banco real, não o caso feliz.
- Em produção, migration roda no deploy, com backup conferido e sem
  permissão de apagar tabela.
:::

:::checkpoint
Você cria o esquema por migration, sabe o que o `batch` da tabela
`migrations` controla, altera uma coluna sem derrubar a aplicação, e gera
acervo falso com estados que representam os casos difíceis.
:::

:::exercise level=1
Escreva a migration da tabela `exemplares`, com `tombo` único, `livro_id`
apontando para `livros` e `estado` com valor padrão.

Depois diga por que o `down()` dessa migration é honesto, ao contrário do
exemplo do capítulo.

:::answer
```php title="..._create_exemplares_table.php" numbered
public function up(): void
{
    Schema::create('exemplares', function (Blueprint $t) {
        $t->id();
        $t->foreignId('livro_id')->constrained();
        $t->unsignedInteger('tombo')->unique();
        $t->string('estado', 20)->default('bom');
        $t->timestamps();
    });
}

public function down(): void
{
    Schema::dropIfExists('exemplares');
}
```

O `down()` é honesto porque o `up()` **criou** a tabela. Desfazer a criação
de uma tabela é apagá-la, e nenhum dado existia antes dela — quem reverter
volta exatamente ao estado anterior.

O exemplo do capítulo era outro caso: `dropColumn('assunto')` numa tabela que
já existia. Ali o `down` não devolve o estado anterior, porque os valores da
coluna não estão em lugar nenhum.

A régua: **`down` de `create` é seguro; `down` de `alter` quase nunca é.**
:::

:::exercise level=2
A Vera pediu que o sistema guardasse, para cada exemplar, a data em que ele
entrou no acervo — informação que hoje está só na etiqueta.

A tabela tem oitocentos registros e o sistema está no ar. Escreva o plano
completo, com as migrations e o que o código faz em cada etapa.

:::answer
**Etapa 1 — expandir.** A coluna nasce aceitando nulo, porque os oitocentos
registros existentes não têm valor:

```php
Schema::table('exemplares', function (Blueprint $t) {
    $t->date('adquirido_em')->nullable()->after('estado');
});
```

O código passa a preencher a coluna em todo cadastro novo. A tela mostra a
data quando existe e "não informado" quando não existe. Nada quebra, e nada
foi perdido.

**Etapa 2 — preencher o histórico.** Aqui há uma decisão de produto, não
técnica: de onde vem a data dos oitocentos antigos?

Se a Vera tiver a informação nas fichas, ela digita ao longo das semanas. Se
não tiver, a alternativa é usar uma aproximação — a data de criação do
registro — e **registrar que é aproximada**, numa coluna a mais ou num
valor convencionado. Inventar um dado e apresentá-lo como exato é a origem
de um relatório errado daqui a dois anos.

**Etapa 3 — contrair.** Só se e quando a coluna deixar de poder ser nula:

```php
Schema::table('exemplares', function (Blueprint $t) {
    $t->date('adquirido_em')->nullable(false)->change();
});
```

E esta etapa tem uma condição de entrada verificável: `SELECT COUNT(*) FROM
exemplares WHERE adquirido_em IS NULL` precisa devolver zero. Rodar a
migration antes disso derruba o deploy.
:::

:::exercise level=3
Reescreva este seeder, apontando os quatro problemas:

```php
class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        DB::table('usuarios')->insert([
            'nome' => 'Administrador',
            'email' => 'admin@admin.com',
            'senha' => md5('123456'),
            'perfil' => 'admin',
        ]);

        Livro::factory()->count(5000)->create();

        DB::table('assuntos')->insert([
            ['nome' => 'literatura'],
            ['nome' => 'didatico'],
        ]);
    }
}
```

:::answer
**Um: a senha.** `md5('123456')` é o defeito do capítulo
@cap:conversao-automatica voltando pela porta dos fundos, agora escrito por
nós. Senha se guarda com `Hash::make()`, e a senha do administrador inicial
não fica no código: vem do ambiente, ou o usuário é criado por um comando
que a pede.

**Dois: dado de teste misturado com dado essencial.** Os cinco mil livros
falsos estão no mesmo lugar que os assuntos, que são reais. No dia em que
alguém rodar `db:seed` em produção para criar os assuntos, o acervo ganha
cinco mil títulos inventados.

Separar em dois seeders e chamar o de dados falsos só onde ele faz sentido:

```php
public function run(): void
{
    $this->call(AssuntoSeeder::class);

    if (app()->environment('local', 'testing')) {
        $this->call(AcervoFalsoSeeder::class);
    }
}
```

**Três: o `insert` não é repetível.** Rodar duas vezes duplica os assuntos —
e a segunda execução falha se houver índice único, deixando o seeder pela
metade. `updateOrInsert` resolve.

**Quatro: cinco mil registros um a um.** Cada `create()` da factory é um
`INSERT` separado. Cinco mil inserções levam minutos, e o seeder vira algo
que ninguém roda. A forma em lote (`->make()` mais uma inserção em blocos)
resolve, ao custo de não disparar eventos de model — que num dado falso não
importam.

E um quinto, que não estava na lista e vale dizer: `admin@admin.com` com
senha `123456` num seeder é uma credencial padrão. Elas têm o hábito de
sobreviver até produção, e são a primeira coisa que qualquer varredura
automática tenta.
:::
