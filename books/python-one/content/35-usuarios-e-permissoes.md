---
title: "Usuários e permissões"
number: 35
slug: usuarios-e-permissoes
part: p7
kicker: "Saber quem é a pessoa responde metade da pergunta. A outra metade é o que ela pode fazer com o dado que é de outro."
goal: >-
  Modelar papéis, proteger rotas por papel, verificar propriedade do recurso
  e escolher a camada certa para cada tipo de autorização.
---

A cooperativa tem três tipos de gente no sistema: quem administra, quem
opera o armazém e o produtor, que só enxerga os próprios produtos.

Essas três frases descrevem duas coisas diferentes — e confundi-las é o erro
de autorização mais comum que existe.

:::diagram type="blocks" caption="Três camadas de autorização — e a de baixo é a única que conhece o dado."
rows:
  - [{ text: "Autenticado?", note: "tem token válido · 401 se não" }]
  - [{ text: "Tem o papel?", note: "admin, operador, produtor · 403 se não" }]
  - [{ text: "O recurso é dele?", note: "só o serviço sabe · 403 ou 404" }]
:::

## Papéis

```python title="app/models/usuario.py" numbered
from enum import Enum


class Papel(str, Enum):
    ADMIN = "admin"
    OPERADOR = "operador"
    PRODUTOR = "produtor"


class Usuario(Base):
    papel: Mapped[Papel] = mapped_column(
        default=Papel.PRODUTOR
    )
    produtor_id: Mapped[int | None] = mapped_column(
        ForeignKey("produtor.id"), default=None
    )
```

O padrão é o papel **menos** privilegiado. Um usuário criado por um caminho
que esqueceu de definir o papel nasce sem poder nenhum, e não administrador
— a diferença entre um bug e um incidente.

:::key
Autorização é sempre uma lista de permissão, nunca uma lista de proibição.
"Todo mundo pode, exceto..." significa que toda funcionalidade nova nasce
liberada, e alguém precisa lembrar de proibir. "Ninguém pode, exceto..."
significa que ela nasce fechada, e alguém precisa lembrar de liberar — e o
esquecimento, aí, produz um chamado de suporte em vez de um vazamento.
:::

## Exigir papel

```python title="app/dependencies.py" numbered
from collections.abc import Callable


def exigir_papel(*papeis: Papel) -> Callable:
    def verificar(usuario: UsuarioDep) -> Usuario:
        if usuario.papel not in papeis:
            raise HTTPException(
                403, "você não tem permissão para esta operação"
            )
        return usuario

    return verificar


AdminDep = Annotated[
    Usuario, Depends(exigir_papel(Papel.ADMIN))
]
OperacaoDep = Annotated[
    Usuario, Depends(exigir_papel(Papel.ADMIN, Papel.OPERADOR))
]
```

`exigir_papel` é uma fábrica: ela recebe os papéis e devolve a dependência
já configurada — o mesmo padrão do decorador com argumento do capítulo
@cap:dependency-injection.

```python title="uso.py" numbered
@router.post("", response_model=ProdutoLer, status_code=201)
def criar(dados: ProdutoCriar, servico: ServicoDep,
          usuario: OperacaoDep):
    return servico.criar(dados)


@router.delete("/{produto_id}", status_code=204)
def apagar(produto_id: int, servico: ServicoDep,
           usuario: AdminDep):
    servico.apagar(produto_id)
```

Repare que `usuario` não é usado no corpo de `apagar`. Declarar o parâmetro
é o que aciona a verificação — e, se isso incomodar, a alternativa é
`dependencies=[Depends(exigir_papel(Papel.ADMIN))]` no decorador.

## `401` e `403`

| Status | Significa | O que o cliente faz |
|---|---|---|
| `401` | não sei quem você é | pedir login ou renovar token |
| `403` | sei quem você é, e não pode | mostrar erro, não tentar de novo |

Tabela: Devolver `401` para falta de permissão faz o cliente entrar num
laço de renovação de token que nunca resolve.

