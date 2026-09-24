---
title: "Git, CI e o dia do deploy"
number: 28
slug: git-ci-e-deploy
part: p7
kicker: "No dia 31 de março, às sete da manhã, o papel dobrado com a senha do FTP saiu da pasta do projeto pela última vez."
goal: >-
  Sair do "funciona na minha máquina": um histórico que dá para ler, uma
  esteira que recusa o que não passa, um deploy em ordem com migration,
  cache e worker no lugar certo, uma verificação de saúde honesta — e,
  no fim, um requisito novo implementado de ponta a ponta, sozinho.
---

## `.gitignore` antes do primeiro `git add`

O projeto `casa-amarela/` está num repositório desde o capítulo
@cap:primeiro-projeto-laravel, e o Laravel já veio com um `.gitignore`. Ele
merece ser lido uma vez, linha por linha, porque cada linha é um incidente
que alguém já teve:

```text title=".gitignore"
/vendor
/node_modules
/public/build
/public/storage
/storage/*.key
.env
.env.backup
.env.production
.phpunit.result.cache
```

**`/vendor`** é recriado pelo `composer install` a partir do
`composer.lock` — a lição do capítulo @cap:do-include-ao-composer.

**`.env`** tem a senha do banco, a chave da aplicação, o token do provedor
de mensagens. É o arquivo mais importante da lista.

**`.env.backup`** e **`.env.production`** existem porque alguém, em algum
projeto, fez uma cópia do `.env` com outro nome "só para guardar", e a
cópia foi para o repositório.

O que **entra** no repositório é o `.env.example`, com todas as chaves e
nenhum valor de verdade. Ele é a documentação de quais variáveis a
aplicação precisa, e é o que a pessoa nova copia no primeiro dia.

## Segredo no histórico se resolve trocando o segredo

A regra existe e, em algum momento, alguém vai quebrá-la. O `.env` vai
entrar num commit, por um `git add .` feito com pressa, antes de o
`.gitignore` estar certo.

A reação instintiva é apagar o arquivo e fazer outro commit. Não resolve:
o Git guarda **todo o histórico**, e o `.env` continua no commit anterior,
legível por qualquer pessoa com acesso ao repositório — e por qualquer
cópia dele que já tenha sido feita.

Existem ferramentas para reescrever o histórico e apagar o arquivo de todos
os commits. Elas são úteis e **não são a solução**, porque não alcançam os
clones que já existem, os *forks*, o cache do serviço de hospedagem, a
máquina da pessoa que baixou o repositório ontem.

:::key
Segredo que entrou no histórico está vazado. A única correção é **trocar o
segredo**: gerar uma senha nova para o banco, uma chave nova para o
provedor, revogar o token.

Reescrever o histórico é limpeza. Trocar o segredo é a correção. Na ordem
certa: primeiro troca, depois limpa.
:::

É a mesma resposta do capítulo @cap:middleware para as senhas que foram
para o log, e do capítulo @cap:autenticacao para as senhas do Sistema. Ela
se repete porque o princípio é um só: um segredo que outra pessoa pode ter
visto deixou de ser segredo.

## Commit que conta uma história

O histórico de um projeto é lido muito mais vezes do que é escrito, e quase
sempre por alguém procurando **por que** uma linha é do jeito que é.

```text
$ git log --oneline
a3f9c21 ajustes
7be4d02 wip
c01e8f5 corrige
9d2a6b7 mais ajustes
e44f1a0 agora vai
```

Cinco commits, nenhuma informação. Compare:

```text
$ git log --oneline
a3f9c21 Devolução pela caixa usa PrazoDeEmprestimo
7be4d02 Teste reproduz multa em devolução adiantada
c01e8f5 Listagem de empréstimos desempata por id
9d2a6b7 Último exemplar exige autorização, não recusa
e44f1a0 Limite de 5 empréstimos em janeiro
```

Cada linha diz o que mudou, no imperativo ou como fato, em menos de
setenta caracteres. Quem procurar por que a devolução da caixa mudou em
fevereiro acha em segundos — e o commit logo abaixo mostra que o teste veio
antes da correção, como o capítulo @cap:testes pediu.

Para as mudanças que precisam de explicação, o corpo do commit, depois de
uma linha em branco, conta o porquê:

