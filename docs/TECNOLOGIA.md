# Tecnología de clasificación y representación semántica

## Implementado

**IA local no significa ChatGPT:** el encoder multilingüe y el OCR corren en tu PC. ChatGPT/OpenAI y Claude son externos; el renombrado con sus APIs es una función separada y consentida. El encoder local calcula representaciones para similitud, no es un asistente conversacional con las mismas capacidades que ChatGPT.

1. **Extracción MIME:** biblioteca estándar de Python. Se conserva el original y se extrae texto plano o HTML sin acceso a recursos remotos. Alternativas MIME no se cuentan dos veces. Se conserva texto citado para contexto y una vista auxiliar del texto nuevo. PDF, DOCX y adjuntos de texto se extraen en procesos separados con límites. Tesseract eng/spa, Pillow y PDFium aportan OCR de imágenes y PDF escaneados. Formatos no soportados, cifrado, fallos y límites quedan explícitos y requieren revisión. Leer texto no equivale a comprender gráficos, fotos u objetos incrustados.
2. **Embeddings multilingües locales:** Sentence Transformers con PyTorch CPU y `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Se descarga desde el repositorio público del modelo. `trust_remote_code=False`, pesos safetensors y revisión del modelo registrada cuando está disponible. Textos largos: fragmentos por IDs de token, todos procesados, promedio ponderado por longitud y normalización. El promedio puede diluir temas minoritarios: no equivale a razonamiento perfecto sobre una conversación.
3. **Referencia clásica:** TF-IDF + TruncatedSVD (LSA) con scikit-learn y vectores normalizados. Se evita densificar 30.000 × vocabulario; el ajuste usa representación dispersa y el paso de predicción se hace en lotes.
4. **Descubrimiento:** MiniBatchKMeans, semilla fija y un número de grupos acotado que crece aproximadamente con la raíz del número de documentos únicos. Padres mediante otra agrupación de centroides. Es una heurística de dos niveles, no una ontología óptima demostrada. Se deduplican textos exactos al descubrir grupos.
5. **Asignación:** similitud coseno con centroides; hasta dos grupos cuando hay evidencia geométrica suficiente. El resto va a revisión. La similitud no está calibrada como probabilidad. Los casos nuevos reutilizan la estructura congelada.
6. **Nombres:** términos TF-IDF representativos; API opcional OpenAI/Anthropic para nombres con ejemplos limitados y consentimiento. El modelo externo no puede ejecutar acciones ni decidir borrar.
7. **SKOS:** exportación `ontology.skos.jsonld` con `ConceptScheme`, `Concept`, `prefLabel`, `broader` e `inScheme`. SKOS representa la organización; no es el algoritmo que la descubre. No se utiliza un razonador OWL.
8. **Entidades:** dominios de remitente frecuentes. No hay aún desambiguación avanzada de personas o empresas que compartan dominios.
9. **Planes:** hashes de versión/contenido, cuenta verificada, límites de cambios, registro durable y reversión de etiquetas nuevas. Políticas opcionales para etiquetas futuras conocidas; sin borrado automático.

## Por qué estas técnicas

Son componentes conocidos de recuperación de información, NLP y aprendizaje no supervisado. La alternativa ligera permite comparar coste y comportamiento; el motor neural aporta similitud multilingüe sin enviar los correos a una API. No hace falta entrenar una red desde cero ni instalar MySQL.

BERTopic/HDBSCAN son alternativas razonables para comparar posteriormente: **no son el motor implementado**. Tampoco se utiliza aprendizaje supervisado a partir de correcciones todavía. La evaluación actual mide acuerdo con etiquetas humanas, pero la selección de la mejor combinación requiere datos y un test independiente.

## Fuentes

- [Sentence-BERT, Reimers y Gurevych, 2019](https://arxiv.org/abs/1908.10084): representaciones de frases para similitud.
- [Embeddings multilingües por destilación, 2020](https://arxiv.org/abs/2004.09813).
- [Ficha del modelo multilingüe usado](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2): arquitectura, licencia y alcance; respeta sus términos y los de sus dependencias.
- [scikit-learn: agrupación de documentos](https://scikit-learn.org/stable/auto_examples/text/plot_document_clustering.html).
- [scikit-learn: clasificación de documentos](https://scikit-learn.org/stable/auto_examples/text/plot_document_classification_20newsgroups.html).
- [SKOS, recomendación W3C](https://www.w3.org/TR/skos-reference/).
- [Introduction to Information Retrieval, Manning, Raghavan y Schütze](https://nlp.stanford.edu/IR-book/): fundamentos de recuperación de información, clasificación y agrupación.

El libro alojado en Stanford es una referencia de fundamentos, **no aval de Stanford a este repositorio**. No hay evidencia de que «los mejores expertos» utilicen exactamente esta configuración ni de que sea la mejor para toda bandeja. La confianza se gana con calidad medida sobre el dominio concreto, no con el nombre de una institución.
