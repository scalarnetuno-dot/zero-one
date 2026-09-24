---
title: "Validação"
number: 26
slug: validacao
part: p5
kicker: "Três camadas validam a mesma coisa, e nenhuma das três é redundante."
goal: >-
  Distribuir a validação entre esquema, serviço e banco; escrever validadores
  que normalizam; e produzir mensagens de erro que quem consome a API
  consegue usar.
---

"Preço tem de ser positivo" parece uma regra só. Ela aparece em três lugares
do projeto, e quem tenta economizar dois deles sempre descobre por quê.

:::diagram type="blocks" caption="Cada camada valida uma coisa diferente — e as três são necessárias."
rows:
  - [{ text: "Esquema (Pydantic)", note: "forma: tipo, tamanho, faixa" }]
  - [{ text: "Serviço", note: "contexto: o que depende de outros dados" }]
  - [{ text: "Banco", note: "verdade: a garantia final, sob concorrência" }]
:::

| Camada | Pergunta que responde | O que o cliente recebe |
|---|---|---|
| Esquema | a requisição está bem formada? | `422` com `loc` do campo |
| Serviço | isso faz sentido agora? | `409`, `404`, `400` com mensagem |
| Banco | isso continua verdadeiro? | erro convertido pelo serviço |

Tabela: A camada de cima responde rápido e barato; a de baixo responde
sempre.

## Camada 1: o esquema valida a forma

```python title="app/schemas/produto.py" numbered
class ProdutoCriar(BaseModel):
    nome: Annotated[str, Field(min_length=2, max_length=120)]
    preco: Annotated[Decimal, Field(gt=0, decimal_places=2)]
    estoque: Annotated[int, Field(ge=0)] = 0
    categoria: Categoria
    validade: date | None = None
```

O esquema sabe tudo que pode ser decidido **olhando só a requisição**. Ele
não precisa do banco, não precisa do usuário logado, não precisa de hora.

A recompensa é que essa validação acontece antes da sua função rodar, custa
microssegundos e não abre transação.

## Normalizar é parte de validar

```python title="normalizacao.py" numbered
from pydantic import field_validator


class ProdutoCriar(BaseModel):
    nome: str
    email_contato: str | None = None

    @field_validator("nome")
    @classmethod
    def limpar_nome(cls, v: str) -> str:
        return " ".join(v.split())

    @field_validator("email_contato")
    @classmethod
    def minusculo(cls, v: str | None) -> str | None:
        return v.strip().lower() if v else None
```

`" ".join(v.split())` faz três coisas numa linha: tira espaço das pontas,
colapsa espaços internos e normaliza tabulação e quebra de linha. `"  Tomate
   italiano \n"` vira `"Tomate italiano"`.

:::key
Normalize na **borda**, uma vez, na entrada. Se a limpeza acontecer no
serviço, o esquema aceita sujeira; se acontecer na consulta, cada consulta
precisa lembrar. A borda é o único lugar em que "todo dado que entrou está
limpo" é uma frase verdadeira.
:::

:::pitfall
Normalizar e comparar precisam usar a **mesma** regra. Se o cadastro grava
`"tomate italiano"` em minúsculas e a busca de duplicidade compara com o
texto original, dois produtos iguais passam. Normalização é um par: a
gravação e a consulta têm de concordar.
:::

## Camada 2: o serviço valida o contexto

```python title="app/services/produto.py" numbered
def criar(self, dados: ProdutoCriar) -> Produto:
    if self.repo.buscar_por_nome(dados.nome):
        raise ProdutoJaExiste(dados.nome)

    produtor = self.repo_produtor.buscar(dados.produtor_id)
    if produtor is None:
        raise ProdutorNaoEncontrado(dados.produtor_id)
    if not produtor.ativo:
        raise ProdutorInativo(produtor.id)

    if dados.preco < produtor.preco_minimo:
        raise PrecoAbaixoDoMinimo(produtor.preco_minimo)

    ...
```

