# Instrucciones de continuidad

- Lee README.md, docs/ESPECIFICACION.md y docs/METODO_Y_CALIDAD.md antes de cambiar el enfoque.
- Objetivo: descubrir una taxonomía personalizada a partir del contenido, no imponer carpetas fijas ni clasificar solo cabeceras.
- Prioridad siguiente: fase 1, contenido MIME Gmail/MBOX. Embeddings, taxonomía aprendida y calidad sobre correo real siguen pendientes.
- Documentación y estado real deben coincidir. Tests funcionales y corpus sintéticos no demuestran calidad semántica.
- Usa el checkout existente. No crees worktrees salvo petición explícita; las tareas cloud ya están aisladas.
- Usa datos ficticios. No leas, imprimas ni publiques secretos o correos para comprobar configuración; comprueba presencia, no valores.
- Datos, claves, tokens, exportaciones, modelos e índices quedan fuera de Git. No insertes valores sensibles en ejemplos, logs o commits.
- Las credenciales locales no se trasladan automáticamente a la nube. No solicites secretos por chat.
- No borres ni archives correo. Preserva aprobación y confirmación para etiquetas. Antes de uso masivo implementa los controles pendientes de la especificación.
- Mantén compatibilidad SQLite con migraciones y pruebas relevantes. No debilites protecciones silenciosamente.
- Ejecuta `python -m unittest discover -s tests -v` para cambios de comportamiento y `python -m pip check` para dependencias, con el Python del entorno virtual.
- Los conectores se prueban con respuestas simuladas salvo acceso autorizado. No afirmes validación real porque pasen mocks.
- No instales modelos grandes sin justificar recursos, origen, licencia y utilidad. No entrenes desde cero por defecto.