```text
Último exemplar exige autorização, não recusa

A regra foi anotada como "só c/ autoriz." e implementada
como recusa. Corrigida com a Vera em 18/02. A Autorizacao
registra quem autorizou e o motivo, e cobre também os
casos que antes eram tratados de cabeça no balcão.
```

:::note
Ramos e revisão entram aqui numa frase, porque são assunto de equipe mais
do que de código: cada mudança nasce num ramo, vira um *pull request*, e
alguém lê antes de ela entrar no ramo principal. O ramo principal é sempre
publicável. A revisão não é para achar erro de digitação — a esteira acha —
mas para perguntar "por que assim?", que só uma pessoa pergunta.
:::

## A esteira: Pint, PHPStan, testes

A esteira de integração contínua é um conjunto de conferências que roda
sozinho a cada *push*, numa máquina limpa, e diz se o código pode entrar.
Para a Casa Amarela, quatro:

```yaml title=".github/workflows/esteira.yml" numbered
name: esteira

on: [push, pull_request]

jobs:
  conferir:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_DATABASE: casa_amarela_teste
          MYSQL_ROOT_PASSWORD: teste
        ports: ['3306:3306']
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=5s --health-retries=10

    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.3'
          coverage: none

      - run: composer install --no-interaction --prefer-dist

      - name: Estilo
        run: vendor/bin/pint --test

      - name: Análise estática
        run: vendor/bin/phpstan analyse --no-progress

      - name: Nada de dd() esquecido
        run: "! grep -rnE '\\b(dd|dump|var_dump)\\(' app/"

      - name: Testes
        run: php artisan test --parallel
        env:
          DB_HOST: 127.0.0.1
          DB_PASSWORD: teste
```

**Pint** confere o estilo do código — espaçamento, ordem dos `use`,
chaves. Com `--test`, ele só acusa, sem alterar. A discussão sobre estilo
sai da revisão de código e vai para uma ferramenta, onde não ofende
ninguém.

**PHPStan**, no nível 5 do capítulo @cap:tipagem-estrita, lê o código sem
rodar e acusa o que não fecha: método que não existe, tipo que não bate,
`null` onde não pode. Para projetos Laravel, a extensão Larastan ensina o
PHPStan a entender os models e as *facades*.

**A busca por `dd(`** é a regra do capítulo @cap:cache-logs-e-medicao, numa
linha.

**Os testes** rodam no **mesmo MySQL** da produção — o serviço declarado no
topo —, pelo motivo do capítulo @cap:testes-de-feature-http-e-banco.

A esteira vermelha bloqueia o *merge*. Não é recomendação: é configuração
do repositório. O ramo principal só recebe o que passou.

## Migration em produção é um passo separado

O deploy de uma aplicação Laravel tem uma ordem, e a ordem existe porque
cada passo depende do anterior:

```bash title="deploy.sh" numbered
#!/usr/bin/env bash
set -euo pipefail

cd /var/www/casa-amarela

git fetch --tags
git checkout "$1"

composer install --no-dev --optimize-autoloader

php artisan down --retry=15

php artisan migrate --force

php artisan config:cache
php artisan route:cache
php artisan view:cache

php artisan queue:restart

php artisan up
```

O `set -euo pipefail` faz o script **parar no primeiro erro**. Sem ele, uma
migration que falha é seguida de `config:cache` e `up`, e a aplicação volta
ao ar com o banco pela metade.

O `$1` é a versão — uma *tag* do Git, como `v1.0.0`. O deploy publica uma
versão com nome, não "o que estiver no ramo principal agora". Voltar atrás
é rodar o mesmo script com a *tag* anterior.

O `--no-dev` não instala o Telescope, o Pest nem o Debugbar. O
`--optimize-autoloader` gera o mapa de classes do capítulo
@cap:namespaces-e-autoload, que o autoload de produção usa em vez de
procurar arquivo a cada classe.

A migration é um passo **separado e único**: roda uma vez, num lugar só.
Quando a aplicação cresce e passa a rodar em cinco servidores, a tentação é
pôr o `migrate` no início de cada um — e as cinco máquinas tentam alterar a
mesma tabela ao mesmo tempo. O `--isolated` do `migrate` trava a execução
para que só uma rode, e a regra continua valendo: migração é um passo do
deploy, não da inicialização de cada máquina.

