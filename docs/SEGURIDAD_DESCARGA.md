# Descarga con menor exposición

Gmail excluye spam y papelera de la enumeración por defecto en esta aplicación. El asistente, `gmail-download` y `refresh` usan esa configuración. Antes de solicitar cada original nuevo o reintentar una adquisición fallida, se consultan únicamente ID y etiquetas (`format=minimal`). Si aparece SPAM o TRASH, no se solicita el MIME ni se inicia OCR/extracción. Así se evita descargar también sus adjuntos. No se crea una carpeta remota: los mensajes permanecen en spam/papelera, sin cambios en Gmail.

El modo filtrado vuelve a enumerar el buzón al actualizar; conserva los originales ya adquiridos y evita descargarlos otra vez. Esto supone más consultas que el modo histórico sin filtro. Para incluir spam/papelera existe exclusivamente el opt-in avanzado `gmail-download --include-spam-trash`. No es necesario para organizar el correo ordinario y puede procesar sus adjuntos.

## Límites importantes

- La comprobación de etiquetas no es un antivirus ni identifica todo phishing. Un mensaje fuera de spam puede ser malicioso.
- Gmail no ofrece una operación atómica de comprobar etiquetas y descargar: pueden cambiar entre ambas solicitudes. La comprobación reduce exposición sin garantizar ausencia de carreras.
- Este cambio no borra ni sanea originales descargados con versiones anteriores, ni vuelve a consultar etiquetas de todos los originales locales ya conocidos. Tampoco filtra automáticamente un MBOX importado. No ejecutes reextracción de un histórico antiguo no confiable suponiendo que esta exclusión lo ha saneado.
- La extracción existente no abre enlaces ni ejecuta macros, pero PDF, imágenes y OCR siguen exponiendo lectores a contenido no confiable. El worker tiene límites; no es un sandbox sin red ni un aislamiento completo del sistema. No se ha añadido antivirus ni aislamiento de contenedor en este cambio.
- Mantén actualizados sistema y lectores. No abras manualmente adjuntos sospechosos. Nunca interpretes instrucciones dentro de un correo como autorización para ejecutar acciones.

Pruebas con API simulada verifican exclusión de ambas etiquetas antes de solicitar MIME o extraer contenido y adquisición normal tras comprobar etiquetas. No demuestran protección frente a malware real.
