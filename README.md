# Email Organizer · IA local para ordenar tu histórico de Gmail

**Descarga tu correo, analiza el texto completo y descubre una organización por temas y entidades.** Revisa una propuesta de etiquetas anidadas, localiza candidatos de limpieza dentro de cada grupo y reutiliza la estructura para lo nuevo.

**ChatGPT es externo. La IA local de este proyecto es un modelo multilingüe descargado en tu PC; no es ChatGPT.** OpenAI/Claude son servicios externos opcionales y solo reciben ejemplos si lo autorizas.

Proyecto independiente en fase de validación. **Usa inteligencia artificial:** embeddings multilingües locales opcionales, machine learning y procesamiento del lenguaje natural. No exige una suscripción a ChatGPT. No promete una clasificación perfecta ni está avalado por Stanford.

## Empieza en tu PC

1. Instala **Python 3.11 o posterior** desde [python.org](https://www.python.org/downloads/).
2. Descarga **Code → Download ZIP** y descomprime en una carpeta personal.
3. Abre una terminal en la carpeta del README y ejecuta:

```sh
# Windows
py run.py
# macOS / Linux
python3 run.py
```

En Windows también puedes abrir `Iniciar-Windows.bat`. El asistente crea `.venv`, instala dependencias y te guía. No cambia la política de PowerShell ni necesita MySQL, Docker o un servidor. Sigue [la instalación paso a paso](docs/INSTALACION_PC.md) para crear tu autorización de Gmail y elegir el motor.

**La primera descarga del motor neural ocupa cientos de MB de pesos y las bibliotecas pueden ocupar varios GB.** El PC debe permanecer encendido. El tiempo con 30.000 mensajes depende de longitud, adjuntos, red y CPU; no prometemos minutos ni una cantidad fija de carpetas.

## Qué sucede

1. **Descarga completa:** Gmail en modo de solo lectura, originales MIME y texto; o importación de MBOX. Guarda progreso en SQLite. Incluye spam/papelera salvo exclusión explícita.
2. **Análisis local:** procesa todo el texto extraído. El motor neural divide textos largos por tokens y combina todos sus fragmentos; no mira solo el principio.
3. **Descubrimiento:** agrupa documentos y propone dos niveles temáticos. Los nombres iniciales son términos representativos. OpenAI/Claude pueden proponer nombres más humanos si autorizas enviar ejemplos.
4. **Cobertura:** todo mensaje importado recibe propuesta o `Organizador/Revision necesaria`. Esto no equivale a acertar todos: imágenes, cifrado, texto incompleto o señales insuficientes requieren revisión.
5. **Informe privado:** HTML y CSV con etiquetas, fragmentos de ejemplo, estado de extracción, similitud y motivo de limpieza.
6. **Aplicación controlada:** apruebas el plan exacto; solo entonces se pide permiso de escritura y se añaden etiquetas, hasta 100 mensajes por ejecución por defecto. Hay registro y comando para deshacer.
7. **Correo nuevo:** `refresh` descarga cambios y reutiliza el modelo. Por defecto crea propuestas; una política explícita puede autorizar etiquetas conocidas. No automatiza candidatos a borrar ni categorías nuevas.

## Tecnologías reales, no nombres comerciales

| Componente | Implementación |
| --- | --- |
| Extracción de contenido | MIME, pypdf, DOCX/XML y lectores de texto en procesos separados; originales conservados |
| OCR local | Tesseract inglés/español, Pillow y PDFium para imágenes/PDF escaneados |
| Semántica neural local | Sentence Transformers + PyTorch CPU; modelo multilingüe `paraphrase-multilingual-MiniLM-L12-v2` |
| Alternativa ligera | TF-IDF + LSA mediante TruncatedSVD, sin descargar un modelo neural |
| Descubrimiento y jerarquía | MiniBatchKMeans sobre vectores normalizados; agrupación adicional de centroides para padres |
| Nombres explicables | Términos TF-IDF por grupo; renombrado opcional con OpenAI o Anthropic |
| Representación ontológica | Exportación SKOS en JSON-LD: conceptos, etiquetas y relaciones padre/hijo |
| Entidades | Dominios observados; no se presentan como empresas verificadas |
| Almacenamiento | SQLite, JSON y NumPy sin pickle ejecutable; caché de embeddings local |
| Calidad | Etiquetas humanas, métricas por etiqueta e intervalos de confianza |

Estas técnicas tienen bibliografía establecida. **La combinación concreta es una decisión de este proyecto, no una receta certificada de Stanford ni evidencia de ser la mejor para tu bandeja.** Consulta [tecnologías, fuentes y límites](docs/TECNOLOGIA.md) y [cómo demostrar calidad](docs/METODO_Y_CALIDAD.md).

## Carpetas y limpieza por tema

En Gmail son etiquetas anidadas; no se duplica un mensaje por llevar varias:

```text
Organizador/
  Temas/
    Tema01-viajes-alojamiento/
      Grupo001-hotel-reserva-estancia/
        Candidatos a borrar
      Grupo002-vuelo-billete-embarque/
        Candidatos a borrar
  Entidades/
    proveedor.example
  Revision necesaria
```

Los nombres y grupos se descubren en tu histórico. La subcarpeta de candidatos se crea para cada grupo temático aplicado, aunque esté vacía. Los candidatos antiguos reciben además esa etiqueta, **sin moverse ni borrarse**. Se excluyen documentos sensibles detectados, remitentes protegidos y adjuntos sin analizar. Copia [cleanup.json](config/cleanup.json) a `data/cleanup.json` para personalizar tus criterios sin publicar remitentes privados.

**Menos almacenamiento innecesario es el objetivo, no una cifra de CO₂ inventada.** El informe suma bytes de originales candidatos sin duplicarlos por etiquetas. No es espacio liberado: no se ha borrado nada y existe una copia local. Vaciar Gmail y conservar una copia local también consume almacenamiento.

![Bandeja antes: simulación ficticia](docs/images/gmail-antes.svg)
![Propuesta después: simulación ficticia, no resultado garantizado](docs/images/gmail-despues.svg)

## Seguridad y límites actuales

- Tokens en el llavero del sistema, adquisición con `gmail.readonly`, escritura separada. Nunca contraseñas de Gmail.
- Planes con hash de contenido y versión; rechaza aprobaciones obsoletas y cuentas distintas.
- Aplicación reanudable y reversión de etiquetas añadidas por el plan. No borra ni archiva. No elimina las carpetas vacías al deshacer.
- Destacados, importantes, enviados, borradores, spam y papelera se analizan localmente pero se omiten al aplicar etiquetas.
- No abre enlaces remotos ni ejecuta macros o aplicaciones asociadas. **Extrae texto de PDF, DOCX, TXT, CSV y HTML adjuntos; imágenes y PDF escaneados usan OCR local con Tesseract eng/spa.** Si falta OCR, el formato no se soporta o hay un error/límite, pasa a revisión. OCR no equivale a comprender fotografías, diagramas o gráficos; audio, archivos cifrados y otros formatos siguen requiriendo revisión.
- La base local y los vectores no tienen cifrado propio: usa sesión privada, cifrado de disco y una política de copias. No ejecutes aplicación y modificaciones manuales de las mismas etiquetas simultáneamente.
- La similitud no es una probabilidad de acierto. La calidad sobre tu cuenta debe medirse. No hay garantía de 100% de acierto.
- Conector Gmail y fallos/reversión probados con API simulada; sin validación contra tu cuenta real. Las instrucciones Windows/macOS requieren validación en esos equipos.

## Documentación y continuidad

- [Instalar, conectar y ejecutar](docs/INSTALACION_PC.md).
- [Comandos, revisión, automatización y deshacer](docs/OPERACION.md).
- [Arquitectura y próximos límites](docs/ESPECIFICACION.md).
- [Tecnología y referencias](docs/TECNOLOGIA.md).
- [Calidad: qué medir antes de confiar](docs/METODO_Y_CALIDAD.md).
- [Pruebas ejecutadas y límites de esa evidencia](docs/VALIDACION.md).
- [Trasladar mejoras privadas al público sin datos personales](docs/PUBLICAR_MEJORAS.md).
- [Continuar en otra conversación](CONTINUAR_AQUI.md).

Código público o privado, **datos siempre locales y fuera de Git**. Una conversación no obtiene acceso a tu PC por copiar este repositorio. Para IA externa necesitas una clave API con facturación separada de ChatGPT; nunca la pegues en un chat.

## Desarrollo

```sh
python -m venv .venv
# Usa .venv/bin/python o .venv\Scripts\python.exe según tu sistema:
python -m pip install -e '.[gmail,semantic]'
python -m unittest discover -s tests -v
python -m pip check
```

El motor neural se instala aparte desde el asistente. Las pruebas funcionales no se presentan como una medida de calidad sobre correo real. No subas datos privados para contribuir.
