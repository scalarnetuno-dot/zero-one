---
title: "Autenticação com Sanctum"
number: 44
slug: autenticacao
part: p9
kicker: "O Sistema guardava as senhas em MD5, sem sal. Na hora do almoço, na máquina de um desenvolvedor, sessenta por cento caíram em quatro minutos."
goal: >-
  Responder "quem é você" com segurança: guardar senha do jeito certo,
  migrar as que estão erradas, emitir e revogar tokens com Sanctum, e
  escrever um login cuja resposta de erro não entrega nada — nem no texto,
  nem no tempo.
---

:::story Quatro minutos
Dedé tinha exportado a tabela `usuarios` do Sistema para planejar a
migração. Duas colunas interessavam: `email` e `senha`. A segunda tinha
trinta e dois caracteres hexadecimais em cada linha.

— MD5 — disse ele.

— Isso é ruim? — perguntou Tainá.

— Me dá quatro minutos.

Ele baixou uma lista pública de senhas vazadas — alguns milhões de linhas,
o tipo de arquivo que circula há uma década —, escreveu um laço de oito
linhas e rodou. O ventilador do notebook acelerou.

```text
$ php quebrar.php usuarios.csv senhas-comuns.txt
testadas: 14.344.391
quebradas: 1.047 de 1.731 (60,5%)
tempo: 3min52s
```

Tainá olhou a lista que foi aparecendo. `123456`. `casaamarela`.
`biblioteca`. `marmelada1994`. O nome de um cachorro que ela conhecia de
foto no balcão.

— Você pode apagar isso agora? — disse ela.

— Já estou apagando.

— E se alguém tiver essa tabela?

— O Sistema está no ar há quinze anos, com backup num HD na sala dos
fundos e a senha do FTP num papel — disse Dedé. — Eu não sei quem tem essa
tabela.
:::

## Senha nunca é guardada

O Sistema cometeu um erro que parece técnico e é de princípio. Ele
guardava **alguma coisa derivada da senha** que permitia descobrir a senha.

O que um sistema de login precisa não é saber a senha. É **conferir** se a
senha digitada agora é a mesma cadastrada antes. Para isso, basta guardar
algo que:

1. seja sempre igual para a mesma senha;
2. não permita, na prática, voltar à senha original.

Uma função com essas duas propriedades se chama *hash*. O MD5 é uma — e é
por isso que o Sistema achava que estava protegido.

O problema está na palavra "na prática". O MD5 foi desenhado para ser
**rápido**: conferir a integridade de arquivos grandes, milhões de vezes
por segundo. Uma placa de vídeo comum calcula bilhões de MD5 por segundo.
Com essa velocidade, não é preciso voltar do hash para a senha: basta
calcular o hash de todas as senhas prováveis e comparar.

E sem **sal** — um valor aleatório diferente para cada usuário, misturado
à senha antes do cálculo —, pessoas com a mesma senha têm o mesmo hash. A
lista de hashes de senhas comuns, calculada uma vez, serve para todos os
sistemas do mundo que usaram MD5 puro.

| Guardar | Quem vaza a tabela obtém |
|---|---|
| a senha | todas as senhas, na hora |
| MD5 sem sal | as senhas comuns, em minutos |
| SHA-256 sem sal | o mesmo, um pouco mais devagar |
| MD5 com sal | as comuns, uma conta por vez |
| `bcrypt` / `argon2` | muito pouco, muito devagar |

Tabela: O que muda de uma linha para outra não é a matemática da função; é
quanto tempo custa **cada tentativa**.

## `bcrypt`, `argon2` e o custo que é proposital

Funções feitas para senha fazem o contrário do MD5: são **lentas de
propósito**, com o quanto de lentidão ajustável por um fator de custo.

```php
$hash = Hash::make('marmelada1994');
```

```text
$2y$12$Qm1S3pTjXe4K8b0vYzN1ZuQ4rW7pX2... (60 caracteres)
```