:::pitfall
O `--force` existe porque o Laravel, em produção, **pergunta antes de
migrar**, e um script não responde perguntas. Ele é necessário no script e
é perigoso fora dele: digitado à mão, no terminal errado, com o `.env`
errado, é o `migrate:fresh` da quinta-feira do capítulo
@cap:migrations-seeders-e-factories com outro nome.

Deploy é um script, versionado, revisado. Ninguém roda migration de
produção digitando.
:::

## `down`, cache e o worker que precisa reiniciar

O `artisan down` põe a aplicação em manutenção: toda requisição recebe
`503` com o cabeçalho `Retry-After`, e o aplicativo do leitor mostra "em
manutenção, volte em alguns minutos". Ele existe para que ninguém faça um
empréstimo **durante** a migration, com metade das colunas no formato
antigo.

Os três `cache` vêm **depois** da migration e do código novo, porque
congelam o que existir naquele momento — o capítulo
@cap:cache-logs-e-medicao explicou o que acontece quando rodam antes. E
vêm **antes** do `up`, para que a primeira requisição já encontre tudo
pronto.

O `queue:restart` é o passo que mais se esquece e o que o capítulo
@cap:events-jobs-e-filas pediu que não se esquecesse: sem ele, o worker
continua com o código de ontem na memória, e os avisos saem com o texto
antigo — ou quebram, procurando a coluna que a migration de hoje renomeou.

:::note
Deploy **sem** tirar a aplicação do ar existe, e tem nome: *zero downtime*.
A técnica mais comum é preparar a versão nova numa pasta ao lado, com tudo
pronto, e trocar um atalho de uma para a outra num instante.

O que ela exige é que **as duas versões funcionem com o mesmo banco** ao
mesmo tempo — o que obriga as migrations a seguirem a expansão e contração
do capítulo @cap:migrations-seeders-e-factories: acrescentar antes, remover
num deploy seguinte. É mais trabalho em toda migration. Para uma biblioteca
que abre às nove, um minuto de manutenção às sete da manhã é a escolha
honesta.
:::

## Health check: vivo não é o mesmo que pronto

O capítulo @cap:primeiro-projeto-laravel apresentou a `/up`, que o Laravel
traz pronta. Ela responde `200` se a aplicação consegue atender uma
requisição. É uma pergunta útil — **o processo está vivo?** — e não é a
única.

A aplicação pode estar viva e sem banco. Viva e com o disco cheio. Viva e
com a fila parada há seis horas. A `/up` responde `200` nos três casos.

```php title="app/Http/Controllers/ProntoController.php" numbered
public function __invoke(): JsonResponse
{
    $checagens = [
        'banco' => $this->tenta(fn () => DB::select('SELECT 1')),
        'cache' => $this->tenta(fn () => Cache::put('pronto', 1, 5)),
        'fila' => $this->tenta(fn () => $this->filaAndando()),
        'disco' => $this->tenta(fn () => $this->discoComFolga()),
    ];

    $ok = !in_array(false, $checagens, true);

    return response()->json(
        ['pronto' => $ok, 'checagens' => $checagens],
        $ok ? 200 : 503,
    );
}

private function filaAndando(): bool
{
    $maisVelho = DB::table('jobs')->min('created_at');

    return $maisVelho === null
        || now()->diffInMinutes($maisVelho) < 15;
}
```

| Rota | Pergunta | Quem consulta |
|---|---|---|
| `/up` | o processo responde? | o balanceador, a cada poucos segundos |
| `/pronto` | consegue fazer o trabalho? | o monitoramento, a cada minuto |

Tabela: A primeira deve ser barata e não depender de nada. A segunda pode
consultar o banco, e por isso não é chamada a cada dois segundos.

A `/pronto` não diz **o que** quebrou para quem não deve saber: fica atrás
de um token do monitoramento, ou responde só `200` e `503` para o mundo e o
detalhe para quem se autentica. A lição do capítulo
@cap:erros-padronizados vale para ela também.

## A lista antes de publicar

Uma lista curta, conferida na véspera, por uma pessoa com a lista na mão —
e não de memória:

- `APP_ENV=production` e `APP_DEBUG=false`.
- `APP_KEY` gerada **no servidor**, diferente da de desenvolvimento.
- HTTPS com certificado válido, e HTTP redirecionando para HTTPS.
- `.env` do servidor fora do repositório, legível só pelo usuário da
  aplicação.
