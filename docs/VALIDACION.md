# Evidencia de validación disponible

Validación de desarrollo realizada en Linux con Python 3.12, el 23 de octubre de 2026. No usa credenciales ni correos del usuario.

## Pruebas funcionales

```sh
python -m unittest discover -s tests -v
```

Cubren extracción MIME, HTML pasivo, alternativas con contenido adicional, adjuntos no interpretados, codificaciones, importación idempotente, descarga/historial simulados, fallo sin avanzar cursor, migración de una base anterior, bloqueo local, clasificación del cuerpo, textos largos por tokens, cobertura explícita, caché, planes obsoletos, manipulación de acciones, límites, cuenta incorrecta, protección remota, recuperación tras éxito remoto y fallo local, deshacer, política de automatización y nombres IA inválidos.

Las pruebas de Gmail y de API de nombres usan respuestas simuladas. No prueban OAuth real ni permisos/cuotas de una cuenta.

## Modelo neural real

Se descargó y cargó `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revisión `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, con pesos safetensors y ejecución de código remoto deshabilitada.

- Comprobación de frases: similitud aproximada 0,878 entre una factura en español y su traducción inglesa, frente a 0,029 con una frase sobre un gato. Es una comprobación puntual, no un benchmark de precisión.
- Flujo completo con ocho mensajes ficticios ES/EN: cuatro sobre alojamiento y cuatro sobre senderismo. Se procesaron cuerpos, se obtuvieron ocho resultados y se agruparon las variantes lingüísticas dentro de sus dos temáticas. Se generó plan local sin aplicación remota.

Versiones usadas: Sentence Transformers 5.7.0, Transformers 4.57.6, PyTorch 2.14.1+cpu, scikit-learn 1.9.1, NumPy 2.5.4 y SciPy 1.18.1. Las dependencias tienen rangos en pyproject.toml; no hay un lockfile universal para todos los sistemas. Transformers se limita a 4.x porque se detectaron incompatibilidades de tokenizer con 5.x.

## Volumen sintético

```sh
python scripts/validate_synthetic.py --messages 30000
```

En la comprobación realizada: 30.000 originales ficticios importados, 30.000 cuerpos procesados con **LSA**, 30.000 resultados, 30.000 operaciones propuestas y cero aprobaciones automáticas. El proceso completo tardó unos 53 segundos en esta máquina con textos sintéticos breves. **No representa el tiempo de descargar Gmail, procesar adjuntos o ejecutar 30.000 correos reales con el motor neural.**

## Arranque y dependencias

Se ejecutó `run.py`, creó/verificó el entorno y abrió el menú; se salió sin conectar cuentas. `pip check` no detectó dependencias incompatibles. Se verificaron enlaces locales de documentación y XML de los SVG.

Hay CI definida para Windows/macOS/Linux, pero su existencia no implica que sus ejecuciones hayan pasado. Consulta los resultados de Actions de tu commit. No se afirma instalación validada en los tres sistemas desde este entorno Linux.

## Lo que no está demostrado

Precisión sobre un histórico personal real, calibración de confianza, calidad de todas las categorías, estabilidad ante deriva, independencia estadística de una evaluación, calidad de entidad más allá del dominio, comprensión de adjuntos y ahorro ambiental. Sigue METODO_Y_CALIDAD.md antes de atribuir calidad demostrada o habilitar una política desatendida.
