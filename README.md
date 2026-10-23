# Email Organizer: descubrir la organización de tu correo

Proyecto local para estudiar un histórico de unos 30.000 correos, descubrir sus temas y entidades, construir una jerarquía comprensible y utilizarla para organizar el correo nuevo.

**La estructura debe surgir del contenido del usuario, no de una lista fija de carpetas.** Un mensaje podrá organizarse por temática, entidad y tipo documental. La calidad se medirá con ejemplos revisados y evaluación independiente.

## Empieza aquí

1. Lee el estado real de esta página.
2. Sigue [la instalación en Windows, macOS o Linux](docs/INSTALACION_PC.md).
3. Configura Gmail y, opcionalmente, la API de OpenAI o Anthropic según esa guía.
4. Para continuar el desarrollo en otra conversación, usa [CONTINUAR_AQUI.md](CONTINUAR_AQUI.md).

Puedes mantener tu copia de código pública o privada. **Correos, bases, exportaciones, índices y credenciales deben permanecer locales y fuera de Git**, incluso si el repositorio es privado. No necesitas MySQL, Docker ni un servidor web.

Una cuenta de ChatGPT o su contraseña **no sirve como credencial API**. OpenAI necesita una clave API con facturación independiente de ChatGPT. Nunca escribas claves ni contraseñas en el repositorio o en una conversación.

## Procedimiento que guía el proyecto

```text
Copiar histórico → extraer contenido y conversaciones → explorar temas y entidades
    → proponer taxonomía → revisar y versionar → evaluar calidad independiente
    → clasificar histórico → aplicar etiquetas aprobadas
    → organizar correo nuevo y aprender de correcciones
```

El diseño combina extracción de texto, embeddings locales, descubrimiento de temas, clasificación multietiqueta y aprendizaje activo. SKOS orientará la representación de categorías; no sustituye al modelo que descubre contenido. Organización temática y propuestas de borrado son políticas distintas.

Consulta la [especificación](docs/ESPECIFICACION.md), el [motor semántico propuesto](docs/MOTOR_SEMANTICO_PROPUESTO.md) y el [procedimiento de calidad con fuentes](docs/METODO_Y_CALIDAD.md).

## Estado real

| Capacidad | Estado |
| --- | --- |
| Importar cabeceras desde Gmail OAuth o MBOX | Implementado |
| Inventario de todos los mensajes importados | Implementado |
| Borrador de ontología IA con cabeceras, cobertura y reanudación | Implementado; probado con respuestas simuladas |
| Reglas temáticas, entidades por dominio, propuestas CSV | Implementado |
| Etiquetas Gmail anidadas con aprobación explícita | Implementado; sin validación contra una cuenta real aquí |
| Descargar y analizar cuerpos completos y conversaciones | **Pendiente: siguiente prioridad** |
| Embeddings locales, índice semántico y agrupación del contenido | Pendiente |
| Resolver entidades más allá del dominio | Pendiente |
| Calidad demostrada con correos reales revisados | Pendiente |
| Historial incremental Gmail y automatización del correo nuevo | Pendiente |
| Outlook/Hotmail, interfaz gráfica y deshacer automático | Pendiente |

**No es todavía el organizador semántico completo ni está listo para cambios masivos sin supervisión.** Instalarlo permite preparar conexiones y probar el flujo inicial de cabeceras. No se debe presentar ese flujo como análisis completo del contenido. Los casos ambiguos deberán quedar en revisión.

## Qué sucederá al ejecutarlo hoy

- `gmail-sync`: autorización en navegador e importación de cabeceras; sin cambios en Gmail.
- `inventory`: informe local del histórico importado.
- `ai-ontology`: borrador basado en dominios y asuntos; requiere consentimiento, clave API y presupuesto. Indica cobertura parcial o completa de cabeceras.
- `classify`, `ai-classify`, `review`: propuestas locales, sin modificar Gmail.
- `approve`: registra aprobación local.
- `gmail-apply --confirm`: añade etiquetas aprobadas; no borra, archiva ni mueve a papelera.

La instalación no conecta cuentas ni inicia procesos de fondo. Empieza por datos ficticios o una exportación local. Para una cuenta real, prueba unas pocas propuestas antes de considerar un lote mayor. Consulta los [requisitos funcionales y de seguridad pendientes](docs/ESPECIFICACION.md).

## Simulación visual de la base actual

Ejemplos ficticios, **no resultados del motor semántico pendiente**. Se mantienen los mensajes en Recibidos: únicamente se añaden etiquetas.

![Antes: Gmail ficticio con mensajes mezclados](docs/images/gmail-antes.svg)

![Después: etiquetas aprobadas, sin borrar ni archivar](docs/images/gmail-despues.svg)

## Documentación

- [Instalar y configurar en tu PC](docs/INSTALACION_PC.md).
- [Guía detallada de Gmail y revisión por CSV](docs/GUIA_PASO_A_PASO.md).
- [Descubrimiento de ontología e IA actual](docs/ONTOLOGIA_E_IA.md).
- [Método y evaluación de calidad](docs/METODO_Y_CALIDAD.md).
- [Especificación y prioridades](docs/ESPECIFICACION.md).
- [Referencia de los comandos y reglas actuales](docs/REFERENCIA_CLI.md).

## Desarrollo y validación

Desde la raíz, usando el Python del entorno virtual:

```sh
python -m unittest discover -s tests -v
python -m pip check
```

Las pruebas actuales verifican reglas, persistencia, caché, cobertura, límites y operaciones simuladas. **No acreditan precisión semántica sobre tu correo.** La comprobación sintética de 30.000 mensajes tampoco es un benchmark sobre cuerpos reales. No se han validado instalaciones Windows/macOS desde este entorno Linux.