- Permissões de `storage/` e `bootstrap/cache/` como no capítulo
  @cap:primeiro-projeto-laravel.
- Worker sob supervisor, reiniciando no deploy.
- Agendador no `cron`: `* * * * * php artisan schedule:run`.
- Log em JSON, com rotação, e nenhum campo sensível — conferido com uma
  busca.
- `/pronto` sendo consultada pelo monitoramento, com alerta para alguém.
- Backup diário do banco **e uma restauração testada**.

O último item é o único que merece explicação, porque é o que mais se
pula. Um backup que nunca foi restaurado é uma hipótese. O arquivo pode
estar corrompido, incompleto, criptografado com uma chave que ninguém tem,
ou ser o backup de outro banco. A única forma de saber é restaurar numa
máquina separada e abrir o acervo.

O Nonato fez um `UPDATE` sem `WHERE` numa sexta de 2013, no capítulo
@cap:sql-do-zero, e é por isso que existe backup diário desde então. O que
ninguém tinha feito, em treze anos, era restaurar um.

:::warning
Docker entra nesta lista só onde agrega. Para a Casa Amarela — uma
aplicação, um banco, um worker, um servidor —, um servidor com PHP, MySQL
e supervisor instalados é mais simples de entender, de manter e de
consertar às sete da manhã. Docker faz sentido quando há muitas aplicações
na mesma máquina, ambientes difíceis de reproduzir, ou uma equipe que já
opera tudo assim. Adotá-lo "porque é profissional" é o erro do capítulo
@cap:primeiro-projeto-laravel, com mais peças.
:::

:::story O papel dobrado
Às sete da manhã do dia 31, a Márcia tirou da pasta do projeto o papel
dobrado que o Seu Juvenal tinha entregado em outubro. Usuário, senha, e no
canto, em caneta de outra cor: *"não mexer na pasta antiga"*.

O sistema novo ia para um servidor novo. O papel servia para a última
coisa que ainda era preciso fazer na hospedagem velha: tirar uma cópia
final do Sistema e trocar a página inicial por um aviso com o endereço
novo.

Nonato pegou o papel, leu, e ficou um tempo parado.

— Essa letra é minha.

— A senha? — perguntou Tainá.

— O "não mexer na pasta antiga". Eu escrevi isso em 2011. A pasta antiga
era a versão de 2009, que eu deixei lá caso a nova desse problema.

— E deu?

— Não. Mas eu nunca tive coragem de apagar.

Dedé rodou o script de deploy. `down`, `migrate`, três `cache`,
`queue:restart`, `up`. Quatro minutos. A `/pronto` respondeu `200` com
quatro `true`.

O celular do Dedé vibrou. Rejane: *"Parabéns pelo ownership nesse
go-live!!! Sua promoção foi aprovada para o ciclo de abril."* Ele leu duas
vezes e guardou o celular sem responder.

Nonato entrou por FTP na hospedagem velha, baixou as duas pastas — a antiga
e a de 2011 —, conferiu o tamanho dos arquivos duas vezes e trocou o
`index.php` por uma página com uma frase e um endereço.

— Pronto — disse ele. — Quinze anos.

— Meio milhão de empréstimos — disse Tainá. — Eu contei. Nenhum acervo
perdido.

Nonato dobrou o papel de novo, pelas mesmas dobras.

— Posso ficar com isso?

Márcia olhou para ele, depois para o papel.

— A senha ainda funciona.

— Então troca a senha — disse Dedé. — Depois ele fica.
:::

:::art caption="Quinze anos, meio milhão de empréstimos e um papel dobrado."
src="quinze-anos-meio-milhao-de-emprestimos-e-um-papel-dobrado.png"
Ilustração editorial minimalista em fundo branco, tom mais contido: um
dev de uns quarenta anos, de camisa xadrez, segura com cuidado um papel
dobrado em quatro, com uma anotação à mão num canto em caneta de outra
cor. Atrás dele, um monitor de tubo antigo mostra uma tela cinza com
formulário, e ao lado um monitor novo mostra uma tela limpa com um visto
verde. Em volta, de pé, uma gerente com uma pasta, um desenvolvedor mais
novo que guarda o celular no bolso sem olhar, e uma estagiária de caderno
aberto, todos olhando para o papel. Poucos elementos, humor sutil e
afetuoso, estética de revista de tecnologia.
:::

