# Glossary — PHP One (en)

Fixed names for both volumes (`php-one-v1-en` and `php-one-v2-en`). The
Portuguese book is the source; this table only keeps the translation
consistent. Code identifiers follow the case of the original
(`snake_case` stays `snake_case`, `PascalCase` stays `PascalCase`).

## Not translated

Casa Amarela (the library — "the Casa Amarela Library"), CasaAmarela
(namespace), Vera, Tainá, Dedé, Caio, Iolanda and every other person's name;
titles of books in the catalog (*O Cortiço*, *Vidas Secas*…); PHP, SQL,
Laravel and package names; `R$` amounts and Brazilian dates.

## Domain

| pt-BR | en |
|---|---|
| acervo | catalog |
| livro / livros | book / books |
| exemplar / exemplares | copy / copies |
| tombo / tombos | accession / accessions (accession number) |
| leitor / leitores | reader / readers |
| empréstimo / emprestimo(s) | loan / loan(s) |
| emprestar | lend (reader side: borrow) |
| devolução / devolver | return |
| devolver_ate / devolverAte | due_on / dueOn |
| devolvido_em / devolvidoEm | returned_at / returnedAt |
| retirado_em | borrowed_at |
| adquirido_em | acquired_at |
| cadastro_em | registered_at |
| prazo / prazo_em_dias | loan period / loan_days |
| multa / multas | fine / fines |
| multa_em_centavos | fine_in_cents |
| multa_por_dia | fine_per_day |
| dias_de_atraso / diasDeAtraso | days_late / daysLate |
| atrasado(s) / em atraso | overdue |
| centavos / reais | cents / reais |
| titulo / autor / ano / assunto | title / author / year / subject |
| status: disponivel · emprestado · restauro · extraviado · danificado · reservado | available · on_loan · in_repair · lost · damaged · reserved |
| StatusExemplar | CopyStatus |
| estado (do exemplar) | status; values good · on_loan · in_repair · damaged · lost |
| situação | situation / state |
| infantil · juvenil · literatura | children · young_adult · literature |
| documento (CPF do leitor) | document (ID number) |
| senha | password |
| atendente / bibliotecária | desk clerk / librarian |
| aviso / avisos | notice / notices |
| EnviadorDeAviso | NoticeSender |
| RegrasDeCirculacao | CirculationRules |
| PoliticaDeEmprestimo | LoanPolicy |
| ExcecaoDeDominio | DomainException (class `DomainError` when it clashes) |
| ExemplarIndisponivel | CopyUnavailable |
| LimiteDeEmprestimosAtingido | LoanLimitReached |
| EmprestimoRealizado | LoanCreated |
| AvisarDevolucaoProxima | NotifyUpcomingReturn |
| LivroController · EmprestimoController · DevolucaoController | BookController · LoanController · ReturnController |
| RealizarEmprestimoRequest · StoreLivroRequest | CreateLoanRequest · StoreBookRequest |
| EmprestimoResource · LivroResource · LeitorResource | LoanResource · BookResource · ReaderResource |
| ServicoDeEmprestimo / EmprestimoService | LoanService |
| consulta | query |
| relatório | report |
| doação / termo de doação | donation / donation form |
| capa | cover |
| fuso | time zone |
| feriados | holidays |
| lote | batch |
| fila | queue |
| equipe | staff |
| regra de negócio | business rule |

## The legacy System's files

| pt-BR | en |
|---|---|
| conexao.php | connection.php |
| emprestimo.php | loan.php |
| funcoes.php · funcoes2.php · funcoes2_NOVO.php · funcoes2_NOVO_final.php | functions.php · functions2.php · functions2_NEW.php · functions2_NEW_final.php |
| relatorio.php · relatorio_novo_OK.php | report.php · report_new_OK.php |
| teste.php | test.php |
| Vertexo Sistemas | Vertexo Systems |
| Biblioteca Comunitária Casa Amarela | Casa Amarela Community Library |
| Seu Juvenal | Mr. Juvenal |
| Dr. Aurélio | Dr. Aurélio |

## Database (tables and columns)

