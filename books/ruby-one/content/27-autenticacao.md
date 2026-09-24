---
title: "Autenticação"
number: 27
slug: autenticacao
part: p6
kicker: "A credencial da Serra Azul era de leitura. O Diego mandou um POST com ela, e o nortea criou o contrato."
goal: >-
  Saber quem está do outro lado do pedido: a Helena entra com usuário e
  senha guardada do jeito certo; a Serra Azul consulta com uma credencial
  que só lê os próprios contratos; e o teste prova o 403 do que ela não
  pode fazer.
---

:::story Credencial de leitura
Na segunda, 25 de maio, a nove dias da renovação, o Diego mandou uma
mensagem para a sala com um print e uma linha:

> Criei um contrato com o token da Serra Azul.

O print mostrava o comando:

```text
$ curl -X POST https://homolog.nortea.com.br/api/contracts \
    -H "Authorization: Bearer sa_live_7Qk..." \
    -d "contract[code]=CT-9999&contract[equipment_id]=412..."
HTTP/1.1 201 Created
```

A Lívia leu duas vezes.

— O token é de leitura. Está escrito na tela de credenciais.

— Está escrito na tela — disse o Caio. — Onde está escrito no código?

Ela procurou. O `before_action` da API conferia se o token existia. Não
conferia o que ele podia fazer. E o `/api/contracts` antigo, o de 2025,
ainda tinha o `create` que o Sérgio usava para sincronizar com a planilha.

O Renato chegou, leu o print e pôs a caneca na mesa.

— Isso não sobe. Nem com a data.
:::

## Quem é e o que pode

Duas perguntas, feitas em ordem, a todo pedido que não é público:

**Quem é você?** A autenticação. A Helena, com usuário e senha. O sistema
da Serra Azul, com uma credencial. Se não der para saber, a resposta é
`401`.

**O que você pode fazer?** A autorização. A Helena pode cadastrar e
cancelar. A Serra Azul pode ler os contratos dela. Se a pessoa é conhecida
e a ação não é permitida, a resposta é `403`.

O `nortea` tinha a primeira pergunta para a API, e não a segunda. É o
defeito mais comum desse tipo de sistema, e o do print do Diego.

## A Helena entra

Senha não se guarda. Guarda-se um *hash* dela: o resultado de uma conta de
mão única, que permite conferir a senha digitada sem ser possível voltar
da conta para a senha. O Rails faz isso com uma linha:

```ruby title="app/models/user.rb" numbered
class User < ApplicationRecord
  has_secure_password

  validates :email, presence: true, uniqueness: true
end
```

`has_secure_password` precisa de uma coluna `password_digest` e da gem
`bcrypt`. Ele cria o atributo `password`, que não é gravado; o que vai para
o banco é o hash, em `password_digest`. E cria `authenticate`:

```text
nortea(dev)> u = User.find_by(email: "helena@nortea.com.br")
nortea(dev)> u.password_digest
=> "$2a$12$Kx9vQ2mT8pLr4wYz6nB1cOd3fG5hJ0sA2eR7tU9iO..."
nortea(dev)> u.authenticate("errada")
=> false
nortea(dev)> u.authenticate("a senha certa")
=> #<User id: 3, email: "helena@nortea.com.br", ...>
```

O `bcrypt` é lento de propósito: cada conferência leva um quarto de
segundo. Para a Helena entrar, não se nota. Para quem roubar a tabela e
tentar milhões de senhas, é a diferença entre minutos e anos.

O controller de entrada:

```ruby title="app/controllers/sessions_controller.rb" numbered
class SessionsController < ApplicationController
  skip_before_action :require_login, only: [:new, :create]

  def create
    user = User.find_by(email: params[:email])

    if user&.authenticate(params[:password])
      session[:user_id] = user.id
      redirect_to contracts_path
    else
      flash.now[:alerta] = "E-mail ou senha incorretos."
      render :new, status: :unprocessable_entity
    end
  end
end
```

`session` é um hash guardado num cookie assinado: o navegador o manda de
volta a cada pedido, e o Rails confere que ninguém o alterou. A mensagem
de erro é a mesma para e-mail inexistente e senha errada: dizer "e-mail
não cadastrado" é dizer a quem tenta quais e-mails existem.

