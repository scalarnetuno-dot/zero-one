---
title: "Upload de arquivos"
number: 29
slug: upload-de-arquivos
part: p8
kicker: "A Vera fotografou trezentas capas com o celular novo. Metade não subiu. A outra metade subiu deitada."
goal: >-
  Receber arquivos grandes sem ser barrado por um limite que você não
  configurou, validar imagem pelo conteúdo e pelas dimensões, escolher entre
  disco privado e público, processar a imagem fora da requisição, trocar um
  arquivo sem deixar órfão, e testar tudo sem tocar no disco.
---

:::story Deitadas
Na primeira semana de abril, a Vera ganhou da associação um celular novo e
decidiu que o acervo teria capa. Ficou três tardes no depósito,
fotografando livro por livro em cima de uma cartolina branca.

Na quinta, abriu o painel e começou a subir. Da primeira à nonagésima,
todas deram a mesma mensagem:

```text
The capa failed to upload.
```

— Em inglês — disse ela à Tainá, pelo telefone. — E eu nem sei o que é
*failed*.

Na sexta, a Tainá passou as fotos pelo computador, que as diminuiu, e as
capas subiram. Todas. Deitadas.

— Deitadas como?

— Deitadas. *Vidas Secas* com o título de cima para baixo. *O Cortiço*
olhando para a esquerda. No celular estão em pé.

O Dedé abriu uma das fotos originais.

— Doze megabytes — disse ele. — O servidor aceita dois. E o celular não
gira a foto: ele grava deitada e anota num canto do arquivo "mostre em
pé". O navegador lê a anotação. O nosso código, não.

A Vera suspirou.

— Eu tirei trezentas.
:::

## Três limites antes do seu código

O capítulo @cap:requests-e-responses tratou da segurança do upload: nome e
extensão gerados do lado de cá, conteúdo conferido, pasta fora de
`public/`. Tudo isso acontece dentro do Laravel. A foto de doze megabytes
da Vera não chegou lá.

Entre o celular e o controller há três porteiros, e cada um recusa de um
jeito:

| Onde | Configuração | Padrão comum | O que o cliente vê |
|---|---|---|---|
| servidor web | `client_max_body_size` (nginx) | 1 MB | `413` em HTML, antes do PHP |
| PHP | `upload_max_filesize` | 2 MB | o arquivo chega com erro: *failed to upload* |
| PHP | `post_max_size` | 8 MB | o corpo inteiro é descartado: `413` do Laravel |

Tabela: Três limites, três sintomas. O da Vera foi o segundo: o PHP
recebeu o pedido, descartou o arquivo e avisou o Laravel.

O segundo e o terceiro moram no `php.ini`. O `post_max_size` precisa ser
**maior** que o `upload_max_filesize`, porque o corpo da requisição leva o
arquivo e os outros campos junto:

```ini title="/etc/php/8.3/fpm/conf.d/99-casa-amarela.ini"
upload_max_filesize = 12M
post_max_size = 14M
```

E o nginx precisa concordar com os dois:

```text title="/etc/nginx/sites-available/casa-amarela"
client_max_body_size 14m;
```

Esses números abrem a porta. Quem decide o que entra é a validação, que
devolve `422` com uma mensagem que o aplicativo sabe mostrar — em vez de
um `413` que ninguém sabe ler.

:::key
Configure os três porteiros com **folga**, e ponha o limite de verdade na
validação. O porteiro barra com uma página de erro genérica; a validação
barra com uma frase no campo certo, no idioma do cliente.
:::

## Validar a imagem pelo que ela é

O `'image'` do capítulo @cap:requests-e-responses confere que o arquivo é
uma imagem. Para capa de livro, a Casa Amarela precisa de mais: formato
que o navegador mostra, tamanho máximo, e resolução mínima — uma capa de
100×150 pixels vira um borrão na tela.

```php title="app/Http/Requests/CapaRequest.php" numbered
public function rules(): array
{
    return [
        'capa' => [
            'required',
            File::image()
                ->types(['jpg', 'png', 'webp'])
                ->max('10mb')
                ->dimensions(
                    Rule::dimensions()->minWidth(300)->minHeight(400),
                ),
        ],
    ];
}
```

`File` é a regra fluente de arquivo do Laravel, em
`Illuminate\Validation\Rules\File`. Cada método acrescenta uma condição, e a
resposta traz uma mensagem para cada uma que falhar:

```text
{"capa":["The capa field has invalid image dimensions."]}

{"capa":["The capa field must not be greater than 10000
kilobytes."]}
```

Repare no "10000". O `'10mb'` é contado em múltiplos de mil — dez mil
kilobytes, não 10.240. A diferença é pequena e aparece exatamente no
arquivo de 10,1 MB que alguém jura ter menos de dez.

