# Motor semántico y protocolo del correo nuevo

Diseño del siguiente paso; **todavía no implementado**. El código actual aporta inventario, borrador de ontología con IA opcional, reglas temáticas, entidades por dominio y aprobación de etiquetas.

## Descubrimiento del histórico

1. Copia local: importar cabeceras y, con consentimiento, texto de los correos. No empezar con todos los adjuntos. Separar texto citado, firmas y contenido repetido para que no dominen los grupos.
2. Embeddings: un modelo multilingüe local convierte cada mensaje o conversación en un vector semántico. Evaluar el modelo y sus requisitos antes de elegirlo; el rendimiento depende del PC y la longitud de los textos.
3. Agrupación: probar HDBSCAN para descubrir grupos con tamaños diferentes y permitir mensajes sin grupo. Comparar con alternativas de agrupación jerárquica. UMAP puede ayudar a explorar o reducir dimensiones, pero hay que comprobar que no destruya relaciones útiles.
4. Taxonomía: extraer términos, entidades y ejemplos representativos de cada grupo. Usar un modelo de lenguaje local o externo para proponer nombres y relaciones padre/hijo. La similitud entre vectores no garantiza una jerarquía conceptual correcta.
5. Validación: revisar ejemplos de cada grupo, mensajes ambiguos y cobertura. Comparar granularidad, errores y carpetas redundantes. Versionar la estructura aceptada antes de aplicarla.

No hace falta entrenar una red neuronal desde cero con los 30.000 mensajes. Un modelo de embeddings preentrenado suele ser un punto de partida más económico. No se debe prometer un número fijo de carpetas: depende del contenido, el propósito del usuario y el nivel de detalle que resulte útil.

## Protocolo posterior

```text
Mensaje nuevo
  → importar de forma incremental e idempotente
  → comprobar reglas y protecciones aprobadas
  → recuperar ejemplos similares del índice local
  → clasificador entrenado con correcciones del usuario
  → confianza suficiente: proponer etiquetas existentes
  → confianza insuficiente: cola de revisión
  → tema nuevo repetido: propuesta de nueva subcarpeta
```

Se pueden entrenar clasificadores ligeros multietiqueta sobre embeddings cuando haya suficientes ejemplos revisados. Hay que separar entrenamiento y validación por conversaciones y tiempo para evitar evaluar con duplicados del entrenamiento. Los umbrales deben basarse en precisión medida, no en el número de confianza que declare un modelo de lenguaje.

El protocolo debe distinguir tema, entidad y acción: «Facturas», «Proveedor X» y «Revisar para borrar» son dimensiones distintas. Nunca deducir borrado de la similitud semántica. La categoría de seguridad y las aprobaciones tienen prioridad sobre recomendaciones del modelo.

La automatización de etiquetas puede habilitarse por regla o categoría tras validar su calidad. El archivado, la papelera y los cambios de ontología requieren políticas separadas. Se registran versión de modelo, ontología, evidencia, cambios y correcciones; los cambios remotos deben tener un mecanismo de reversión antes de habilitar acciones más amplias.

## Lo que hay que medir antes de automatizar

- Cobertura sobre mensajes importados y cobertura sobre contenido realmente analizado.
- Precisión por categoría, mensajes ambiguos y falsos positivos sensibles.
- Número de etiquetas útiles y volumen de mensajes por subcarpeta.
- Tiempo, almacenamiento y coste real del proceso en el PC del usuario.
- Deriva: remitentes, temas y lenguaje nuevos frente al histórico.

Los vectores, textos e índices también son datos privados. Deben quedar fuera de Git y protegidos igual que el correo original. Un sistema completamente local necesita descargar modelos y disponer de RAM y almacenamiento suficientes; no elimina los requisitos de privacidad ni validación.
