# Dónde ejecutar y guardar el histórico

## Recomendación inicial: tu PC

Para una cuenta personal, empieza en tu ordenador, con sesión privada, disco cifrado y copia de seguridad protegida. No necesitas contratar otra nube ni tener GitHub para ejecutar un ZIP descargado. El PC debe estar encendido mientras trabaja; el programa no instala un servicio permanente.

Un servidor o una máquina virtual puede servir para ejecución continua, pero añade coste, mantenimiento, copias, protección de accesos y configuración del llavero OAuth. Alojarlo tú no convierte en local una llamada a OpenAI o Anthropic. La configuración actual está orientada a escritorio; no se ha validado un despliegue desatendido en una nube distinta.

## ¿Hay que descargar los correos?

Sí, para el análisis local implementado se descarga el contenido mediante Gmail API, incluidos los originales MIME y sus adjuntos. El asistente lo hace: no necesitas exportar manualmente ni usar Google Takeout. También admite MBOX si ya tienes una exportación.

Descargar crea una copia: no mueve ni borra los mensajes de Gmail. La autorización inicial es de lectura. Aplicar etiquetas requiere otra autorización y un plan aprobado.

## Lotes para procesar; visión conjunta para organizar

La descarga es reanudable, y la extracción de adjuntos y el cálculo de embeddings trabajan progresivamente. No necesitas todos los originales en RAM. Para descubrir una estructura coherente se considera el conjunto del histórico extraído, en lugar de inventar carpetas independientes para cada lote. Después, el correo nuevo reutiliza esa estructura.

Eso no significa consumo de memoria constante: el ajuste global necesita memoria para texto, representaciones y agrupación. El tamaño y complejidad de los documentos importan más que el número de mensajes aislado.

**Actualmente se conservan todos los originales en SQLite**, junto con texto y estado de extracción; también se guardan modelos, vectores y planes privados. Procesar por lotes no significa que el programa borre los archivos procesados. No existe aún una política implementada de purga selectiva de originales.

Conserva la copia durante la primera validación: permite repetir OCR o extracción sin volver a descargar. No borres la base para liberar espacio: contiene también estado necesario para revisar, reanudar y deshacer. Una futura purga necesitará controles de integridad y recuperación; borrar registros de SQLite tampoco reduce necesariamente el archivo inmediatamente.

## Cuánto espacio reservar

Consulta [Google One: almacenamiento](https://one.google.com/storage) para distinguir Gmail de Drive y Fotos. Los 15 GB de una cuenta gratuita son compartidos entre esos servicios; una cuenta de pago puede tener más capacidad. El número de correos no determina su peso.

Si Gmail ocupa alrededor de 15 GB, reservar inicialmente **30–50 GB libres** es un margen orientativo para originales, texto extraído, bibliotecas, modelos, vectores y temporales. No es un requisito medido ni una relación fija: comprueba el crecimiento real y reserva también espacio para copias. Los límites de extracción y formatos soportados están en [la instalación](INSTALACION_PC.md).

## GitHub y copias de seguridad

Git sirve para código, documentación y configuración sin secretos. **No guardes correo, adjuntos, SQLite, vectores, informes privados ni credenciales en Git, aunque el repositorio sea privado.** Los binarios y el historial aumentan su tamaño, y borrar un archivo de la última versión no lo elimina del historial.

Para respaldar datos, detén el programa y realiza una copia consistente de `data` en un destino cifrado y con acceso restringido. Los tokens están en el llavero del sistema, fuera de esa carpeta; volver a autorizar puede ser necesario al restaurar. Comprueba que puedes recuperar la copia. Una nube de respaldo es opcional: revisa cifrado y quién dispone de las claves. No uses sincronización de archivos como sustituto de una copia consistente de una base abierta.

El modelo semántico y OCR actuales se ejecutan localmente. El renombrado opcional con OpenAI/Claude envía ejemplos consentidos y tiene facturación API separada de una suscripción de chat. No hace falta contratarlo para analizar el correo.