As mensagens estão em inglês porque o projeto ainda não tem tradução. O
capítulo @cap:mail-e-notificacoes cuida disso, e da mesma causa em outro
lugar.

:::pitfall
A foto do iPhone chega, às vezes, em HEIC — um formato que o `types()`
acima recusa e que a extensão de imagem do PHP não lê. O navegador do
próprio iPhone costuma converter para JPEG no upload; o aplicativo, não
necessariamente. Combine com o Kauã: o aplicativo converte antes de
enviar, e a API aceita só o que sabe processar.
:::

## Disco privado, disco público

O Laravel guarda arquivos em **discos**, declarados em
`config/filesystems.php`. Um projeto novo vem com três:

| Disco | Onde grava | Quem lê |
|---|---|---|
| `local` | `storage/app/private` | só o código |
| `public` | `storage/app/public` | o navegador, via link |
| `s3` | um serviço de arquivos na nuvem | depende da configuração |

Tabela: O disco padrão é o `local`, e ele é privado de propósito.

O `public` fica visível na web por um atalho que um comando cria uma vez
por servidor:

```text
$ php artisan storage:link
```

Ele liga `public/storage` a `storage/app/public`. Uma capa gravada em
`capas/x.webp` no disco `public` passa a responder em `/storage/capas/
x.webp` — e é o `url()` do disco que monta esse endereço:

```php title="app/Http/Resources/LivroResource.php" numbered
'capa_url' => $this->capa
    ? Storage::disk('public')->url($this->capa)
    : null,
```

A decisão é simples de dizer: **o que é para qualquer um ver vai para o
`public`; o resto, para o `local`**. A capa de *Vidas Secas* é pública. A
foto original da Vera, de doze megabytes, não precisa ser — e o termo de
doação assinado pelo Seu Juvenal, com CPF, não pode ser.

Um arquivo privado sai por uma rota, depois da policy:

```php title="app/Http/Controllers/TermoDeDoacaoController.php" numbered
public function __invoke(Doacao $doacao)
{
    $this->authorize('view', $doacao);

    return Storage::disk('local')->download(
        $doacao->termo,
        "termo-{$doacao->id}.pdf",
    );
}
```

A troca de disco é uma linha de `.env`. Quando o acervo de capas crescer
além do disco do servidor, `FILESYSTEM_DISK` e as credenciais do `s3`
mudam, e o código acima continua o mesmo — é o `Storage` fazendo pelo
upload o que o `DB` fez pelo banco.

## Processar depois de responder

A foto da Vera precisa de três coisas antes de virar capa: ficar em pé,
ficar menor e mudar para um formato leve. Nenhuma delas precisa acontecer
enquanto o celular espera.

O controller guarda o original no disco privado e entrega o resto à fila:

```php title="app/Http/Controllers/CapaController.php" numbered
public function __invoke(CapaRequest $request, Livro $livro)
{
    $original = $request->file('capa')
        ->store('capas/originais', 'local');

    PrepararCapa::dispatch($livro->id, $original);

    return response()->json(['situacao' => 'processando'], 202);
}
```

`202 Accepted` é o status do capítulo @cap:o-que-e-uma-api-rest para "recebi
e ainda não terminei". O aplicativo mostra a capa quando o `capa_url` do
livro deixar de ser `null`.

E o job faz o trabalho com a extensão GD, que acompanha a maior parte das
instalações do PHP:

```php title="app/Jobs/PrepararCapa.php" numbered
public function handle(): void
{
    $livro = Livro::find($this->livroId);
    if ($livro === null) {
        return;
    }

    $caminho = Storage::disk('local')->path($this->original);

    $imagem = imagecreatefromstring(file_get_contents($caminho));
    $imagem = $this->endireitar($imagem, $caminho);
    $imagem = imagescale($imagem, 600);

    $destino = 'capas/' . Str::uuid() . '.webp';
    Storage::disk('public')->put($destino, $this->emWebp($imagem));

    $this->trocarCapa($livro, $destino);
    Storage::disk('local')->delete($this->original);
}
```

`imagescale($imagem, 600)` reduz a largura para 600 pixels e calcula a
altura na proporção. Uma foto de 3000×4000 vira 600×800, e doze megabytes
viram uns sessenta kilobytes em WebP.

A anotação "mostre em pé" se chama **EXIF**: dados que a câmera grava
dentro do JPEG, entre eles a orientação. Ler e aplicar:

```php title="app/Jobs/PrepararCapa.php (continuação)" numbered
private function endireitar(GdImage $imagem, string $caminho): GdImage
{
    if (mime_content_type($caminho) !== 'image/jpeg') {
        return $imagem;
    }

    $exif = exif_read_data($caminho) ?: [];
    $graus = match ($exif['Orientation'] ?? 1) {
        3 => 180,
        6 => -90,
        8 => 90,
        default => 0,
    };

    return $graus === 0 ? $imagem : imagerotate($imagem, $graus, 0);
}

private function emWebp(GdImage $imagem): string
{
    ob_start();
    imagewebp($imagem, null, 80);
    return (string) ob_get_clean();
}
```

O `if` do começo não é enfeite. PNG e WebP não têm EXIF, e `exif_read_data`
num PNG emite um *warning* — que, no Laravel, vira exceção, como o
`bootstrap.php` do capítulo @cap:erros-e-debug fazia. Sem o `if`, toda capa
em PNG falharia na fila.

`imagewebp` escreve direto na saída; `ob_start` e `ob_get_clean` capturam
essa saída numa string, que o `Storage` grava onde o disco mandar.

:::note
Em projetos com muita imagem, uma biblioteca como a Intervention Image
esconde o GD atrás de uma interface mais curta — e resolve a orientação
com um método. Para uma capa por livro, as vinte linhas acima bastam, e
você sabe o que cada uma faz.
:::

## Trocar sem deixar órfão

Quando a Vera refaz a foto de *O Cortiço*, a capa nova entra e a antiga
precisa sair. A ordem importa, porque banco e disco não participam da
mesma transação:

```php title="app/Jobs/PrepararCapa.php (continuação)" numbered
private function trocarCapa(Livro $livro, string $nova): void
{
    $antiga = $livro->capa;

    try {
        $livro->update(['capa' => $nova]);
    } catch (Throwable $e) {
        Storage::disk('public')->delete($nova);
        throw $e;
    }

    if ($antiga !== null) {
        Storage::disk('public')->delete($antiga);
    }
}
```

**Primeiro o arquivo novo, depois o banco, por último o arquivo velho.**
Se o `update` falhar, o arquivo novo sai e o livro continua com a capa
antiga, inteira. Se o `delete` do velho falhar, sobra um arquivo sem dono
— um desperdício de espaço, e não um livro sem capa.

É o "grave num temporário e renomeie no fim" do capítulo @cap:manipulacao-de-arquivos,
agora com um banco no meio: em nenhum instante o sistema mostra uma capa
pela metade ou aponta para um arquivo que não existe.

:::key
Quando uma operação mexe em banco e em disco, ordene os passos para que a
falha em qualquer um deixe **sobra**, nunca **falta**. Sobra se limpa
depois, com um comando agendado que compara o disco com a tabela. Falta é
a capa quebrada na tela do leitor.
:::

## Testar sem disco e sem fila

`Storage::fake` troca um disco por uma pasta temporária, que some no fim
do teste. `UploadedFile::fake()->image()` fabrica uma imagem de verdade,
com as dimensões pedidas:

```php title="tests/Feature/CapaTest.php" numbered
test('aceita a capa e deixa o trabalho para a fila', function () {
    Storage::fake('local');
    Queue::fake();
    $livro = Livro::factory()->create();

    $this->actingAs(Usuario::factory()->atendente()->create())
        ->postJson("/api/livros/{$livro->id}/capa", [
            'capa' => UploadedFile::fake()
                ->image('capa.jpg', 800, 1200),
        ])
        ->assertStatus(202);

    Queue::assertPushed(PrepararCapa::class);
    expect(Storage::disk('local')->allFiles('capas/originais'))
        ->toHaveCount(1);
});

test('prepara a capa em webp com 600 de largura', function () {
    Storage::fake('local');
    Storage::fake('public');
    $livro = Livro::factory()->create();
    $original = UploadedFile::fake()->image('capa.jpg', 800, 1200)
        ->store('capas/originais', 'local');

    (new PrepararCapa($livro->id, $original))->handle();

    $capa = Storage::disk('public')->get($livro->fresh()->capa);
    [$largura, $altura] = getimagesizefromstring($capa);

    expect([$largura, $altura])->toBe([600, 900]);
    Storage::disk('local')->assertMissing($original);
});
```

O primeiro teste prova o contrato: `202`, original guardado, job na fila.
O segundo chama o `handle` direto e prova o trabalho: largura 600, altura
na proporção, original apagado. Nenhum dos dois grava nada no disco de
verdade, e os dois rodam em menos de um segundo.

`UploadedFile::fake()->image()` precisa da extensão GD no PHP que roda os
testes — a mesma que o job usa. Se a esteira do capítulo
@cap:git-ci-e-deploy não a tiver, o teste falha com uma mensagem que diz
isso.

:::note Na sua carreira
Arquivo enviado por usuário é o dado que mais cresce e o que menos gente
lembra de copiar. O backup do banco roda toda noite; a pasta
`storage/app` fica de fora porque "é só imagem".