E todas as telas exigem a entrada:

```ruby title="app/controllers/application_controller.rb" numbered
class ApplicationController < ActionController::Base
  before_action :require_login

  private

  def require_login
    @current_user = User.find_by(id: session[:user_id])
    redirect_to new_session_path unless @current_user
  end
end
```

`before_action` no `ApplicationController` vale para todos os controllers
que herdam dele — todas as telas. O `skip_before_action` do
`SessionsController` abre uma exceção só para a tela de entrada, senão
ninguém conseguiria chegar a ela.

## A Serra Azul consulta

Um sistema não digita senha numa tela. Ele manda uma credencial em cada
pedido, no cabeçalho `Authorization`. Na Nortea, cada cliente com acesso à
API tem uma:

```ruby title="app/models/api_credential.rb" numbered
class ApiCredential < ApplicationRecord
  belongs_to :customer
  has_secure_token :token

  SCOPES = %w[read write].freeze
  validates :scope, inclusion: { in: SCOPES }

  def can_write?
    scope == "write"
  end
end
```

`has_secure_token :token` gera um texto aleatório longo para a coluna
`token` ao criar. `scope` diz o que a credencial pode: `read` ou `write`.
A da Serra Azul é `read`. A do script de sincronização do Sérgio é
`write`.

O controller base da API:

```ruby title="app/controllers/api/base_controller.rb" numbered
module Api
  class BaseController < ActionController::API
    include ActionController::HttpAuthentication::Token::
              ControllerMethods

    before_action :authenticate!

    private

    def authenticate!
      @credential = authenticate_with_http_token do |token, _|
        ApiCredential.find_by(token: token)
      end

      head :unauthorized unless @credential
    end

    def require_write!
      head :forbidden unless @credential.can_write?
    end
  end
end
```

`authenticate_with_http_token` lê o cabeçalho `Authorization: Bearer ...`
e entrega o token ao bloco. Sem credencial válida, `401` e nada mais.

`require_write!` é a segunda pergunta. Quem herda de `Api::BaseController`
e grava declara:

```ruby title="app/controllers/api/contracts_controller.rb" numbered
module Api
  class ContractsController < BaseController
    before_action :require_write!, only: [:create, :update]
    # ...
  end
end
```

O token da Serra Azul passa pelo `authenticate!` — ele existe — e para no
`require_write!`. `403`.

:::term Autenticação e autorização
Autenticação responde **quem é**: senha, token. Falhou, `401`.
Autorização responde **o que pode**: gravar, ler, ver este contrato.
Falhou, `403`.

Um sistema com só a primeira pergunta trata todo mundo conhecido como
dono de tudo.
:::

## Só os próprios contratos

O `422` do capítulo @cap:apis deixou um aviso: a lista devolvia os
contratos de todos os clientes. Com a credencial, a API sabe quem
pergunta, e a consulta parte do cliente dela:

```ruby title="app/controllers/api/v1/contracts_controller.rb" numbered
def index
  # ... a validação do status, como antes
  contracts = @credential.customer.contracts
                         .includes(:equipment).where(status: status)
  render json: contracts.map(&:as_api)
end

def show
  contract = @credential.customer.contracts
                        .includes(:equipment)
                        .find_by!(code: params[:id])
  render json: contract.as_api
end
```

A busca começa em `@credential.customer.contracts` — a associação do
capítulo @cap:associacoes —, não em `Contract`. O contrato de outro
cliente não é encontrado, e o `find_by!` responde `404`.

`404`, e não `403`, de propósito: `403` diria à Serra Azul que o
`CT-3150` existe e é de outra pessoa. Para quem não pode ver, o contrato
alheio não existe.

:::key
A consulta de quem é autenticado **começa no que é dele**:
`credencial.customer.contracts`, nunca `Contract.where(...)` com um
filtro. Um filtro esquecido vaza tudo. Uma consulta que começa no dono
não tem o que vazar.
:::

## O teste do `403`

Autorização se testa pelo lado da recusa. Ninguém testa à mão o que a
credencial **não** pode, porque o caminho feliz é o que se vê na tela.