:::pitfall
Há um caso em que `403` vaza informação: responder `403` para um recurso de
outra pessoa confirma que aquele identificador existe. `GET /produtos/1234`
com `403` diz "existe o produto 1234, e não é seu"; com `404`, não diz nada.
Para dado sensível, responda `404` nos dois casos — o cliente legítimo nunca
vai pedir um recurso que não é dele.
:::

## A terceira camada: o recurso é dele?

Esta é a que nenhuma dependência resolve.

```python title="app/services/produto.py" numbered
def atualizar(
    self, produto_id: int, dados: ProdutoAtualizar,
    usuario: Usuario,
) -> Produto:
    produto = self.buscar(produto_id)

    if usuario.papel is Papel.PRODUTOR:
        if produto.produtor_id != usuario.produtor_id:
            raise SemPermissao(produto_id)

    alteracoes = dados.model_dump(exclude_unset=True)
    for campo, valor in alteracoes.items():
        setattr(produto, campo, valor)

    self.session.commit()
    return produto
```

A dependência sabe o papel; ela **não** sabe de quem é o produto — para
isso seria preciso carregá-lo, e carregar é trabalho do serviço, que vai
carregá-lo de qualquer jeito.

:::key
Autorização por papel é uma propriedade de **quem chama**: cabe na borda.
Autorização por propriedade é uma propriedade do **dado**: cabe no serviço.
Tentar resolver a segunda na dependência significa consultar o banco duas
vezes e espalhar regra de negócio pela camada HTTP.
:::

## Filtrar a listagem

```python title="listagem.py" numbered
def listar(
    self, filtro: ProdutoFiltro, usuario: Usuario
) -> list[Produto]:
    if usuario.papel is Papel.PRODUTOR:
        filtro = filtro.model_copy(
            update={"produtor_id": usuario.produtor_id}
        )
    return self.repo.listar(filtro)
```

O produtor vê a lista dele. Repare que o filtro é **sobrescrito**, não
apenas preenchido quando vazio: se ele informar `produtor_id=9`, o valor é
substituído pelo dele. Confiar no filtro que o cliente mandou é o defeito
clássico de listagem com escopo.

:::story O relatório de todo mundo
O produtor ligou animado.

— Consegui ver o preço de todo mundo!

Bia pediu a URL. Era `/produtos?produtor_id=3`.

O filtro existia desde o capítulo dos filtros, era público, e ninguém tinha
pensado nele ao fechar a listagem — a rota exigia autenticação, e isso
pareceu suficiente na revisão.

— A gente protegeu quem entra — disse Bia. — Não protegeu o que ele pergunta
depois de entrar.
:::

:::warning
Toda funcionalidade que aceita um identificador vindo do cliente precisa da
pergunta: *e se ele mandar o de outra pessoa?* Isso vale para filtro, para
parâmetro de caminho, para campo do corpo e para o campo de ordenação. É a
falha número um das listas de vulnerabilidades de API, e tem nome:
autorização quebrada em nível de objeto.
:::

## Registrar quem fez

```python title="auditoria.py" numbered
class Produto(Base):
    criado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id"), default=None
    )
    atualizado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id"), default=None
    )
```

Dois campos que ninguém pede no começo e todo mundo pede depois — em geral
na primeira vez que um preço muda e ninguém sabe quem mudou. Acrescentá-los
no início custa duas colunas; acrescentá-los depois custa duas colunas e a
falta de todo o histórico anterior.

:::summary
- Papel padrão é o menos privilegiado.
- Autorização é lista de permissão, nunca lista de proibição.
- Papel se verifica na borda; propriedade do recurso, no serviço.
- `401` é identidade; `403` é permissão — e `404` quando `403` vazaria.
- Filtro com escopo é sobrescrito, não completado.
- Todo identificador vindo do cliente merece a pergunta "e se for de outro?".
:::

:::milestone
A API sabe quem entra, o que cada um pode e de quem é cada dado. É a última
peça antes dos testes — e os testes existem, em boa parte, para garantir que
estas três respostas continuem certas amanhã.
:::