Nenhuma dessas quatro regras cabe no esquema, porque todas dependem de algo
que não veio na requisição: o que já existe, quem é o produtor, qual o preço
mínimo dele.

:::key
A pergunta que separa as duas primeiras camadas: *para decidir isto, eu
preciso consultar alguma coisa?* Se não, é esquema. Se sim, é serviço. Essa
regra não tem exceção e resolve praticamente toda dúvida de "onde eu ponho
essa validação".
:::

## Camada 3: o banco garante

```python title="restricoes.py" numbered
from sqlalchemy import CheckConstraint, UniqueConstraint


class Produto(Base):
    __tablename__ = "produto"
    __table_args__ = (
        UniqueConstraint("nome", name="uq_produto_nome"),
        CheckConstraint("preco > 0", name="ck_produto_preco"),
        CheckConstraint("estoque >= 0", name="ck_produto_estoque"),
    )
```

O banco é a única camada que vale para **todo mundo**: a sua API, o script
de importação da madrugada, a correção feita à mão no `psql` numa
sexta-feira, e a segunda instância da aplicação rodando em paralelo.

:::warning
Sem `CHECK (estoque >= 0)`, a garantia de estoque não-negativo depende de
que todo caminho de código lembre de conferir. A história do capítulo
@cap:classes-e-objetos — quatro produtos com estoque negativo — é exatamente
o que acontece quando o sexto caminho esquece.
:::

## Validação entre campos

```python title="model_validator.py" numbered
from pydantic import model_validator


class PeriodoBusca(BaseModel):
    inicio: date
    fim: date

    @model_validator(mode="after")
    def periodo_coerente(self):
        if self.fim < self.inicio:
            raise ValueError("fim não pode ser antes do início")
        if (self.fim - self.inicio).days > 366:
            raise ValueError("período máximo de um ano")
        return self
```

Isso ainda é camada 1 — não consulta nada. Regra entre campos da mesma
requisição pertence ao esquema, por mais "de negócio" que ela pareça.

## A mensagem que o cliente recebe

```text
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "preco"],
      "msg": "Input should be greater than 0",
      "input": "-5.00",
      "ctx": {"gt": 0}
    }
  ]
}
```

Quatro informações úteis: o **tipo** do erro, que permite tratamento
programático; o **caminho** até o campo; a mensagem legível; e o valor
recebido.

A mensagem vem em inglês. Traduzi-la é possível e tem uma armadilha:

:::pitfall
Traduzir `msg` e manter `type` é a decisão certa. Traduzir e **remover** o
`type` transforma a resposta em algo que só humano consegue interpretar — e
quem consome uma API é um programa. O cliente deve poder decidir o que fazer
lendo `type` e `loc`, e mostrar `msg` para a pessoa.
:::

## Validar a saída também

```python title="saida.py" numbered
@router.get("/{produto_id}", response_model=ProdutoLer)
def buscar(produto_id: int, servico: ServicoDep):
    return servico.buscar(produto_id)
```

O `response_model` não só filtra: ele **valida**. Se o serviço devolver um
produto com `criado_em` nulo, e o esquema declarar `datetime` obrigatório, a
resposta falha com `500` — e isso é desejável. Um `500` no seu log é melhor
que uma resposta malformada que o cliente vai tentar interpretar.

:::trivia
Validar a saída parece desperdício: os dados vieram do seu próprio banco. Na
prática, é o que pega migração incompleta, campo que virou nulo sem que
ninguém revisasse o esquema, e o resultado de uma consulta que mudou de
formato. O custo é baixo desde o Pydantic v2, e o benefício é encontrar o
problema no seu servidor em vez de no cliente do outro.
:::

## Onde a validação **não** deve estar

Três lugares em que ela aparece e não deveria:

- **No router.** Um `if` de regra dentro da rota é regra fora do serviço, e
  ela não vale para quem chamar o serviço por outro caminho.
- **No repositório.** Ele guarda; validar ali some na implementação em
  memória e o teste passa a mentir.
