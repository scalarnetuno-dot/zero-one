---
title: "Blade, quando a tela ainda é a resposta"
number: 32
slug: blade
part: p6
kicker: "A Vera não quer aplicativo. Ela quer um campo de busca e um botão, como o do Sistema, que funcionava."
goal: >-
  Entregar o painel que a bibliotecária usa no balcão — listagem,
  formulário e ação — entendendo o escape automático, o token de
  formulário e onde fica o limite entre Blade e front-end de verdade.
---

:::story Um campo e um botão
Dr. Aurélio apresentou o aplicativo do leitor na reunião de terça, com as
telas no projetor, e perguntou à Vera o que ela achava.

— Bonito. Onde é que eu empresto?

— O empréstimo é aqui, ó. O leitor abre no celular dele e...

— Não. Eu. No balcão. Com a pessoa na minha frente e o livro na mão.

Silêncio de quem não tinha pensado nisso.

— A gente pode fazer uma tela.

— É o que eu uso hoje — disse Vera. — Um campo, eu digito o número do
tombo, aperta o botão, empresta. Leva quatro segundos.

— A do Sistema?

— A do Sistema. Aquela funcionava.
:::

## Nem tudo é API

Um aplicativo faz sentido para quem consulta o acervo do sofá. Não faz
nenhum para quem está em pé, atrás de um balcão, com fila.

O painel da Vera tem três telas, e o resto do livro continua sendo API. Esta
é a única parte web, e ela existe porque o cliente real do sistema trabalha
num computador que já está ligado na mesa.

:::key
A pergunta que decide entre tela e API não é "o que é mais moderno?". É:
**quem usa isso, em que situação?**

Fila no balcão, quatro segundos por atendimento e teclado pede formulário. O
leitor no ônibus, querendo saber se o livro voltou, pede aplicativo. O mesmo
sistema atende os dois, e nenhum dos dois atende os dois.
:::

## Blade é PHP com menos cerimônia

Uma view é um arquivo em `resources/views/` com a extensão `.blade.php`. O
controller monta os dados e escolhe a view:

```php title="app/Http/Controllers/PainelController.php" numbered
public function index(Request $request)
{
    $emprestimos = Emprestimo::emAberto()
        ->comLivroELeitor()
        ->orderBy('devolver_ate')
        ->get();

    return view('painel.index', [
        'emprestimos' => $emprestimos,
        'hoje' => now(),
    ]);
}
```

```blade title="resources/views/painel/index.blade.php" numbered
<h1>Empréstimos em aberto</h1>

<table>
    @forelse ($emprestimos as $emprestimo)
        <tr>
            <td>{{ $emprestimo->exemplar->tombo }}</td>
            <td>{{ $emprestimo->exemplar->livro->titulo }}</td>
            <td>{{ $emprestimo->leitor->nome }}</td>
            <td>{{ $emprestimo->devolver_ate->format('d/m/Y') }}</td>
        </tr>
    @empty
        <tr><td colspan="4">Nada emprestado agora.</td></tr>
    @endforelse
</table>
```

`@forelse` é um `foreach` com um caso a menos para esquecer: ele já traz o
`@empty` para a lista vazia. Sem ele, a tela de uma biblioteca sem
empréstimos seria uma tabela sem nenhuma linha e sem nenhuma explicação.

As diretivas que cobrem quase tudo:

| Blade | PHP |
|---|---|
| `{{ $x }}` | `echo e($x)` |
| `@if` / `@else` / `@endif` | `if` / `else` |
| `@foreach` / `@endforeach` | `foreach` |
| `@forelse` / `@empty` | `foreach` com teste de vazio |
| `@php ... @endphp` | um bloco de PHP puro |

Tabela: O último existe, é legítimo em casos raros e costuma ser o sinal de
que a conta deveria ter sido feita no controller.

## `{{ }}` escapa, e isso é o recurso

Suponha que alguém cadastre um livro com este título:

```text
<script>alert('oi')</script>
```

```blade
<td>{{ $livro->titulo }}</td>
```

```text
<td>&lt;script&gt;alert('oi')&lt;/script&gt;</td>
```

O navegador mostra o texto e não executa nada. `{{ }}` converte os
caracteres que teriam significado em HTML antes de imprimir — é o que
impede o campo de um formulário de virar código na tela de outra pessoa.

E existe a outra forma:

```blade
<td>{!! $livro->titulo !!}</td>
```

```text
<td><script>alert('oi')</script></td>
```

:::pitfall
`{!! !!}` não é "a versão que não quebra o HTML". É uma decisão de
segurança, e a pergunta que ela obriga é uma só: **quem escreveu esse
conteúdo?**

