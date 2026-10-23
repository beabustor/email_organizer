# Especificación, prioridades y seguridad

## Objetivo acordado

Sistema local que estudie unos 30.000 correos, descubra temas y entidades a partir del contenido, proponga una jerarquía humana revisable y demuestre su calidad antes de organizar el histórico y el correo nuevo.

Código público reutilizable; cada persona configura cuentas y claves en su PC. Gmail primero; Outlook/Hotmail después. No vincular el repositorio a una cuenta particular.

## Principios

- El cuerpo y la conversación son evidencia principal junto con metadatos. No confundir análisis de cabeceras con comprensión completa.
- Separar tema, entidad, tipo documental y acción. Gmail permite varias etiquetas anidadas sin duplicar mensajes.
- Descubrir antes de fijar carpetas. El catálogo actual es una referencia de diagnóstico.
- Registrar contenido procesado, omitido y fallido. No fingir cobertura, confianza o precisión.
- Coste visible y acotado. Preferir reglas/modelos locales cuando funcionen. IA externa opcional con consentimiento. Límite de llamadas no equivale a presupuesto monetario.
- Sin borrado automático por clasificación. Revisión, trazabilidad y pruebas de reversión antes de ampliar acciones remotas.

## Fases de implementación en orden

### 1. Adquisición del contenido — siguiente prioridad

Añadir opción explícita de descarga de cuerpos Gmail/MBOX. Parsear MIME y texto HTML sin abrir enlaces o imágenes remotas. Conservar mensaje, conversación, origen y versión del parser. Reanudar, deduplicar y distinguir mensajes completos/parciales. Migraciones SQLite compatibles.

**Aceptación:** pruebas de texto, HTML, multipart, idiomas/codificaciones, citas, firmas, mensajes largos, partes vacías e interrupciones. Los fallos no se descartan silenciosamente. Descargar un cuerpo no autoriza enviarlo a IA.

### 2. Motor semántico local

Evaluar embeddings multilingües, fragmentación de textos largos y agregación por mensaje/conversación. Índices y cachés privados. Comparar BERTopic/HDBSCAN con alternativas por estabilidad y utilidad. Documentar requisitos y licencias antes de instalar modelos grandes.

**Aceptación:** cobertura real del contenido, ejemplos representativos, mensajes sin grupo, consumo de recursos y reanudación. Agrupación no equivale a calidad de clasificación demostrada.

### 3. Taxonomía y entidades

Borrador personalizado con sinónimos, padres/hijos, evidencia e identificadores estables, inspirado en SKOS. Resolver entidades con evidencia: un dominio no equivale siempre a una organización. Revisar fusiones/divisiones y controlar proliferación de etiquetas.

**Aceptación:** versión aprobada, ejemplos trazables y migración al cambiar nombres. No aplicar una nueva ontología sin invalidar aprobaciones afectadas.

### 4. Calidad independiente

Datos revisados y test independiente, separado por conversaciones/duplicados y tiempo. Comparar reglas, TF-IDF + clasificador lineal y embeddings + clasificador multietiqueta. Mostrar precisión, recall y F1 por categoría, cobertura, tamaño de muestra e incertidumbre.

**Aceptación:** informe reproducible, con categorías aptas/no aptas para automatización según objetivos acordados. No convertir confianza declarada de la IA en precisión demostrada. Véase METODO_Y_CALIDAD.md.

### 5. Operaciones Gmail y correo nuevo

Aplicar propuestas aprobadas por lotes con registro y reversión probada. Historial incremental Gmail, manejo de caducidad del cursor y reconciliación. Cola de revisión, detección de temas nuevos y correcciones. Outlook/Hotmail posteriormente con Graph y sus propias pruebas.

**Aceptación:** operaciones idempotentes, límites, recuperación y deshacer. Cada acción (etiquetar, archivar, papelera) tiene su política y permiso; esta versión no implementa las dos últimas.

## Requisitos antes de uso masivo o desatendido

Estas son tareas pendientes; no una certificación de seguridad del código actual:

- OAuth por mínimo privilegio y fases: evaluar un modo de solo lectura para adquisición; solicitar escritura al aplicar. Actualmente se solicita `gmail.modify` desde la conexión inicial.
- Aprobaciones ligadas a una versión o hash del plan, no solo al ID de mensaje. Un CSV antiguo debe rechazarse si cambió la propuesta. Hoy ese control estricto no existe.
- Previsualización exacta de todas las acciones, máximo de cambios por ejecución y límites por cuenta. Detenerse ante anomalías.
- Registro durable y recuperación entre petición remota y confirmación local; deshacer únicamente etiquetas añadidas por el programa, preservando las previas.
- Reintentos, cuotas, errores de permisos, mensajes desaparecidos y credenciales caducadas probados. Prueba de integración real sobre una cuenta de prueba con datos ficticios.
- Tokens en llavero; datos locales protegidos mediante permisos, cifrado de disco y copias de seguridad verificadas. La base SQLite actual no está cifrada por la aplicación.
- Texto de emails tratado como datos no confiables: no ejecutar instrucciones, seguir enlaces ni abrir adjuntos. Un prompt por sí solo no es aislamiento suficiente.
- Políticas explícitas por tipo de dato enviado a IA, minimización, coste estimado/consumo y límites; timeout y recuperación sin exponer cuerpos o claves en errores.
- Dependencias reproducibles, revisión de vulnerabilidades y validación en Windows/macOS/Linux. Las instrucciones de instalación no equivalen a pruebas en esos tres sistemas.

## Qué funciona hoy

Importación de cabeceras, inventario, ontología opcional de cabeceras con IA, reglas temáticas, entidades por dominio, revisión CSV y etiquetas aprobadas. Pruebas con datos ficticios y API simulada. Sin certificación de seguridad ni evaluación semántica sobre correo real.

## Qué no se necesita ahora

MySQL, Docker, servidor público, entrenamiento de redes desde cero o cientos de carpetas prefijadas. SQLite basta inicialmente. No instalar BERTopic ni un LLM local solo para aparentar que el motor completo existe.