| pt-BR | en |
|---|---|
| livros · exemplares · leitores · emprestimos · autores · autor_livro | books · copies · readers · loans · authors · author_book |
| titulo · autor · isbn · assunto · ano | title · author · isbn · subject · year |
| nome · documento · cadastro_em · telefone | name · document · registered_at · phone |
| livro_id · exemplar_id · leitor_id · autor_id | book_id · copy_id · reader_id · author_id |
| tombo · estado (coluna) · status · adquirido_em | accession · status (`condition` is reserved in MySQL) · status · acquired_at |
| retirado_em · devolver_ate · devolvido_em · multa_em_centavos | borrowed_at · due_on · returned_at · fine_in_cents |
| uk_livros_isbn · uk_exemplares_tombo · uk_leitores_documento | uk_books_isbn · uk_copies_accession · uk_readers_document |
| fk_exemplares_livro · idx_emprestimos_leitor | fk_copies_book · idx_loans_reader |
| banco casa_amarela | database casa_amarela (unchanged) |

## Routes and JSON fields

`/livros` → `/books`, `/emprestimos` → `/loans`, `/leitores` → `/readers`,
`/exemplares` → `/copies`; JSON keys follow the column names above.

## Recurring code names

| pt-BR | en |
|---|---|
| multaEmCentavos() | fineInCents() |
| emReais() / reais() | inReais() / reais() |
| chaveDeBusca() | searchKey() |
| devolucao (variável) | checkin |
| funcoes.php | functions.php |
| avisos.php | notices.php |

## Classes

| pt-BR | en |
|---|---|
| Livro · Exemplar · Leitor · Emprestimo · Autor · Editora | Book · Copy · Reader · Loan · Author · Publisher |
| livroDeLinha() · exemplarDeLinha() | bookFromRow() · copyFromRow() |
| conexao.php · acervo.php · multa.php · recibo.php | connection.php · catalog.php · fine.php · receipt.php |
| pacote casa-amarela/acervo | casa-amarela/catalog |
| namespaces CasaAmarela\Acervo · Leitores · Legado · Emprestimos · Recibos · Relatorios | CasaAmarela\Catalog · Readers · Legacy · Loans · Receipts · Reports |
| LivroNovo · LivroNovo2 · LivroDoSistema | BookNew · BookNew2 · SystemBook |
| importar.php | import.php |
| Exemplar: estado() · disponivel() · emprestar() · devolver() · ESTADOS | Copy: status() · isAvailable() · lend() · return() · STATUSES |
| Multa: centavos · diasDeAtraso · valorFormatado() · perdoar() | Fine: cents · daysLate · formatted() · waive() |
| Circulacao\Emprestavel: identificacao() · disponivel() · prazoEmDias() | Circulation\Lendable: identifier() · isAvailable() · loanDays() |
| Classificacao: infantil · didatico · referencia · importado · sonoro · emprestavel() | Classification: children · textbook · reference · imported · audio · lendable() |
| RegistraHistorico · RegistraAuditoria · ItemDeAcervo | RecordsHistory · RecordsAudit · CatalogItem |
| ExemplarIndisponivel · LimiteDeEmprestimosAtingido · LeitorComPendencia · LinhaInvalida | CopyUnavailable · LoanLimitReached · ReaderHasPendingItems · InvalidRow |
| StatusExemplar: Bom · Emprestado · Restauro · Extraviado · rotulo() | CopyStatus: Good · OnLoan · InRepair · Lost · label() |
| StatusEmprestimo: EmAberto · Devolvido · Renovado · EmAtraso | LoanStatus: Open · Returned · Renewed · Overdue |
| Dinheiro: emCentavos() · zero() · mais() · vezes() · formatado() | Money: inCents() · zero() · plus() · times() · formatted() |
| PrazoDeEmprestimo: devolverAte · retirada · atrasadoEm() · diasDeAtraso() | LoanPeriod: dueOn · borrowedAt · isLateOn() · daysLate() |
| Relogio: agora() · RelogioDoSistema · RelogioParado | Clock: now() · SystemClock · FrozenClock |
| Registro · Servicos (registrar, get) · carregarEnv() | Logger · Services (register, get) · loadEnv() |
| Importacao\Importador · bin/importar-doacoes.php | Import\Importer · bin/import-donations.php |
| .env: APP_FUSO · DB_USUARIO · DB_SENHA · PRAZO_EM_DIAS | APP_TIMEZONE · DB_USER · DB_PASSWORD · LOAN_DAYS |
