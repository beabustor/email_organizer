# Especificación y estado de implementación

## Objetivo

Sistema local para estudiar un histórico completo de correo, descubrir temas y entidades, proponer una jerarquía comprensible, demostrar calidad con ejemplos revisados y reutilizar la estructura para organizar correo nuevo. Objetivo adicional: facilitar limpieza de almacenamiento con candidatos explicables dentro de cada grupo, sin borrado automático ni cifras ambientales inventadas.

## Implementado en 0.2

- Importación de originales MIME y texto Gmail/MBOX, parser pasivo y estado de extracción.
- Gmail en solo lectura para adquisición, sesión de escritura separada, historial incremental y reconciliación al caducar.
- Embeddings locales multilingües con todos los fragmentos del texto, o TF-IDF/LSA como referencia ligera.
- Grupos y padres descubiertos, nombres por términos y renombrado API opcional.
- Resultados para todos los registros: propuesta o revisión. Adjuntos/cifrado no comprendidos se declaran, no se ocultan.
- Exportación SKOS y entidades por dominio, con límites para no generar miles de etiquetas.
- Plan HTML/CSV con hash, motivo de limpieza y bytes originales. Aprobación exacta, límites, cuenta verificada, registro de intento y deshacer.
- Política opcional para etiquetar correo nuevo en categorías conocidas; nunca limpieza/revisión automática.
- Evaluación de etiquetas humanas con métricas por categoría e incertidumbre; exportación pública agregada opcional.
- Asistente local, preparación de entorno y guías de instalación/contribución privada a pública.

## Límites que siguen abiertos

- No existe precisión universal garantizada ni evaluación independiente de una cuenta real. Las pruebas funcionales no prueban calidad humana.
- El modelo de embeddings y la agrupación son candidatos razonables, no «el mejor» sistema demostrado. Falta comparar alternativas sobre ejemplos reales revisados.
- No se hace OCR ni se extraen PDF/audio/otros adjuntos. Se conserva su original y se protege su limpieza por defecto.
- No hay resolución avanzada de entidades, detección robusta de idioma por mensaje ni clasificador supervisado que aprenda de correcciones.
- La base no tiene cifrado propio. Se apoya en permisos de archivos/sesión y cifrado del sistema.
- Las versiones de modelos y planes no deben editarse a mano; no son artefactos firmados contra un atacante con control del PC.
- No se soportan procesos de escritura simultáneos sobre un mismo plan. Reversión y ediciones externas concurrentes idénticas no son distinguibles.
- No hay instalador firmado, aplicación gráfica completa o servicio de fondo. Hay asistente de terminal e informe HTML local.
- Outlook/Hotmail sigue pendiente. La compatibilidad de instalación en cada SO requiere validación y CI.
- Las APIs Gmail y de nombres se han probado con dobles; el usuario debe validar su OAuth y cuenta antes de cambios amplios.

## Requisitos antes de uso desatendido

Revisar la estructura, comprobar ejemplos, evaluar categorías y sus errores, aprobar una política acotada y probar deshacer. Mantener fuera de automatización clases con calidad insuficiente. Tener espacio y copias locales protegidas, revisar retención/coste del proveedor si se envían ejemplos, evitar ejecuciones solapadas y conservar trazabilidad de versión.

La intención no es «forzar que todo parezca bien clasificado», sino que no exista correo ignorado: cada uno tiene un estado explícito. `Revision necesaria` es un resultado honesto, no evidencia de clasificación temática correcta.