```ruby title="spec/requests/api/contracts_spec.rb" numbered
require "rails_helper"

RSpec.describe "API de contratos" do
  let(:serra) { create(:customer) }
  let(:leitura) do
    create(:api_credential, customer: serra, scope: "read")
  end

  def auth(credencial)
    { "Authorization" => "Bearer #{credencial.token}" }
  end

  it "recusa gravação com credencial de leitura" do
    post "/api/contracts",
         params: { contract: attributes_for(:contract) },
         headers: auth(leitura)

    expect(response).to have_http_status(:forbidden)
    expect(Contract.count).to eq(0)
  end

  it "não mostra contrato de outro cliente" do
    alheio = create(:contract)

    get "/api/v1/contracts/#{alheio.code}", headers: auth(leitura)

    expect(response).to have_http_status(:not_found)
  end

  it "recusa pedido sem credencial" do
    get "/api/v1/contracts"

    expect(response).to have_http_status(:unauthorized)
  end
end
```

Um teste de *request* manda um pedido HTTP de verdade para o `nortea`,
passando pela rota, pelos `before_action` e pelo controller. É o print do
Diego, escrito para o computador conferir a cada mudança.

O segundo `expect` do primeiro exemplo é o que importa: além do `403`,
nenhum contrato foi criado. Um `403` devolvido **depois** de gravar
passaria só no primeiro.

```text
$ bundle exec rspec spec/requests/api/contracts_spec.rb
...

3 examples, 0 failures
```

:::summary
- Autenticação diz quem é (`401`); autorização diz o que pode (`403`).
- `has_secure_password` guarda o hash com `bcrypt`; `authenticate`
  confere. A mensagem de erro não diz se o e-mail existe.
- `before_action` no controller base protege todas as telas;
  `skip_before_action` abre a exceção da entrada.
- A credencial da API vai no cabeçalho `Authorization`, com escopo. A
  consulta começa em `credencial.customer.contracts`.
- Contrato alheio responde `404`. O teste da recusa confere também que
  nada foi gravado.
:::

:::exercise level=1
Diga o código de resposta para cada pedido:

1. `GET /api/v1/contracts` sem cabeçalho `Authorization`.
2. `GET /api/v1/contracts/CT-3196` com o token da Serra Azul, contrato
   dela.
3. O mesmo, com um contrato de outro cliente.
4. `POST /api/contracts` com o token da Serra Azul.

:::answer
`401`, `200`, `404` e `403`.

O 3 é `404`, e não `403`, porque a consulta parte dos contratos da Serra
Azul: para ela, o contrato alheio não existe.
:::

:::exercise level=2
A Marta quer que a Serra Azul **não** veja contratos cancelados na lista,
nem que peça por eles. Escreva a mudança e diga onde ela mora.

:::answer
Na consulta que parte do cliente, e na tabela de status aceitos da API:

```ruby
contracts = @credential.customer.contracts
                       .where.not(status: "cancelled")
                       .includes(:equipment).where(status: status)
```

E `"cancelado"` sai dos valores aceitos no filtro — um pedido por ele
recebe o `422` com a lista do que é aceito, em vez de uma lista vazia.

A tabela combinada com a Serra Azul ganha a linha que diz isso. Uma regra
de visibilidade que só está no código é uma regra que ninguém do outro
lado sabe que existe.
:::

:::exercise level=3
O Sérgio precisa que o script de sincronização da planilha continue
gravando pela API. Ele pede para usar o token da Serra Azul "só nas
madrugadas", porque é o único que ele tem à mão. Responda, e diga o que
fazer.

:::answer
Não. O token da Serra Azul é de leitura, e o `403` agora vai recusar —
mas o motivo principal não é esse. Uma credencial identifica **quem** fez o
pedido. Gravações do script feitas com o token da Serra Azul apareceriam,
no log e em qualquer auditoria, como feitas pela Serra Azul.

O que fazer: uma credencial própria para o script, com escopo `write`,
ligada a um cliente interno — a própria Nortea —, guardada fora do
repositório, como a senha do banco. E, com ela, uma pergunta para depois
de 3 de junho: se o script precisa mesmo gravar pela API, ou se pode rodar
dentro do `nortea`, com `bin/rails runner`, sem expor uma credencial de
escrita na rede.
:::