- **Só no cliente.** Validação no front é para experiência do usuário, nunca
  para segurança. Toda requisição pode ser montada à mão.

:::summary
- Esquema valida forma; serviço valida contexto; banco garante sob
  concorrência.
- A pergunta que decide a camada: preciso consultar algo para decidir isto?
- Normalize na borda, uma vez — e use a mesma regra ao comparar.
- Regra entre campos da mesma requisição ainda é esquema.
- Mantenha `type` e `loc` na resposta de erro; traduza só `msg`.
- `response_model` valida a saída e transforma dado inconsistente em erro
  seu, não do cliente.
:::

:::checkpoint
Você decide em que camada cada regra mora, normaliza entrada sem
inconsistência, e produz respostas de erro que um programa consegue tratar.
:::

:::exercise level=1
Acrescente ao `ProdutoCriar` a validação de que `validade`, quando
informada, precisa ser uma data futura.

:::answer
```python
from datetime import date

from pydantic import field_validator


@field_validator("validade")
@classmethod
def validade_futura(cls, v: date | None) -> date | None:
    if v is not None and v <= date.today():
        raise ValueError("validade precisa ser futura")
    return v
```
Usar `date.today()` dentro de um validador amarra o teste ao relógio. Em
projeto com testes sérios, a data de referência entra por configuração ou por
um parâmetro de contexto — e o capítulo @cap:testando-services trata disso.
:::

:::exercise level=2
Implemente a regra "produto de categoria `verdura` não pode ter validade
maior que 7 dias" — e diga em que camada ela mora.

:::answer
Camada 1, o esquema: ela envolve dois campos da mesma requisição e não
consulta nada.

```python
@model_validator(mode="after")
def validade_de_verdura(self):
    if self.categoria is not Categoria.VERDURA:
        return self
    if self.validade is None:
        return self
    if (self.validade - date.today()).days > 7:
        raise ValueError(
            "verdura não pode ter validade maior que 7 dias"
        )
    return self
```
Se a regra fosse "validade máxima definida por categoria numa tabela de
parâmetros", ela mudaria de camada — passaria a exigir consulta e viraria
serviço.
:::

:::exercise level=3
A cooperativa exige que o preço nunca fique abaixo do preço mínimo do
produtor, que é cadastrado e muda ao longo do tempo. Onde essa validação
mora? E o que acontece com os produtos já cadastrados quando o produtor
aumenta o mínimo?

:::answer
A validação mora no **serviço**: ela depende de consultar o produtor. Não
cabe no esquema, porque `preco_minimo` não vem na requisição.

```python
if dados.preco < produtor.preco_minimo:
    raise PrecoAbaixoDoMinimo(
        produtor.preco_minimo, dados.preco
    )
```

A segunda pergunta é a interessante, e ela não tem resposta técnica: é uma
decisão de negócio que o código vai ser obrigado a tomar de um jeito ou de
outro. Três caminhos possíveis:

**Nada acontece.** A regra vale só na gravação. Produtos antigos continuam
abaixo do mínimo, e o sistema fica permanentemente em um estado que ele
próprio recusaria criar. É a opção mais comum e a menos honesta.

**Reajuste automático.** Ao aumentar o mínimo, todo produto do produtor
abaixo dele sobe. É atraente e perigoso: um erro de digitação no cadastro do
produtor reajusta o catálogo inteiro, e ninguém autorizou preço nenhum.

**Sinalizar e exigir ação.** Os produtos abaixo do mínimo ganham um status
de pendência e saem da vitrine até alguém resolver. Mais trabalho e é o que
preserva as duas verdades — a regra vale e ninguém mexeu em preço sem
decidir.

O que **não** é aceitável é a quarta opção, que costuma vencer por omissão:
não perguntar. A validação vai para o serviço, o mínimo vai subir algum dia,
e o sistema vai se comportar de um dos três jeitos acima — escolhido por
acidente em vez de por decisão. Vale registrar a pergunta e levá-la a quem
pode respondê-la, que é a Dona Neuza, não o time.
:::
