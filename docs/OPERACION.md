# Operación, revisión y automatización

Ejecuta desde la raíz usando `.venv/bin/python` (macOS/Linux) o `.venv\Scripts\python.exe` (Windows). En ejemplos se abrevia como `python`.

## Flujo de comandos

```sh
python -m email_organizer.cli gmail-download
# O, sin Gmail:
python -m email_organizer.cli import-full /ruta/historico.mbox
python -m email_organizer.cli analyze --backend neural
python -m email_organizer.cli plan
```

`analyze --backend lsa` utiliza el motor ligero. El comando de análisis no instala dependencias por sí mismo; utiliza `run.py` para instalación guiada. El número máximo de grupos es configurable con `--max-topics` (1–60); no se fuerza ese número si hay pocos documentos. `--threshold` es un umbral de similitud geométrica, no una probabilidad calibrada.

Si importaste varias cuentas, usa `--source ORIGEN` para analizar y crear planes por separado. El origen aparece al importar. Un plan nunca mezcla cuentas. `--db RUTA` es una opción global y va antes del subcomando. Por defecto los datos se guardan en `data/organizer.sqlite`.

## Revisar un plan

Abre `data/plans/ID.html` y su CSV. Incluyen estado de contenido, etiquetas exactas, similitud, motivo de limpieza y bytes del original. En el CSV escribe `si` en `aprobar` solo para las filas elegidas:

```sh
python -m email_organizer.cli approve-plan ID --csv data/plans/ID.csv --confirm
python -m email_organizer.cli apply-plan ID --confirm --max-changes 100
```

Para aprobar todo después de revisarlo, sustituye `--csv ...` por `--all`. La aprobación contiene hashes de mensaje, etiquetas y versión. Un CSV de otro plan o un contenido modificado no se acepta. Cambiar la clasificación requiere revisar otro plan.

`apply-plan` añade etiquetas, crea padres y una subcarpeta `Candidatos a borrar` por grupo temático. No elimina INBOX, no archiva, no lleva a papelera. Omite mensajes protegidos al volver a consultar Gmail: destacados, importantes, enviados, borradores, spam y papelera. Todos mantienen resultado local, pero esto significa que no todos se etiquetan remotamente.

## Limpieza por carpeta

Copia `config/cleanup.json` a **`data/cleanup.json`** y edita esa copia privada antes de analizar. El programa la utiliza si existe; así tus remitentes protegidos no acaban en un archivo versionado. Sin copia usa los valores generales de `config/cleanup.json`. Por defecto:

- Newsletter con desuscripción y al menos 365 días.
- Notificación de remitente automático y al menos 730 días.
- No candidato si hay importancia/destacado, fecha desconocida, contenido parcial, remitente protegido, palabras sensibles en asunto o cuerpo o adjuntos sin analizar.
- Los casos de revisión semántica no reciben candidato automático.

Son heurísticas conservadoras, no una garantía. La IA no determina que algo sea prescindible por cercanía a un grupo. Los originales MIME incluyen adjuntos. PDF, DOCX y texto pueden aportar evidencia; imágenes/PDF escaneados requieren Tesseract eng/spa. Si algún adjunto no se pudo procesar, el mensaje queda incompleto y no se propone para limpieza. Gmail puede conservar mensajes en papelera según su política; el programa no gestiona esa retención.

El tamaño mostrado cuenta cada original una vez aunque tenga varias etiquetas. No representa ahorro efectivo ni CO₂. Al conservar copias locales, también existe almacenamiento local que gestionar.

## Reanudar y deshacer

Repite `apply-plan` con el mismo ID para continuar. Guarda el intento antes de pedir el cambio remoto y lo recupera de manera idempotente si se interrumpe.

```sh
python -m email_organizer.cli undo-plan ID --confirm --max-changes 100
```

Retira únicamente las etiquetas que registró como nuevas para ese plan; conserva las que ya existían. Repite para completar el lote si hace falta. No elimina etiquetas/carpetas vacías. Después de iniciar deshacer no se vuelve a aplicar ese plan.

El asistente y la CLI toman un bloqueo de proceso sobre la base para evitar ejecuciones locales solapadas; el sistema lo libera si el proceso termina. Aun así, no ejecutes copias en dos ordenadores sobre la misma cuenta/plan ni edites esas mismas etiquetas manualmente mientras se ejecutan: el registro no puede distinguir una edición concurrente idéntica hecha fuera del programa. Haz copia local antes de migraciones importantes.

## Correo nuevo

```sh
python -m email_organizer.cli refresh
```

Descarga cambios por Gmail history (reconcilia si caduca), clasifica con el modelo guardado y crea un plan. No cambia Gmail.

Tras revisar y aprobar una estructura puedes habilitar etiquetas conocidas:

```sh
python -m email_organizer.cli authorize-automation ID --confirm --max-changes 100
python -m email_organizer.cli refresh --policy data/automation.json
```

La política fija cuenta, versión, etiquetas admitidas y límite. Solo aplica resultados propuestos en categorías permitidas; nunca candidatos de limpieza o revisión. Cambiar estructura/modelo exige nueva aprobación. Omite mensajes ya aplicados, deshechos o protegidos. No ejecuta un clasificador continuamente: programa el comando con Task Scheduler, launchd o cron si lo necesitas. Mantén el ordenador encendido y evita ejecuciones solapadas.

**Autorizar una política no demuestra calidad:** eres tú quien acepta su alcance. Antes de habilitarla, mide resultados y conserva en revisión categorías con evidencia insuficiente. No habilites automatización solo porque la similitud sea alta.

## Evaluación humana

Rellena `etiquetas_correctas` en una copia del CSV con rutas completas separadas por `|`. No copies las propuestas sin revisarlas.

Rellena también `idioma` con `es`, `en`, `mixto` u `otro` para comparar acuerdo por idioma. No se deduce automáticamente del remitente. El motor neural puede compartir temas entre inglés y español sin traducir los originales.

```sh
python -m email_organizer.cli evaluate data/plans/ID.csv
python scripts/export_validation.py
```

La evaluación informa precisión/recall/F1 por etiqueta, exact match e intervalos de confianza. **No acredita independencia:** el descubrimiento pudo ver esos mismos mensajes. Para demostrar generalización reserva correos futuros y sigue [METODO_Y_CALIDAD.md](METODO_Y_CALIDAD.md).

## Actualizar la extracción de adjuntos

Si vienes de 0.2, `analyze` reextrae los originales locales con el parser nuevo sin volver a descargarlos. Tras instalar OCR o lectores, puedes reintentar:

```sh
python -m email_organizer.cli extract-attachments --retry
python -m email_organizer.cli analyze --backend neural
python -m email_organizer.cli plan
```

Los cambios de evidencia invalidan planes anteriores. `adjuntos_estado` en el CSV distingue complete, needs_ocr, encrypted, unsupported, limit, timeout y error. Nunca interpretes un fallo como ausencia de información.

## Datos y privacidad

Nunca subas `data`, CSV/HTML, originales, vectores, claves o tokens. El JSON-LD SKOS no contiene cuerpos, pero sus nombres temáticos pueden revelar información personal. No lo publiques automáticamente. Para llevar mejoras al público consulta [PUBLICAR_MEJORAS.md](PUBLICAR_MEJORAS.md).
