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
| estado (do exemplar) | condition |
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
