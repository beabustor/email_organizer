# Procedimiento establecido y calidad demostrable

## Estado real

El repositorio tiene pruebas funcionales con datos ficticios; **no tiene una evaluación de calidad sobre correos reales etiquetados**. Ni esas pruebas ni la capacidad de recorrer 30.000 mensajes demuestran precisión semántica. No se publica una cifra de acierto sin un conjunto de evaluación, resultados y método reproducibles.

Se contrastó documentación de los proyectos enlazados abajo el 23 de octubre de 2026. Son métodos establecidos, no una certificación de calidad para correo personal. El motor de contenido descrito a continuación es un diseño pendiente de implementación.

## Procedimiento recomendado

### A. Preparación local del histórico

- Importar todos los mensajes del alcance acordado y comprobar recuentos, fallos y exclusiones.
- Analizar MIME, obtener texto de HTML sin cargar imágenes remotas, y conservar la relación con mensaje y conversación.
- Separar texto nuevo, citas, firmas y avisos legales. Conservar el original para inspección; no confundir limpieza con descartar contexto relevante.
- Detectar idioma, duplicados y boletines casi idénticos. Tratar adjuntos como una fase separada, identificando qué contenido no se ha analizado.
- Dividir textos largos en fragmentos para no perder contenido por límites del modelo. Agregar evidencia por mensaje y conversación.

### B. Descubrimiento, no clasificación definitiva

Usar BERTopic como candidato inicial: embeddings multilingües → reducción dimensional opcional → HDBSCAN → términos representativos con c-TF-IDF. Inspeccionar documentos representativos y mensajes sin grupo. Probar estabilidad ante cambios de parámetros y semillas.

BERTopic permite jerarquías y asignar documentos nuevos, pero un grupo estadístico no equivale automáticamente a una carpeta útil. Separar temas, entidades y acciones; revisar y versionar la taxonomía. Un modelo de lenguaje puede proponer nombres a partir de evidencia, no decidir por sí solo qué es importante para el usuario.

### C. Clasificación del histórico y del correo nuevo

Comparar al menos estos candidatos sobre los mismos ejemplos revisados:

1. Reglas: referencia inicial interpretable.
2. TF-IDF + modelo lineal (por ejemplo regresión logística): referencia clásica, económica y fuerte para texto.
3. Embeddings + clasificador lineal multietiqueta: candidato semántico local.
4. Un modelo de lenguaje como alternativa para casos ambiguos, si aporta mejora suficiente respecto a coste y privacidad.

Elegir por resultados medidos, no por que el modelo sea más grande. Un correo puede tener varias etiquetas; una prueba monoclase no valida por sí sola esa capacidad. Las entidades deben evaluarse aparte de los temas, incluyendo errores de identidad y dominios compartidos.

### D. Correcciones y mantenimiento

Usar aprendizaje activo: pedir revisión de ejemplos inciertos o representativos para mejorar el entrenamiento. Esos ejemplos no sustituyen al test independiente y representativo, porque su selección está sesgada hacia casos difíciles.

Versionar datos, taxonomía, preprocesamiento, modelos y umbrales. Detectar nuevos temas y cambios en el correo entrante. Proponer nuevas subcarpetas cuando haya evidencia repetida, sin reorganizar todo automáticamente.

## Cómo demostrar calidad

1. Definir las categorías y ejemplos positivos/negativos con criterios claros; medir desacuerdos humanos cuando sea viable.
2. Crear una muestra revisada que cubra categorías, remitentes, idiomas, antigüedad y casos difíciles. Un piloto de 200–500 mensajes ayuda a descubrir problemas, pero no demuestra por sí solo precisión en categorías raras.
3. Reservar un test final que no se use para elegir carpetas, entrenar, ajustar prompts ni seleccionar umbrales. Definir la taxonomía con datos de desarrollo antes de anotar ese test. Si se exploró todo el histórico al diseñarla, declarar esa limitación y preferir mensajes futuros para la validación final.
4. Separar por conversación y duplicados; añadir una evaluación temporal con mensajes posteriores. No repartir correos casi iguales entre entrenamiento y test.
5. Medir precisión, recall y F1 por categoría, macro-F1 para no ocultar clases pequeñas y métricas multietiqueta. Mostrar número de ejemplos, matriz de errores y resultados por idioma.
6. Para modelos que se abstienen: informar conjuntamente precisión de lo automatizado y cobertura. Acertar el 99% de solo el 1% más fácil del buzón no demuestra organización del conjunto.
7. Presentar intervalos de confianza y tamaño muestral. Cero errores en una muestra pequeña no significa certeza de ausencia de errores.
8. Repetir la evaluación después de cambios sustanciales de taxonomía o modelo.

## Política propuesta antes de automatizar

Los siguientes son **objetivos de aceptación**, no resultados obtenidos:

- Comenzar solo con propuestas revisables.
- Establecer con el usuario la precisión requerida para cada categoría y el coste de sus errores; por ejemplo, una meta inicial del 95% para etiquetas ordinarias, con evidencia suficiente y margen de incertidumbre explícito.
- Habilitar automatización únicamente en categorías que alcancen el umbral acordado en datos independientes. No usar como prueba el valor de confianza que declare una IA.
- Mantener categorías sensibles y casos ambiguos bajo revisión. No automatizar borrado como consecuencia de un clasificador temático.
- Evaluar por separado el riesgo de proponer «Revisar para borrar». Las reglas conservadoras tampoco garantizan ausencia de documentos importantes.

## Evidencia publicada frente a evidencia propia

El ejemplo oficial de scikit-learn compara clasificadores sobre 20 Newsgroups y muestra cómo cabeceras, firmas y citas pueden inflar resultados. Es una referencia útil, pero ese corpus no representa automáticamente Gmail personal multilingüe. El buen resultado de una biblioteca en un benchmark no se transfiere sin evaluación al buzón del usuario.

## Fuentes consultadas

- [BERTopic: algoritmo y componentes](https://github.com/MaartenGr/BERTopic/blob/master/docs/algorithm/algorithm.md).
- [BERTopic: jerarquías, documentos representativos y predicción de nuevos documentos](https://github.com/MaartenGr/BERTopic#readme).
- [scikit-learn: clasificación de documentos y efecto de los metadatos](https://scikit-learn.org/stable/auto_examples/text/plot_document_classification_20newsgroups.html).
- [scikit-learn: fugas de información y errores frecuentes](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage).
- [scikit-learn: métricas de evaluación](https://scikit-learn.org/stable/modules/model_evaluation.html).
- [modAL: aprendizaje activo y selección por incertidumbre](https://github.com/modAL-python/modAL#readme).

Las fuentes describen técnicas y limitaciones. No acreditan resultados de este repositorio ni que una combinación sea la mejor para todos los usuarios.