No dia em que o disco do servidor morrer, as quatro mil capas da Vera
somem, e cada uma custou uma foto em cima de uma cartolina. Pergunte, no
mesmo dia em que o primeiro upload for para produção: **quem copia
`storage/`, e para onde?** Se a resposta for o `s3`, a pergunta vira
"quem copia o `s3`".
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/
    Http/Controllers/
      CapaController.php          # 202: guarda e enfileira
      TermoDeDoacaoController.php # download privado, com policy
    Http/Requests/CapaRequest.php # tipo, tamanho, dimensões
    Jobs/PrepararCapa.php         # EXIF, 600px, WebP, troca
  storage/app/
    private/capas/originais/      # o que a Vera enviou
    public/capas/                 # o que o leitor vê
:::

:::summary
- Servidor web, `upload_max_filesize` e `post_max_size` barram antes do
  Laravel. Configure com folga; o limite real fica na validação.
- `File::image()->types()->max()->dimensions()` valida pelo conteúdo;
  `'10mb'` são dez mil kilobytes.
- Disco `local` é privado; `public` aparece na web pelo `storage:link`.
  Arquivo sensível sai por rota, depois da policy.
- Guarde o original, responda `202` e processe na fila.
- Foto de celular traz a orientação no EXIF; aplique-a antes de reduzir.
- Troque arquivos na ordem novo → banco → velho: a falha deixa sobra,
  nunca falta.
- `Storage::fake` e `UploadedFile::fake()->image()` testam sem disco.
:::

:::checkpoint
Você configura os limites de upload do servidor ao Laravel, valida imagem
por tipo, tamanho e dimensão, escolhe entre disco privado e público,
processa a imagem numa fila, troca arquivos sem deixar o livro sem capa, e
testa o caminho inteiro sem tocar no disco.
:::

:::exercise level=1
Para cada sintoma, diga qual porteiro barrou e o que mudar:

1. O aplicativo recebe uma página HTML com "413 Request Entity Too Large".
2. A API responde `422` com *"The capa failed to upload."*.
3. A API responde `413` em JSON, e os outros campos do formulário também
   sumiram.

:::answer
1. O nginx, com `client_max_body_size`. O PHP nem viu o pedido.
2. O PHP, com `upload_max_filesize`. O corpo chegou, o arquivo foi
   descartado, e o Laravel avisou que ele não subiu.
3. O PHP, com `post_max_size`. O corpo inteiro foi descartado — por isso
   os outros campos sumiram —, e o Laravel respondeu com
   `PostTooLargeException`.
:::

:::exercise level=2
O termo de doação é um PDF de até 5 MB. Escreva a regra de validação e
diga em que disco ele fica e por quê. Depois, escreva o teste que prova
que um leitor comum recebe `403` ao tentar baixá-lo.

:::answer
```php
'termo' => ['required', File::types(['pdf'])->max('5mb')],
```

Disco `local`: o termo tem nome, endereço e CPF. Ele sai só pela rota do
`TermoDeDoacaoController`, depois da policy.

```php
test('leitor comum não baixa termo de doação', function () {
    Storage::fake('local');
    $doacao = Doacao::factory()->create([
        'termo' => UploadedFile::fake()
            ->create('termo.pdf', 100, 'application/pdf')
            ->store('termos', 'local'),
    ]);

    $this->actingAs(Usuario::factory()->leitor()->create())
        ->get("/api/doacoes/{$doacao->id}/termo")
        ->assertForbidden();
});
```
:::

:::exercise level=3
Seis meses depois, o disco do servidor está com 70% ocupado, e a pasta
`storage/app/public/capas` tem 11.000 arquivos para 4.000 livros. Explique
de onde vieram os 7.000 a mais, e desenhe o comando agendado que os limpa
sem nenhum risco de apagar uma capa em uso.

:::answer
Vieram das sobras que a ordem novo → banco → velho aceita: `delete` do
arquivo antigo que falhou, jobs que gravaram a capa e caíram antes do
`update`, capas trocadas várias vezes durante testes da Vera.

O comando, `capas:limpar`, agendado uma vez por semana:

1. Lista os arquivos de `capas/` no disco `public`.
2. Lista os valores da coluna `capa` de `livros`.
3. Apaga os arquivos que estão no primeiro conjunto e não no segundo — e
   **só os modificados há mais de um dia**, para não apagar a capa que um
   job acabou de gravar e ainda não registrou no banco.
4. Registra no log quantos apagou.

A regra do passo 3 é o que torna o comando seguro: ele nunca disputa com
um `PrepararCapa` em andamento. Antes de rodar de verdade, uma opção
`--simular` que só lista o que seria apagado é o tipo de cuidado que a
Vera nunca vai saber que existiu.
:::