## O primeiro pedido depois do ar

O sistema está no ar. E, como todo sistema no ar, ele recebe o primeiro
pedido novo na mesma semana — o primeiro de uma fila que a Parte 8 começa
a atender.

A Vera quer poder **perdoar uma multa**. Existem casos — uma enchente, uma
doença, um livro devolvido molhado pela chuva de dezembro — em que ela
decide que a pessoa não deve pagar. Hoje, ela anota no caderno e não cobra,
e o relatório de fim de mês mostra uma dívida que não existe.

Este pedido é seu. Ele atravessa quase tudo que este livro construiu, e o
roteiro abaixo diz **onde** cada parte mora — não **como** escrevê-la:

| Camada | O que decidir | Capítulo |
|---|---|---|
| rota | `POST /multas/{multa}/perdao`, e por que não `DELETE` | @cap:o-que-e-uma-api-rest |
| Form Request | o `motivo` é obrigatório, com tamanho mínimo | @cap:validation-e-form-requests |
| policy | quem pode perdoar — e se a atendente pode | @cap:autorizacao |
| service | multa já paga ou já perdoada não se perdoa | @cap:services |
| exceção | o `tipo` do `409` | @cap:erros-padronizados |
| evento | `MultaPerdoada`, depois do commit | @cap:events-jobs-e-filas |
| fila | avisar o leitor, uma vez só | @cap:events-jobs-e-filas |
| resource | a multa mostra que foi perdoada, e por quem? | @cap:api-resources |
| testes | a regra na unidade, o `403` na feature | @cap:testes |
| documentação | o `tipo` novo na tabela de erros | @cap:documentacao-da-api |

Tabela: Dez decisões, e nenhuma delas é de digitação. O código de cada
camada tem entre cinco e trinta linhas.

Duas perguntas não têm resposta técnica, e precisam ser feitas à Vera antes
da primeira linha. **O leitor deve ver o motivo do perdão?** — "enchente"
talvez sim, "situação financeira" talvez não. **Existe um valor acima do
qual só o admin perdoa?** A resposta vai mudar a policy, e é o tipo de
regra que só aparece quando alguém pergunta.

:::milestone
Fim da Parte 7. A Casa Amarela está no ar: acervo com busca, filtro e
paginação; empréstimos com as onze regras da Vera num service que ela
consegue ler; autenticação e autorização por recurso; erros num formato
só; avisos pela fila, sem repetir; cache onde ele não mente; testes que
provam a regra e o contrato; documentação gerada do código; e um deploy que
é um script.

O Sistema de 2009 está numa pasta, com duas cópias, e ninguém apagou. E o
sistema novo acabou de conhecer a coisa que nenhum ambiente de teste
simula: gente de verdade usando.
:::

:::summary
- O `.gitignore` é uma lista de incidentes; o `.env.example` entra, o `.env`
  nunca.
- Segredo no histórico está vazado: primeiro se troca, depois se limpa.
- Commit diz o que mudou numa linha e o porquê no corpo.
- A esteira confere estilo, análise estática, `dd()` esquecido e testes no
  MySQL de produção, e bloqueia o *merge*.
- O deploy é um script que para no primeiro erro, publica uma *tag*, e
  segue a ordem: código, `down`, `migrate`, caches, `queue:restart`, `up`.
- Migration roda uma vez, num lugar só, e nunca digitada à mão.
- `/up` diz que o processo está vivo; `/pronto`, que ele consegue trabalhar.
- A lista antes de publicar é conferida com a lista na mão; o backup só
  conta depois de restaurado.
- Um requisito novo atravessa rota, validação, policy, service, exceção,
  evento, fila, resource, testes e documentação — e começa com duas
  perguntas a quem faz o trabalho.
:::

:::checkpoint
A aplicação está no ar com a lista cumprida, a esteira bloqueia o que não
passa, o deploy é um script versionado que você consegue explicar passo a
passo, e o perdão de multa está implementado de ponta a ponta — por você,
sozinho, com um teste para cada decisão.
:::

:::exercise level=1
Ponha os passos do deploy na ordem certa e diga o que dá errado se o passo
marcado vier fora do lugar:

`queue:restart` · `migrate --force` · `up` · `config:cache` ·
`composer install --no-dev` · `down` · `git checkout v1.4.0`