O hash já traz dentro dele tudo que é preciso para conferir depois: o
algoritmo (`2y` é `bcrypt`), o custo (`12`), o sal (os 22 caracteres
seguintes) e o resultado. Nada disso é segredo, e nada disso ajuda a
descobrir a senha.

```php
Hash::check('marmelada1994', $hash); // true
Hash::check('marmelada1995', $hash); // false
```

Com custo 12, cada conferência leva algo como duzentos e cinquenta
milissegundos numa máquina comum. Para quem faz login, é imperceptível.
Para quem tenta catorze milhões de senhas, é a diferença entre quatro
minutos e **cento e onze dias** — por conta, porque cada uma tem o seu sal.

O Laravel usa `bcrypt` por padrão, com custo configurado no `.env`. O
`argon2id` é mais moderno e resiste melhor a placas de vídeo; os dois são
escolhas corretas. A escolha errada é qualquer coisa que não tenha sido
feita para senha.

:::key
O custo não é um defeito a otimizar. Se alguém do time "acelerar o login"
baixando o fator de custo para 4, o login fica cinquenta vezes mais rápido
para todo mundo — inclusive para quem roubou a tabela.

O `Hash::needsRehash($hash)` diz se um hash foi gerado com um custo menor
que o configurado. É o que permite **subir** o custo com os anos, conforme
as máquinas ficam mais rápidas.
:::

### Migrar as senhas do Sistema

As 1.731 contas do Sistema não podem ser convertidas de uma vez: para
gerar o `bcrypt` é preciso a senha, e a senha ninguém tem. A saída é
converter **no próximo login de cada pessoa**, quando a senha passa pela
aplicação:

```php title="app/Auth/ConferidorDeSenha.php" numbered
final class ConferidorDeSenha
{
    public function confere(Usuario $u, string $senha): bool
    {
        if ($this->ehMd5Legado($u->senha)) {
            if (!hash_equals($u->senha, md5($senha))) {
                return false;
            }

            $u->forceFill(['senha' => Hash::make($senha)])->save();

            return true;
        }

        if (!Hash::check($senha, $u->senha)) {
            return false;
        }

        if (Hash::needsRehash($u->senha)) {
            $u->forceFill(['senha' => Hash::make($senha)])->save();
        }

        return true;
    }

    private function ehMd5Legado(string $hash): bool
    {
        return (bool) preg_match('/^[a-f0-9]{32}$/', $hash);
    }
}
```

`hash_equals` compara duas strings levando sempre o mesmo tempo,
independentemente de onde elas diferem. A comparação com `===` para no
primeiro caractere diferente — e isso, medido milhões de vezes, vaza
informação.

:::warning
A migração no login protege as contas **daqui para a frente**. Não protege
o que já vazou.

As senhas do Sistema devem ser consideradas comprometidas: ele ficou no ar
quinze anos com a tabela em MD5, e ninguém sabe quem teve acesso aos
backups. A decisão certa — e que a Vera precisa tomar com a associação,
porque envolve avisar todo mundo — é **forçar a troca de senha** no
primeiro acesso ao sistema novo. O `ConferidorDeSenha` continua útil: ele
reconhece a senha antiga uma última vez, para permitir a troca.

E contas que nunca mais entrarem ficam com MD5 para sempre. Depois de um
prazo, elas são apagadas — o hash, não a conta —, e o próximo acesso passa
pela recuperação de senha.
:::

## Sessão e token: dois problemas diferentes

Depois de conferir a senha, o servidor precisa **lembrar** que conferiu. O
HTTP não lembra — o capítulo @cap:o-que-e-http mostrou que cada requisição
chega sozinha. Existem duas formas de resolver, e cada uma serve a um tipo
de cliente.

**Sessão com cookie.** O servidor guarda "o usuário 12 entrou" num
armazenamento dele, e manda ao navegador um cookie com um identificador
aleatório. O navegador devolve o cookie em toda requisição, sozinho. É o
que o painel Blade usa.