Se a resposta incluir "um usuário", a resposta certa é `{{ }}`. Se for
mesmo necessário imprimir HTML vindo de fora — um editor de texto rico, por
exemplo —, o conteúdo precisa passar antes por uma limpeza que remova o que
não é permitido, e isso é uma biblioteca, não uma decisão de chave.

O ataque tem nome, XSS, e o formato mais comum dele é exatamente este: um
campo de cadastro que ninguém olhou, impresso numa tela que outra pessoa
abre.
:::

## Layout e componente

Três telas já repetem cabeçalho, rodapé e menu. O jeito moderno de resolver
isso no Blade é um componente de layout:

```blade title="resources/views/components/layout.blade.php" numbered
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <title>{{ $titulo ?? 'Casa Amarela' }}</title>
</head>
<body>
    <header>
        <strong>Biblioteca Casa Amarela</strong>
        <nav>
            <a href="{{ route('painel.index') }}">Empréstimos</a>
            <a href="{{ route('painel.acervo') }}">Acervo</a>
        </nav>
    </header>

    <main>
        {{ $slot }}
    </main>
</body>
</html>
```

```blade title="resources/views/painel/index.blade.php" numbered
<x-layout titulo="Empréstimos em aberto">
    <h1>Empréstimos em aberto</h1>

    <table>
        ...
    </table>
</x-layout>
```

O arquivo em `components/` vira a etiqueta `<x-layout>`. O que estiver
dentro da etiqueta chega em `$slot`; o que for escrito como atributo chega
como variável.

:::key
Existe também o `@include('parciais.menu')`, mais antigo, e ele envelhece
mal por um motivo específico: o arquivo incluído enxerga **todas** as
variáveis de quem incluiu.

Isso funciona até o dia em que duas telas incluem a mesma parcial e uma
delas não tem a variável que a parcial usa. O erro aparece na tela, e a
causa está em outro arquivo.

O componente declara o que recebe. É a mesma diferença entre o array e a
classe do capítulo @cap:classes-e-objetos, agora em HTML.
:::

## O formulário e o token que você não vê

A tela que a Vera pediu:

```blade title="resources/views/painel/emprestar.blade.php" numbered
<x-layout titulo="Emprestar">
    <form method="POST" action="{{ route('painel.emprestar') }}">
        @csrf

        <label for="tombo">Tombo</label>
        <input id="tombo" name="tombo" value="{{ old('tombo') }}"
               autofocus>

        @error('tombo')
            <p class="erro">{{ $message }}</p>
        @enderror

        <label for="documento">Documento do leitor</label>
        <input id="documento" name="documento"
               value="{{ old('documento') }}">

        @error('documento')
            <p class="erro">{{ $message }}</p>
        @enderror

        <button>Emprestar</button>
    </form>
</x-layout>
```

Três diretivas fazem o trabalho chato.

**`@csrf`** insere um campo escondido com um token. Quando o formulário
volta, o Laravel confere se o token bate com o da sessão — e recusa se não
bater.

:::term CSRF
*Cross-Site Request Forgery*: um site qualquer, aberto noutra aba, monta um
formulário que aponta para o **seu** sistema e faz o navegador enviá-lo. Como
o navegador manda os cookies de sessão junto, o pedido chega autenticado.

O token resolve porque o site de fora não tem como saber qual é. É por isso
que ele existe em `web.php` e não existe em `api.php`: sem sessão em cookie,
não há o que forjar.
:::

**`old('tombo')`** devolve o que a pessoa tinha digitado antes de o
formulário ser recusado. Sem isso, um erro de validação apaga o
preenchimento — e a Vera digita tudo de novo, com a fila esperando.

**`@error('tombo')`** só imprime quando existe um erro naquele campo.

E o controller do outro lado:

```php title="app/Http/Controllers/PainelController.php" numbered
public function emprestar(
    Request $request,
    RegistroDeEmprestimo $emprestimos,
) {
    $dados = $request->validate([
        'tombo' => ['required', 'integer'],
        'documento' => ['required', 'string'],
    ]);

    try {
        $emprestimos->registrarPorTombo(
            $dados['tombo'],
            $dados['documento'],
        );
    } catch (ExemplarIndisponivel $e) {
        return back()
            ->withInput()
            ->withErrors(['tombo' => $e->getMessage()]);
    }

    return redirect()
        ->route('painel.emprestar')
        ->with('sucesso', 'Emprestado.');
}
```

