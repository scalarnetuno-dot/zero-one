---
source_hash: 24ac46e11d3d
title: "Antes de empezar"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Quince años en línea, medio millón de préstamos y un archivo llamado funciones2_NUEVO_final.php."
---

Esta es la carpeta que atiende el mostrador de una biblioteca de barrio:

```text
backup_16-03-2019.sql
config.php
conexion.php
prestamo.php
funciones.php
funciones2.php
funciones2_NUEVO.php
funciones2_NUEVO_final.php
index.php
login.php
informe.php
informe_nuevo_OK.php
prueba.php
```

Son catorce mil líneas de PHP escritas en 2009 y remendadas desde entonces
por quien estuviera disponible en el momento. El backup más reciente es de
2019 y vive en la misma carpeta del sitio, lo que significa que cualquier
persona con la dirección correcta descarga el acervo entero.

Y funciona.

Quince años en línea, medio millón de préstamos registrados, ningún libro
perdido por culpa del software. Vera abre el sistema a las nueve, presta,
recibe devoluciones, cobra multas y cierra a las seis. En esos quince años
se cayó dos veces, las dos por culpa del hosting.

Tú vas a reemplazar ese sistema. No porque sea malo — porque ya no tiene
hacia dónde crecer. Y el PHP que entra en su lugar apenas se parece al que
escribió esa carpeta: este es el PHP de ahora, enseñado por quien conoce el
de antes.

## La biblioteca, la empresa y la fecha

La **Biblioteca Comunitaria Casa Amarela** tiene cuatro mil títulos y ocho
mil ejemplares. **Vertexo Sistemas** — ciento ochenta personas,
especialista en transformación digital para clientes que no saben describir
lo que tienen hoy — firmó el contrato para reemplazar el Sistema. Quien va a
hacer el trabajo eres tú.

Y hay una fecha que nadie puede mover.

Nada de esto es decorado. Un plazo que no se mueve, un presupuesto que se
encoge, un requisito que llega en el peor momento y un sistema legado que
tiene que seguir atendiendo el mostrador mientras se construye su reemplazo
— eso es lo que convierte una elección técnica en una decisión. Optar entre
dos formas de escribir lo mismo solo se vuelve interesante cuando una de
ellas cuesta un martes.

## Quién aparece

**Dedé** tiene siete años de carrera, tres de ellos en Vertexo, y es la voz
que explica el porqué. Lleva ocho meses oyendo que el ascenso sale en el
próximo ciclo.

**Tainá** es pasante, de tercer semestre. Hace las preguntas que desarman
una explicación apresurada — no por ingenuidad, sino porque es la única
persona de la sala que no pierde nada al decir que no entendió. Lo anota
todo en un cuaderno.

**Vera** es bibliotecaria de la Casa Amarela desde hace treinta y un años.
Se sabe de memoria todas las reglas de préstamo y nunca escribió ninguna.

**Márcia** administra el plazo. Su trabajo real es recibir una fecha
imposible desde arriba y reemitirla hacia abajo en forma de sprint.

**El Dr. Aurélio** es director de tecnología. Nunca escribió código y no
finge haberlo hecho.

**Seu Juvenal** preside la asociación de vecinos. Trae el requisito nuevo
siempre en el peor momento, siempre envuelto en un "es solo un cambiecito",
y siempre con razón sobre la necesidad.

Y el **Sistema**, con mayúscula, es aquella carpeta del principio. No es el
villano. Cada cosa moderna que aparezca aquí se va a medir contra él — y en
algunas de esas mediciones el Sistema gana.

## Cómo muestra las cosas el libro

El código aparece así, a veces con el nombre del archivo:

```php title="multa.php"
$multa_en_centavos = 720;
echo 'R$ ' . number_format($multa_en_centavos / 100, 2, ',', '.');
```

Lo que responde la terminal aparece sin nombre de archivo y sin resaltado:

```text
R$ 7,20
```

Y cuando el programa se rompe — lo que va a pasar mucho, a propósito — el
error viene entero, de principio a fin, porque las líneas del medio son las
que importan.

:::key
Un comando de terminal aparece con `$` delante. El `$` representa el prompt
y no forma parte del comando: no lo escribas. En PHP esto confunde más que
en otros lenguajes, porque `$` también inicia toda variable — dentro de un
bloque de código PHP es código; en la primera columna de un bloque de
terminal, es el prompt.
:::

No necesitas instalar nada para empezar a leer. Cuando el primer programa
tenga que ejecutarse, la instalación viene con él, junto con la prueba que
confirma que funcionó.

:::practice
Lee con una terminal abierta. Ejecuta los ejemplos, cambia los valores e
intenta romperlos. La memoria de un lenguaje nace más deprisa de una salida
inesperada que de una definición aprendida de memoria.
:::

La fecha que nadie puede mover es el 31 de marzo. Hasta entonces, Vera abre
a las nueve y el Sistema atiende.