**Token.** O servidor entrega ao cliente uma string longa e aleatória, e o
cliente a manda no cabeçalho `Authorization` de cada requisição. Nada é
automático — o cliente guarda e manda. É o que o aplicativo do leitor usa.

| | Sessão | Token |
|---|---|---|
| quem guarda | o navegador, sozinho | o aplicativo, de propósito |
| como volta | cookie, automático | cabeçalho `Authorization` |
| serve para | páginas no mesmo domínio | aplicativos, integrações |
| risco principal | CSRF | token vazado |

Tabela: O cookie ser automático é a vantagem e o risco. O CSRF do capítulo
@cap:blade existe justamente porque o navegador manda o cookie mesmo quando
a requisição foi disparada por outro site.

## Sanctum

O Sanctum é o pacote do Laravel que resolve as duas coisas no mesmo lugar:
tokens para aplicativos e autenticação por sessão para um front-end no
mesmo domínio. A Casa Amarela usa a primeira metade.

```text
$ php artisan install:api
```

O comando instala o Sanctum, cria a tabela `personal_access_tokens` e o
arquivo `routes/api.php`, se ele ainda não existir. O model de usuário
ganha uma trait:

```php title="app/Models/Usuario.php" numbered
class Usuario extends Authenticatable
{
    use HasApiTokens;

    protected $table = 'usuarios';

    protected $authPasswordName = 'senha';

    protected $fillable = ['nome', 'email'];

    protected $hidden = ['senha'];

    protected function casts(): array
    {
        return [
            'papel' => Papel::class,
            'senha' => 'hashed',
        ];
    }
}
```

O `$authPasswordName` diz ao Laravel que a coluna se chama `senha` e não
`password`. O cast `hashed` faz o hash sozinho quando alguém atribui uma
senha em texto — e não faz de novo se o valor já for um hash, o que evita
o hash de um hash.

O `Papel` é um enum com três casos, e o capítulo seguinte depende dele:

```php title="app/Auth/Papel.php" numbered
enum Papel: string
{
    case Leitor = 'leitor';
    case Atendente = 'atendente';
    case Admin = 'admin';
}
```

Um `Usuario` com papel `Leitor` tem um `leitor_id` apontando para o
cadastro de leitor. Atendentes e admin não têm: são a equipe.

## Login, logout e `GET /eu`

```php title="app/Http/Controllers/Auth/LoginController.php" numbered
public function __invoke(
    LoginRequest $request,
    ConferidorDeSenha $conferidor,
) {
    $usuario = Usuario::where(
        'email',
        mb_strtolower($request->string('email')),
    )->first();

    $valido = $usuario !== null
        && $conferidor->confere($usuario, $request->senha);

    if (!$usuario) {
        Hash::check($request->senha, self::HASH_FALSO);
    }

    if (!$valido) {
        throw new CredenciaisInvalidas();
    }

    $token = $usuario->createToken(
        name: $request->string('dispositivo', 'app'),
        abilities: $usuario->papel->habilidades(),
        expiresAt: now()->addDays(30),
    );

    return response()->json([
        'token' => $token->plainTextToken,
        'expira_em' => $token->accessToken->expires_at
            ->toIso8601String(),
        'usuario' => new UsuarioResource($usuario),
    ], 201);
}
```

`createToken` gera uma string aleatória, grava o **hash** dela na tabela
`personal_access_tokens` e devolve o texto original uma única vez. Depois
desta resposta, nem o servidor sabe mais qual é o token — só consegue
conferir.

:::anatomy title="As partes de um token do Sanctum"
lang: text
code: |
  Authorization: Bearer 7|kX9vQ2mT8pLr4wYz6nB1cD3fG5hJ0sA2eR7tU9iO