`back()->withInput()` devolve a pessoa ao formulário com o que ela digitou,
e é o que alimenta o `old()`. O `redirect()` no caminho de sucesso existe
para que atualizar a página não empreste o mesmo livro de novo — o
navegador reenviaria o `POST`.

:::key
Essa dupla — redirecionar depois de gravar, devolver com os dados depois de
recusar — é a base de toda tela de formulário. Ela resolve o
"atualizar a página duplicou o cadastro" sem nenhuma esperteza.

É o parente pobre da idempotência do capítulo @cap:o-que-e-uma-api-rest, e
resolve o mesmo problema: alguém apertou duas vezes.
:::

## Quando parar

O Blade entrega tela renderizada no servidor. Isso cobre listagem,
formulário, filtro e relatório — o que quase todo painel administrativo é.

Ele para de ser a ferramenta certa quando a tela precisa mudar **sem
recarregar**: arrastar itens, atualizar sozinha, editar em várias abas ao
mesmo tempo.

| A tela precisa de | Blade dá conta |
|---|---|
| listar, filtrar, paginar | sim |
| formulário com validação | sim |
| relatório e impressão | sim |
| trecho que atualiza sozinho | com ajuda |
| interface que não recarrega | não |

Tabela: A coluna do meio tem uma faixa cinza, e é onde mora a decisão de
arquitetura da maioria dos projetos.

:::pitfall
O pior lugar para estar é o meio: um Blade cheio de JavaScript que monta
pedaços da tela e conversa com a API, mas que não é uma aplicação de
front-end nem uma tela do servidor.

Você acaba com dois lugares que sabem montar a mesma lista, duas cópias da
regra de exibição e nenhuma das vantagens dos dois lados.

A decisão honesta é escolher por tela: esta é servida pelo servidor, aquela
é uma aplicação de front-end que consome a API. As duas convivem no mesmo
projeto sem problema — o que não convive é a mistura dentro de uma.
:::

:::note Na sua carreira
A Vera não pediu tela por conservadorismo. Ela pediu porque mede o trabalho
dela em segundos por atendimento, e ninguém no projeto tinha essa unidade na
cabeça.

Vale levar isso para qualquer levantamento de requisito: **pergunte quantas
vezes por dia a pessoa faz aquilo**. A resposta muda a decisão técnica mais
do que qualquer preferência de arquitetura — uma operação feita seiscentas
vezes por dia justifica uma tela dedicada, e uma feita três vezes por mês
não justifica nem um botão.

É também o argumento que funciona quando você precisar defender a escolha
numa reunião em que alguém quer tudo no aplicativo.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  resources/views/
    components/
      layout.blade.php      # <x-layout>
    painel/
      index.blade.php       # empréstimos em aberto
      emprestar.blade.php   # o campo e o botão
      acervo.blade.php
  routes/
    web.php                 # o painel, com sessão e CSRF
    api.php                 # o aplicativo do leitor
:::

:::milestone
Fim da Parte 6. O Laravel está de pé, configurado, com as rotas desenhadas
registradas, controllers que traduzem em vez de decidir, e a tela que a
bibliotecária vai usar no balcão. O que falta agora é o que está por trás
dela: os dados.
:::

:::summary
- Tela e API atendem situações diferentes; a pergunta é quem usa e em que
  situação.
- View é arquivo `.blade.php`; o controller monta os dados e escolhe.
- `@forelse` traz o caso da lista vazia junto.
- `{{ }}` escapa o conteúdo e é o que impede XSS; `{!! !!}` é uma decisão de
  segurança, não de formatação.
- Componente declara o que recebe; `@include` enxerga tudo de quem incluiu.
- `@csrf` protege formulário de sessão; em API não faz sentido porque não
  há cookie a forjar.
- `old()` e `@error` devolvem o formulário preenchido depois de uma recusa.
- Redirecionar depois de gravar impede que atualizar a página repita a
  operação.
- Blade cobre listagem, formulário e relatório; interface que não recarrega
  é outro trabalho, e misturar os dois é o pior dos mundos.
:::

:::checkpoint
Você entrega uma tela funcional com listagem e formulário, explica o que
`{{ }}` faz e por que `{!! !!}` é uma decisão, sabe por que o token de
formulário existe no painel e não na API, e consegue defender por que o
resto do livro continua sendo API.
:::

:::exercise level=1
Diga o que está errado em cada linha de Blade:

```blade
<td>{!! $leitor->nome !!}</td>
```

```blade
<form method="POST" action="/painel/emprestar">
    <input name="tombo">
    <button>Emprestar</button>
</form>
```