:::exercise level=1
Crie a dependência `AdminDep` e proteja a rota de remoção de produtos.

:::answer
```python
AdminDep = Annotated[
    Usuario, Depends(exigir_papel(Papel.ADMIN))
]


@router.delete("/{produto_id}", status_code=204)
def apagar(
    produto_id: int, servico: ServicoDep, usuario: AdminDep
):
    servico.apagar(produto_id)
```
:::

:::exercise level=1
Escreva o teste que garante que um produtor recebe `403` ao tentar alterar
um produto de outro produtor.

:::answer
```python
def test_produtor_nao_altera_produto_alheio(servico):
    produto = servico.criar_para(produtor_id=7, nome="Tomate")
    outro = Usuario(papel=Papel.PRODUTOR, produtor_id=9)

    with pytest.raises(SemPermissao):
        servico.atualizar(produto.id, dados, usuario=outro)
```
Esse teste é mais importante que ele parece. Regra de permissão é o tipo de
código que ninguém exercita manualmente — quem desenvolve está sempre
logado como administrador, e o caminho do produtor só é percorrido em
produção, por quem não tem como avisar que funcionou demais.
:::

:::exercise level=2
Faça a listagem de produtos devolver, para o papel `PRODUTOR`, apenas os
produtos do produtor vinculado ao usuário.

:::answer
```python
def listar(self, filtro, usuario, pagina, tamanho):
    if usuario.papel is Papel.PRODUTOR:
        if usuario.produtor_id is None:
            return Pagina(itens=[], total=0,
                          pagina=pagina, tamanho=tamanho)
        filtro = filtro.model_copy(
            update={"produtor_id": usuario.produtor_id}
        )
    return self._paginar(filtro, pagina, tamanho)
```
O `produtor_id is None` é o caso que a implementação ingênua esquece: um
usuário com papel de produtor e sem vínculo cadastrado. Sem esse tratamento,
o filtro fica `None` e a listagem devolve **tudo** — o pior resultado
possível, produzido por um dado incompleto.
:::

:::exercise level=3
A cooperativa quer que um produtor possa autorizar outro a gerenciar seus
produtos durante as férias. Descreva o que muda no modelo de permissões e
qual é o risco principal.

:::answer
O papel deixa de bastar. `PRODUTOR` descrevia uma relação um-para-um entre
usuário e produtor; agora é muitos-para-muitos, com atributos.

```python
class Delegacao(Base):
    __tablename__ = "delegacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    produtor_id: Mapped[int] = mapped_column(
        ForeignKey("produtor.id"), index=True
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id"), index=True
    )
    inicio: Mapped[date]
    fim: Mapped[date]
    revogada_em: Mapped[datetime | None] = mapped_column(
        default=None
    )
```

E a verificação passa a ser uma função do serviço, não uma comparação:

```python
def pode_gerenciar(self, usuario, produtor_id) -> bool:
    if usuario.papel in (Papel.ADMIN, Papel.OPERADOR):
        return True
    if usuario.produtor_id == produtor_id:
        return True
    return self.repo_delegacao.vigente(
        usuario.id, produtor_id, date.today()
    )
```

**O risco principal é a delegação que não termina.** Uma data de fim que
ninguém confere, um `revogada_em` que a interface não expõe, ou uma consulta
que esquece o filtro de vigência transformam um acesso temporário em
permanente — e ninguém percebe, porque nada quebra quando uma permissão
sobra.

Três coisas mitigam isso, e vale escrevê-las junto com a funcionalidade, não
depois: o filtro de vigência dentro do repositório (para que nenhum chamador
possa esquecê-lo), um prazo máximo validado no cadastro, e um registro de
auditoria que diga, em cada alteração, se ela foi feita pelo dono ou por
delegação. A terceira é a que responde à pergunta que a cooperativa vai
fazer em algum momento: *quem mexeu no meu preço em janeiro?*
:::