notes:
  - { line: 1, text: "`Bearer` é o esquema: \"quem portar isto está autorizado\". Por isso o token é tratado como senha." }
  - { line: 1, text: "`7` é o id da linha em `personal_access_tokens`. Serve para achar a linha sem varrer a tabela." }
  - { line: 1, text: "O `|` separa o id do segredo." }
  - { line: 1, text: "O resto são 40 caracteres aleatórios. O banco guarda só o SHA-256 deles, e é seguro usar SHA aqui: o valor é aleatório, não uma senha que alguém escolheu." }
:::

Repare na última nota. SHA-256 é errado para senha e certo para token, e a
diferença está em quem escolheu o valor. Uma senha é escolhida por uma
pessoa, e existe uma lista das prováveis. Um token de quarenta caracteres
aleatórios não tem lista: tentar todos levaria mais tempo que a idade do
universo, com qualquer velocidade de cálculo.

As rotas protegidas usam o middleware do capítulo anterior:

```php title="routes/api.php" numbered
Route::post('auth/login', LoginController::class)
    ->middleware('throttle:login');

Route::middleware('auth:sanctum')->group(function () {
    Route::get('eu', EuController::class);
    Route::post('auth/logout', LogoutController::class);
    // ... o resto da API do leitor
});
```

```php title="app/Http/Controllers/EuController.php" numbered
public function __invoke(Request $request)
{
    return new UsuarioResource(
        $request->user()->load('leitor'),
    );
}
```

`$request->user()` devolve o usuário dono do token que veio no cabeçalho.
É o `null` que o `LeitorResource` do capítulo @cap:api-resources esperava
deixar de ser.

## Revogar de verdade

```php title="app/Http/Controllers/Auth/LogoutController.php" numbered
public function __invoke(Request $request)
{
    $request->user()->currentAccessToken()->delete();

    return response()->noContent();
}
```

O logout apaga **a linha do token** no banco. Na próxima requisição com
aquele token, o Sanctum procura pelo id, não encontra, e responde `401`.

É a vantagem de um token que mora no banco sobre um token autocontido,
como o JWT, que carrega os dados dentro e é conferido só pela assinatura: o
JWT continua válido até expirar, e "sair" no aplicativo apaga a cópia do
celular sem invalidar as outras. Com o Sanctum, sair é sair.

Três situações pedem revogar **todos** os tokens de uma pessoa:

```php
$usuario->tokens()->delete();
```

**A pessoa trocou a senha.** Se ela trocou porque desconfiou de alguém, o
alguém não pode continuar logado.

**A equipe bloqueou a conta.** O bloqueio que não derruba as sessões
abertas é um bloqueio que vale "no próximo login".

**A pessoa pediu.** O botão "sair de todos os aparelhos" existe em todo
aplicativo sério por isso.

:::pitfall
Token sem expiração é token para sempre. O celular perdido em 2026 ainda
acessa a conta em 2031.

O `expiresAt` no `createToken` define a validade de cada token, e a
configuração `expiration` em `config/sanctum.php` é a rede de segurança
para os que forem criados sem ela. Trinta dias com renovação no uso é um
equilíbrio comum para aplicativo; para o painel da equipe, horas.

Tokens expirados continuam na tabela até alguém apagar. O Sanctum tem um
comando para isso, `sanctum:prune-expired`, e ele vai para o agendamento do
capítulo @cap:configuracao-ambiente-e-artisan.
:::

## A resposta que não diz se o e-mail existe

Voltando ao `LoginController`, há duas linhas que parecem estranhas.

A primeira é a exceção única. Tanto e-mail inexistente quanto senha errada
produzem **a mesma resposta**:

```json
{
  "tipo": "credenciais-invalidas",
  "mensagem": "E-mail ou senha incorretos."
}
```

A alternativa — "e-mail não cadastrado" num caso, "senha incorreta" no
outro — é mais amigável e entrega a quem está atacando uma lista de quem é
leitor da Casa Amarela. Para uma biblioteca, isso parece inofensivo. Para
um serviço de saúde, de namoro ou de apoio psicológico, confirmar que um
e-mail tem conta já é o vazamento.

