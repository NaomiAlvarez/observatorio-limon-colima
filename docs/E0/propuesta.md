### SIAP: análisis de robots.txt y términos de uso
Se consultó `https://nube.agricultura.gob.mx/robots.txt` el 07/11/2026 y el
servidor respondió HTTP 404 (el sitio no publica robots.txt), por lo que no
declara restricciones para programas automatizados. Los datos se obtienen del
portal oficial de Datos Abiertos de la DGSIAP, que los ofrece como archivos CSV
descargables con su diccionario de datos. El sitio remite a los Términos y
Condiciones de gob.mx (https://www.gob.mx/terminos).

Compromisos: descarga solo de los archivos publicados como datos abiertos, un
archivo por año, con pausa de 3 segundos entre descargas, User-Agent que
identifica el proyecto y sin acceso a rutas ajenas a la sección de datos
abiertos. Las fuentes son estadísticas agregadas por municipio y no contienen
datos personales.