```blade
@php
    $total = 0;
    foreach ($emprestimos as $e) {
        $total += $e->multa->centavos();
    }
@endphp
```

:::answer
**A primeira** imprime sem escapar um dado cadastrado por uma pessoa. O nome
de um leitor pode conter `<` e `>` por engano — ou de propósito. É `{{ }}`.

**A segunda** não tem `@csrf`. O formulário vai ser recusado com `419`, e —
pior que não funcionar — se alguém desativar a proteção para "resolver", a
rota fica aberta a envio de fora.

Também vale trocar o caminho fixo por `{{ route('painel.emprestar') }}`,
pelo motivo do capítulo anterior.

**A terceira** é uma conta na view. Ela funciona e mora no lugar errado: não
tem teste, não é reaproveitável pela API e obriga quem mexer no cálculo da
multa a lembrar de um arquivo `.blade.php`.

O total vem pronto do controller, ou do próprio objeto que já sabe somar
`Dinheiro`.
:::

:::exercise level=2
Escreva a tela de devolução: um campo para o tombo, um seletor com os
estados possíveis do exemplar e um botão.

O seletor deve ser montado a partir do enum `StatusExemplar`, sem repetir a
lista no HTML.

:::answer
```blade title="resources/views/painel/devolver.blade.php" numbered
<x-layout titulo="Devolver">
    <form method="POST" action="{{ route('painel.devolver') }}">
        @csrf

        <label for="tombo">Tombo</label>
        <input id="tombo" name="tombo" value="{{ old('tombo') }}"
               autofocus>

        @error('tombo')
            <p class="erro">{{ $message }}</p>
        @enderror

        <label for="estado">Estado na volta</label>
        <select id="estado" name="estado">
            @foreach ($estados as $estado)
                <option value="{{ $estado->value }}"
                    @selected(old('estado') === $estado->value)>
                    {{ $estado->rotulo() }}
                </option>
            @endforeach
        </select>

        <button>Devolver</button>
    </form>
</x-layout>
```

```php
return view('painel.devolver', [
    'estados' => StatusExemplar::devolucao(),
]);
```

Três decisões.

O `value` do `<option>` é `$estado->value` e o texto é `$estado->rotulo()` —
exatamente a separação do capítulo @cap:enums-datas-e-valores entre o que
vai para o sistema e o que a pessoa lê.

O `@selected` é açúcar para o atributo `selected`; ele existe para que o
`old()` funcione também no seletor, e não só nos campos de texto.

E a lista não é `StatusExemplar::cases()`: é um método que devolve só os
estados que fazem sentido numa devolução. `emprestado` não é um deles, e
deixar o `cases()` cru ofereceria à Vera uma opção que o serviço vai
recusar.
:::

:::exercise level=3
O painel cresceu: sete telas, e cada uma tem o mesmo bloco de busca por
tombo no topo. O código foi copiado sete vezes.

Você recebe duas propostas: transformar o bloco num `@include`, ou num
componente. Escolha, escreva a implementação e explique o que aconteceria
com a outra opção daqui a seis meses.

:::answer
**Componente**, e o arquivo é anônimo — não precisa de classe:

```blade title="resources/views/components/busca-por-tombo.blade.php"
@props(['acao', 'rotulo' => 'Tombo', 'valor' => null])

<form method="GET" action="{{ $acao }}" class="busca">
    <label for="tombo">{{ $rotulo }}</label>
    <input id="tombo" name="tombo"
           value="{{ $valor ?? request('tombo') }}" autofocus>
    <button>Buscar</button>
</form>
```

```blade
<x-busca-por-tombo :acao="route('painel.acervo')" />

<x-busca-por-tombo :acao="route('painel.emprestar')"
                   rotulo="Tombo para emprestar" />
```

`@props` declara o que o componente aceita e o valor padrão de cada coisa. É
a assinatura dele — e o Blade avisa quando falta o que é obrigatório.

**O que aconteceria com o `@include`.** Ele funcionaria hoje, porque as sete
telas por acaso têm as variáveis certas no escopo. O problema chega na
oitava.

Alguém cria uma tela nova, inclui a parcial, e ela usa `$acao` — que naquela
tela não existe. O erro aparece na renderização, apontando para o arquivo da
parcial, e quem for investigar vai olhar um arquivo que está correto há seis
meses.

Depois disso, o caminho comum é a parcial ganhar um `?? ''` para não quebrar,
e aí o formulário passa a apontar para lugar nenhum em silêncio. É o mesmo
percurso do `function_exists` do capítulo @cap:do-include-ao-composer: o
remendo apaga o aviso e mantém o defeito.
:::