A segunda é o `Hash::check` com `HASH_FALSO` quando o usuário não existe.
Ele calcula um `bcrypt` inteiro e **joga fora o resultado**.

O motivo é o tempo. Sem essa linha, uma tentativa com e-mail inexistente
responde em cinco milissegundos — só a consulta ao banco. Uma tentativa com
e-mail existente e senha errada responde em duzentos e cinquenta — a
consulta mais o `bcrypt`. A mensagem é idêntica, e o cronômetro conta tudo.

:::key
Uma resposta de login precisa ser igual em **três** dimensões: o status, o
corpo e o tempo.

As duas primeiras se conferem lendo a resposta. A terceira só se confere
medindo — e é por isso que ela é a que costuma ficar de fora.
:::

E o HTTPS, que parece óbvio e merece estar escrito: sem ele, a senha viaja
em texto pela rede do café em que o leitor está. E o token também, em
todas as requisições seguintes. Nada deste capítulo funciona sem HTTPS, e o
capítulo @cap:git-ci-e-deploy o põe na lista antes de publicar.

:::note Na sua carreira
Você vai encontrar senha em MD5, em SHA-1, em texto puro e em "criptografia
reversível para poder mandar a senha por e-mail". Vai encontrar em sistemas
de empresas grandes, feitos por gente competente, anos atrás.

A conversa sobre isso raramente é técnica. É sobre avisar os usuários,
forçar troca de senha e admitir, por escrito, que o sistema antigo tinha um
problema. Quem conduz bem essa conversa — com o plano de migração pronto,
o texto do aviso rascunhado e o risco explicado sem alarmismo — é quem a
empresa chama da próxima vez que algo parecido aparecer.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/Auth/
    Papel.php                    # leitor, atendente, admin
    ConferidorDeSenha.php        # migra MD5 no login
    CredenciaisInvalidas.php     # uma exceção para os dois casos
  app/Models/
    Usuario.php                  # HasApiTokens, cast hashed
  app/Http/Controllers/
    Auth/LoginController.php     # token com validade
    Auth/LogoutController.php    # apaga o token atual
    EuController.php
  config/sanctum.php             # expiration
:::

:::summary
- Senha não se guarda; guarda-se um hash que permite conferir e não permite
  voltar.
- MD5 e SHA são rápidos de propósito; `bcrypt` e `argon2` são lentos de
  propósito, com sal por usuário.
- O custo do hash é proteção; `needsRehash` permite subi-lo com os anos.
- Senhas legadas migram no próximo login; as que vazaram exigem troca
  forçada.
- Sessão é cookie automático para páginas; token é cabeçalho explícito para
  aplicativos.
- O Sanctum guarda o hash do token no banco; logout apaga a linha e vale na
  hora.
- Troca de senha, bloqueio e "sair de todos" revogam todos os tokens.
- Token sem expiração vale para sempre; `expiresAt` e `sanctum:prune-expired`
  resolvem.
- O erro de login é igual no status, no corpo e no tempo; `hash_equals` e o
  hash falso protegem o terceiro.
:::

:::checkpoint
O login da API emite token com validade e habilidades, o logout revoga na
hora, as senhas do Sistema migram no primeiro acesso, e você sabe explicar
por que a resposta de erro é genérica — e por que ela demora o mesmo tempo
quando o e-mail não existe.
:::

:::exercise level=1
Diga o que está errado em cada decisão e qual a correção:

1. `senha` guardada com `hash('sha256', $senha . 'casaamarela')`.
2. Token criado sem `expiresAt` "porque o leitor reclama de ter que entrar
   de novo".
3. Ao trocar a senha, o sistema gera o hash novo e salva.
4. O login responde `404` quando o e-mail não existe.

:::answer
1. SHA-256 é rápido, e o "sal" é o mesmo para todos — é uma constante, não
   um sal. Correção: `Hash::make`.