:::answer
1. `git checkout v1.4.0`
2. `composer install --no-dev`
3. `down`
4. `migrate --force`
5. `config:cache` (e os outros dois caches)
6. `queue:restart`
7. `up`

**`config:cache` antes do `checkout`:** congela a configuração da versão
anterior; a chave nova do `.env` ou do `config/` não entra.

**`migrate` antes do `down`:** durante a migração, a aplicação atende com
o banco pela metade — um empréstimo feito nesse minuto pode gravar no
formato antigo ou falhar.

**`queue:restart` esquecido:** o worker roda o código de ontem até
alguém reiniciá-lo, ou até o `--max-time` expirar.

**`up` antes dos caches:** as primeiras requisições encontram o cache
antigo ou nenhum, e ficam lentas ou erradas por alguns segundos.
:::

:::exercise level=2
A pessoa nova do time fez `git add .` e um `push` com o `.env` de
produção. O repositório é privado, com seis pessoas com acesso. Escreva, em
ordem, o que fazer na próxima hora.

:::answer
1. **Trocar os segredos**, começando pelos que dão mais acesso: a senha do
   usuário do banco, a chave do provedor de mensagens, qualquer token de
   serviço externo. Atualizar o `.env` do servidor e rodar `config:cache`.
2. **Trocar a `APP_KEY`** — com cuidado: ela cifra sessões e cookies, e
   trocá-la derruba quem está logado no painel. Numa biblioteca, às sete
   da manhã, é aceitável; em outros sistemas, pede um plano.
3. **Remover o arquivo** do repositório num commit novo, e acrescentá-lo
   ao `.gitignore` se não estava.
4. **Reescrever o histórico**, se a equipe decidir, avisando as seis
   pessoas para clonarem de novo.
5. **Conferir o `.gitignore`** e a configuração do editor da pessoa, para
   entender como o arquivo passou.

E um sexto, que não é técnico: tratar como acidente, não como culpa. A
pessoa que esconde o próximo erro porque foi exposta neste é o risco maior.
O passo 5 é sobre o processo que deixou passar, não sobre quem digitou.
:::

:::exercise level=3
Implemente o perdão de multa descrito na seção "O último pedido". Use a
tabela de camadas como roteiro e as duas perguntas à Vera como ponto de
partida — decida as respostas e escreva-as num comentário no topo do
service.

Ao terminar, responda: qual das dez decisões você mudaria se a Vera
respondesse diferente à segunda pergunta, e quantos arquivos essa mudança
tocaria?

:::answer
Não há uma resposta única, e uma solução completa tem entre oito e doze
arquivos. Os pontos que uma boa solução acerta:

**Rota:** `POST /multas/{multa}/perdao`, e não `DELETE /multas/{multa}` — a
multa não deixa de existir; ela ganha um desfecho. O histórico precisa
mostrar que houve multa e que foi perdoada. É a mesma razão do
`POST /emprestimos/{id}/devolucao` do capítulo @cap:o-que-e-uma-api-rest.

**Service:** `MultaService::perdoar(int $multaId, Autorizacao $a)`, com
transação e trava, lançando `MultaJaQuitada` se já estiver paga ou
perdoada. A `Autorizacao` do capítulo @cap:services volta: perdão é
julgamento, e julgamento se registra.

**Policy:** `MultaPolicy::perdoar`, perguntando por uma permissão
`PerdoarMulta` — não pelo papel.

**Evento e fila:** `MultaPerdoada` com `ShouldDispatchAfterCommit`, e um
listener que avisa o leitor com registro `unique` em `avisos_enviados`.

**Testes:** a regra de "não perdoa duas vezes" na unidade; o `403` para
leitor e o `201` para quem tem a permissão na feature; o job executado duas
vezes com uma mensagem só.

**Sobre a pergunta final.** Se a Vera responder que multas acima de, por
exemplo, R$ 50 só o admin perdoa, a mudança mora **em um lugar**: a
`MultaPolicy::perdoar` passa a receber a multa e comparar o valor. Um
arquivo de código e um caso novo no dataset do teste de feature.

Se a sua resposta tocou mais arquivos que isso — se o limite apareceu no
service **e** na policy, ou no Form Request —, vale voltar e perguntar onde
a regra mora. É a pergunta que o livro inteiro fez, capítulo a capítulo, e
é a que você vai fazer, a partir de agora, sem ele.
:::
