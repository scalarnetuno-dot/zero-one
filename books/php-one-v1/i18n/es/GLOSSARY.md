# Glosario — PHP One (es)

Nombres fijos para los dos volúmenes (`php-one-v1-es` y `php-one-v2-es`).
El libro en portugués es la fuente; esta tabla solo mantiene la traducción
coherente. Los identificadores siguen la convención del original y van sin
tildes ni eñes (`prestamo`, `anio`).

## No se traduce

Casa Amarela, CasaAmarela (namespace), Vera, Tainá, Dedé, Caio, Iolanda y
todos los nombres de personas; títulos de libros del acervo; PHP, SQL,
Laravel y nombres de paquetes; montos en `R$` y fechas de Brasil.

## Dominio

| pt-BR | es |
|---|---|
| acervo | acervo |
| livro / livros | libro / libros |
| exemplar / exemplares | ejemplar / ejemplares |
| tombo / tombos | registro / registros (número de registro) |
| leitor / leitores | lector / lectores |
| empréstimo / emprestimo(s) | préstamo / prestamo(s) |
| emprestar | prestar |
| devolução / devolver | devolución / devolver |
| devolver_ate / devolverAte | devolver_hasta / devolverHasta |
| devolvido_em / devolvidoEm | devuelto_en / devueltoEn |
| retirado_em | retirado_en |
| adquirido_em | adquirido_en |
| cadastro_em | registrado_en |
| prazo / prazo_em_dias | plazo / plazo_en_dias |
| multa / multas | multa / multas |
| multa_em_centavos | multa_en_centavos |
| dias_de_atraso / diasDeAtraso | dias_de_atraso / diasDeAtraso |
| atrasado(s) | atrasado(s) |
| titulo / autor / ano / assunto | titulo / autor / anio / tema |
| status: disponivel · emprestado · restauro · extraviado · danificado · reservado | disponible · prestado · restauracion · extraviado · danado · reservado |
| StatusExemplar | EstadoEjemplar |
| estado (do exemplar) | condicion |
| infantil · juvenil · literatura | infantil · juvenil · literatura |
| documento | documento |
| senha | contrasena |
| atendente / bibliotecária | encargado de mostrador / bibliotecaria |
| aviso / avisos | aviso / avisos |
| EnviadorDeAviso | EnviadorDeAviso |
| RegrasDeCirculacao | ReglasDeCirculacion |
| PoliticaDeEmprestimo | PoliticaDePrestamo |
| ExcecaoDeDominio | ExcepcionDeDominio |
| ExemplarIndisponivel | EjemplarNoDisponible |
| LimiteDeEmprestimosAtingido | LimiteDePrestamosAlcanzado |
| EmprestimoRealizado | PrestamoRealizado |
| LivroController · EmprestimoController · DevolucaoController | LibroController · PrestamoController · DevolucionController |
| EmprestimoResource · LivroResource · LeitorResource | PrestamoResource · LibroResource · LectorResource |
| ServicoDeEmprestimo / EmprestimoService | PrestamoService |
| consulta | consulta |
| relatório | informe |
| doação | donación |
| capa | portada |
| fuso | zona horaria |
| lote | lote |
| fila | cola |
| equipe | equipo |

## Archivos del Sistema (legado)

| pt-BR | es |
|---|---|
| funcoes.php · funcoes2.php · funcoes2_NOVO.php · funcoes2_NOVO_final.php · funcoes2_NOVO_final_v2.php | funciones.php · funciones2.php · funciones2_NUEVO.php · funciones2_NUEVO_final.php · funciones2_NUEVO_final_v2.php |
| conexao.php · emprestimo.php · relatorio.php · relatorio_novo_OK.php · teste.php · aviso.php | conexion.php · prestamo.php · informe.php · informe_nuevo_OK.php · prueba.php · aviso.php |

## Registro

Se tutea al lector (tú), español neutro. Diálogos con raya (—), como en el
original.

## Columnas del esquema (v1)

| pt-BR | es |
|---|---|
| exemplares.estado: bom · emprestado · restauro · danificado · extraviado | ejemplares.condicion: bueno · prestado · restauracion · danado · extraviado |
| chave `status` em arrays (disponivel · emprestado · restauro) | clave `status` (disponible · prestado · restauracion) |
| leitores: nome · documento · cadastro_em · telefone | lectores: nombre · documento · registrado_en · telefono |
| removido_em | eliminado_en |
