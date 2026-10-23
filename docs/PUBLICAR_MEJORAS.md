# Heredar al público lo aprendido en tu copia privada

## Qué se puede trasladar

Código general, correcciones, instrucciones de instalación, formatos de configuración sin valores personales, fixtures ficticios y métricas agregadas revisadas. No copiar automáticamente tu repositorio privado entero ni convertirlo en público si contiene información personal.

## Qué permanece local o privado

Credenciales OAuth/API, tokens, correos originales, MBOX, SQLite, índices/vectores, cachés de modelos, informes HTML/CSV, etiquetas personales, ejemplos de conversaciones y logs sin revisar. Los nombres de carpetas, remitentes y rutas locales también pueden revelar información.

## Procedimiento

1. Desarrolla y valida en tu PC con la copia privada. Conserva el commit de código y versiones usados.
2. Separa el cambio de código de las configuraciones y resultados de tu cuenta. Revisa `git status` y `git diff --cached` antes de cada commit. `.gitignore` no elimina secretos que ya estuvieran versionados.
3. Sustituye todo ejemplo real por uno ficticio que reproduzca el mismo problema.
4. Si completaste una evaluación humana, genera un resumen agregado:

```sh
python scripts/export_validation.py
```

Guarda `data/public-validation.json`: no incluye remitentes, asuntos, etiquetas, cuerpos ni rutas del PC. Revísalo igualmente; las métricas agregadas pueden ser información que prefieras no compartir. No incluye `per_label` porque los nombres pueden ser personales.

5. Comparte únicamente los commits o un parche de código revisados, más ese informe si quieres. Puedes abrir una PR al repositorio público desde una rama que contenga solo cambios generales. Si tu repositorio privado no es un fork compatible, traslada los commits revisados a un checkout del público; no hagas un mirror ni fuerces su historial.
6. El agente revisa el diff, lo adapta para no depender de tu cuenta y ejecuta los tests con fixtures ficticios. Revisa las estadísticas para no convertir «funcionó en mi cuenta» en una garantía universal.
7. Fusiona/publica la mejora general. Una validación local documentada puede mejorar el estado de soporte de ese sistema operativo, pero no demuestra calidad para otros buzones.

Un chat no ve tu PC ni tu repositorio privado automáticamente: necesitas compartir el cambio de código o conectar su acceso. No compartas credenciales en el chat para facilitarlo. Si un secreto llegó a un commit, revócalo y revisa el historial; borrarlo del último archivo no deshace la exposición.

## Descripción y temas de GitHub

`config/github.json` contiene la descripción y temas sugeridos, sin datos personales. Se intentó aplicarlos desde esta integración, pero GitHub devolvió `403 Resource not accessible by integration` para descripción y topics, aunque permitió subir código. Ese rechazo no se resuelve con un commit.

Si tienes permisos de administración en GitHub, abre la rueda junto a **About** en la página principal del repositorio y copia la descripción y los temas del archivo. No compartas un token personal para esta tarea. En tu copia puedes ajustar el nombre y descripción manteniendo el alcance y límites reales.