2. Token eterno. Correção: validade de trinta dias **renovada no uso** — o
   leitor ativo nunca precisa entrar de novo, e o celular esquecido numa
   gaveta perde o acesso sozinho.
3. Faltou revogar os outros tokens. Correção: `$usuario->tokens()->delete()`
   depois de salvar, exceto, se quiser, o token da requisição atual.
4. Confirma que o e-mail não tem conta. Correção: a mesma resposta `401`
   para os dois casos, com o mesmo tempo.
:::

:::exercise level=2
Escreva o endpoint `POST /eu/senha`, que troca a senha do usuário
autenticado. Ele recebe a senha atual e a nova (com confirmação). Deve
recusar se a atual estiver errada, revogar todos os **outros** tokens, e
manter o atual funcionando.

:::answer
```php title="app/Http/Controllers/TrocaDeSenhaController.php" numbered
public function __invoke(
    TrocaDeSenhaRequest $request,
    ConferidorDeSenha $conferidor,
) {
    $usuario = $request->user();

    if (!$conferidor->confere($usuario, $request->senha_atual)) {
        throw new CredenciaisInvalidas();
    }

    $usuario->senha = $request->senha_nova;
    $usuario->save();

    $atual = $usuario->currentAccessToken()->id;

    $usuario->tokens()
        ->where('id', '!=', $atual)
        ->delete();

    return response()->noContent();
}
```

```php title="app/Http/Requests/TrocaDeSenhaRequest.php" numbered
public function rules(): array
{
    return [
        'senha_atual' => ['required', 'string'],
        'senha_nova' => [
            'required', 'confirmed',
            Password::min(10)->uncompromised(),
        ],
    ];
}
```

O cast `hashed` faz o hash da `senha_nova` na atribuição. O
`Password::uncompromised()` consulta um serviço público de senhas vazadas —
sem enviar a senha, só os primeiros caracteres do hash dela — e recusa as
que aparecem na lista. É a lista que o Dedé usou, virada para o lado
certo.

A rota fica atrás do `throttle`, como o login: sem ele, é um segundo lugar
para testar senhas.
:::

:::exercise level=3
O time de marketing da associação quer que o aplicativo mostre, na tela de
login, a mensagem "Esse e-mail não tem cadastro. Quer se inscrever?" —
porque muitas pessoas tentam entrar sem ter conta e desistem.

A necessidade é real. Proponha uma solução que atenda ao marketing sem
voltar a revelar quais e-mails têm conta, e diga o que ela custa.

:::answer
**O problema real.** Pessoas sem conta tentam entrar, recebem "e-mail ou
senha incorretos", acham que erraram a senha, e desistem. A mensagem
genérica protege quem tem conta e prejudica quem não tem.

**A solução: mudar o fluxo, não a mensagem.** A tela de login passa a ter
duas etapas. Na primeira, a pessoa digita o e-mail e toca em "continuar".
A resposta é sempre a mesma: "Enviamos um link para esse e-mail". Se o
e-mail tem conta, o link leva ao login. Se não tem, o link leva à
inscrição, já com o e-mail preenchido.

Quem está atacando recebe sempre "enviamos um link", e não aprende nada.
Quem não tem conta recebe, no próprio e-mail, o convite para se inscrever
— que é exatamente o que o marketing queria mostrar.

**O que custa.** Um passo a mais no login, e a dependência de envio de
e-mail funcionando — o que, com a fila do capítulo @cap:events-jobs-e-filas,
é tratável. E a tela de inscrição precisa da mesma disciplina: "esse e-mail
já tem cadastro" na inscrição vaza o mesmo dado pela outra porta. A
resposta ali também é "enviamos um link".

**A alternativa mais barata, e pior:** mostrar "Não tem conta? Inscreva-se"
**sempre**, em destaque, embaixo da mensagem de erro. Não revela nada, e
ajuda parte das pessoas. É o que dá para fazer nesta semana, enquanto o
fluxo em duas etapas não fica pronto.
:::
