# Instrucciones de continuidad

- Lee README.md, docs/ESPECIFICACION.md, docs/TECNOLOGIA.md y docs/METODO_Y_CALIDAD.md.
- Objetivo: descubrir organización por contenido completo y entidades, validar calidad y reutilizar la estructura. La base ya implementa cuerpos, motores locales, planes, limpieza por grupo y actualización; no vuelvas al enfoque de solo cabeceras.
- No prometas acierto universal: todo mensaje tiene propuesta o revisión. Similitud, tests funcionales y corpus sintéticos no son precisión sobre correo real.
- Usa checkout existente, sin worktrees salvo petición. Las tareas cloud están aisladas.
- Usa fixtures ficticios. No leas/imprimas secretos para diagnosticar configuración; solo presencia. No pidas claves en el chat.
- Correos, tokens, claves, vectores, modelos, planes e informes permanecen privados y fuera de Git. Sigue docs/PUBLICAR_MEJORAS.md para heredar mejoras generales.
- Nunca borres o archives correo. Respeta hash/versiones, aprobación, verificación de cuenta, límites y protecciones remotas. No mezcles política temática y candidatos de limpieza.
- Guarda intentos antes del cambio remoto y conserva reversión/idempotencia. No habilites escrituras simultáneas sin diseñar bloqueo y recuperación.
- Mantén migraciones SQLite compatibles. Artefactos JSON/NumPy sin pickle ejecutable. No rebajes TLS ni aceptes código remoto de modelos.
- Ejecuta `python -m unittest discover -s tests -v` con el entorno virtual y `python -m pip check`. Pruebas Gmail/API simuladas no acreditan integración real.
- Documenta la validación neural real y sus límites; cambios de dependencias o tokenizer requieren probar textos largos y el pipeline real.
- No atribuyas aval a Stanford ni a otra institución sin evidencia; referencia técnicas y resultados concretos.
