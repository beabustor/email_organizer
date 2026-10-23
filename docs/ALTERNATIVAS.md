# Soluciones existentes y componentes reutilizables

Sí: ya existen organizadores con IA, gestores de filtros, sincronizadores y herramientas de OCR. Antes de ampliar este proyecto conviene comparar alternativas. Revisión documental de los repositorios oficiales: **23 de octubre de 2026**. No se han instalado ni evaluado con una cuenta real en esta comparación; sus README no demuestran precisión, seguridad ni coste sobre tu histórico.

## Alternativas para el correo

| Proyecto y fuente | Qué documenta | Qué comprobar para nuestro objetivo |
| --- | --- | --- |
| [Inbox Zero](https://github.com/elie222/inbox-zero#readme) | Asistente de correo con IA para Gmail/Outlook, cliente de correo y autoalojamiento. También documenta guardado de adjuntos en Drive/OneDrive. | Es el primero que probaría si buscas una aplicación ya hecha. Verifica proveedor/modelo, datos enviados y coste. Autoalojamiento no garantiza inferencia local. No hemos verificado descubrimiento global de jerarquía sobre 30.000 mensajes, OCR de todos los adjuntos ni calidad medida en español/inglés. |
| [gmailctl](https://github.com/mbrt/gmailctl#readme) | Configuración declarativa de filtros Gmail, comparación de cambios y aplicación de reglas. Código Go, licencia MIT. | Adecuado para reglas conocidas y mantenibles. Los filtros de Gmail no sustituyen al análisis semántico del texto de adjuntos mediante OCR. Su gestión de filtros puede reemplazar configuración existente: revisar su procedimiento de migración. |
| [Lieer](https://github.com/gauteh/lieer#readme) | Descarga local Maildir y sincronización bidireccional de etiquetas entre Gmail y notmuch, con sincronización incremental. | Útil si prefieres ese ecosistema local. No es por sí mismo el descubridor semántico de carpetas que buscamos. Revisa conflictos y permisos: sus operaciones remotas no tienen las mismas reglas que nuestros planes aprobados. |

No hay que usar los tres ni conectarlos simultáneamente. Si varias herramientas escriben etiquetas o filtros, pueden interferir entre sí. Empieza por una prueba acotada y revisa sus mecanismos de recuperación.

## Herramientas para documentos y OCR

| Proyecto y fuente | Qué aporta | Relación con este repositorio |
| --- | --- | --- |
| [Docling](https://github.com/docling-project/docling#readme) | Conversión de documentos, estructura de PDF, OCR y opciones de modelos visuales; ejecución local. Código MIT; los modelos tienen licencias propias. | Candidato a comparar para adjuntos complejos antes de ampliar nuestros lectores. No organiza Gmail por sí mismo. No está integrado: habría que medir calidad, memoria, tiempos y aislamiento de documentos no confiables. |
| [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx#readme) | Sistema de gestión, indexación y archivo de documentos. Código GPL-3.0 según metadatos del repositorio. | Alternativa si el problema principal es archivar documentos. No debe confundirse con organizar todo el histórico dentro de Gmail; no añadimos aquí gestión documental empresarial. |

Las licencias MIT indicadas proceden de los metadatos/README consultados. GitHub devuelve `NOASSERTION` para Inbox Zero y Lieer: eso no significa que carezcan de licencia. Antes de copiar código, consulta los archivos de licencia y condiciones de la versión concreta, incluidos modelos y dependencias. Esta comparación no autoriza a reutilizar cualquier componente sin revisar sus términos.

## Qué conviene hacer aquí

1. **Evaluar Inbox Zero antes de construir más interfaz o automatización.** Si cubre tus requisitos de privacidad, clasificación y revisión, puede ahorrar desarrollo. No prometemos que este proyecto sea mejor.
2. **Comparar Docling con el OCR actual** usando adjuntos ficticios y luego una muestra privada revisada, especialmente documentos donde el orden de lectura es importante. No adoptar una dependencia mayor solo por su lista de funciones.
3. **Mantener las garantías del organizador al reutilizar componentes:** lectura inicial, estado de extracción incompleta, planes exactos aprobados, límites de escritura, registro y reversión; sin borrado automático.
4. **Comparar resultados con el mismo conjunto revisado**, idiomas, categorías, coste y cobertura. Véase [el protocolo de calidad](METODO_Y_CALIDAD.md). Ninguno de estos enlaces acredita una clasificación perfecta ni aval institucional.

La diferencia que buscamos validar aquí es estudiar el histórico completo con procesamiento local de contenido y adjuntos, proponer jerarquía temática y entidades, dejar incertidumbres visibles y ofrecer candidatos de limpieza por tema. No hemos comprobado que otra solución reúna exactamente todas esas funciones, ni que la combinación actual sea la mejor.
