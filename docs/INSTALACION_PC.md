# Instalación local paso a paso

## 1. Requisitos

- Python 3.11 o posterior; Python 3.12 es una opción inicial. [Descarga oficial](https://www.python.org/downloads/).
- Windows, macOS o Linux con navegador e Internet y una sesión de usuario privada.
- Llavero seguro del sistema: Windows Credential Locker, macOS Keychain o Secret Service/KWallet en Linux.
- Gmail y un proyecto personal en Google Cloud para OAuth. No una contraseña de aplicación.
- Excel o LibreOffice opcionales para el CSV. Git es opcional si descargas ZIP.
- Para el motor neural se recomienda disponer de 16 GB de RAM y varios GB libres para bibliotecas/modelos, más espacio para los originales del buzón. Es una recomendación, no un rendimiento validado en todos los equipos. No hace falta GPU.

No necesitas MySQL, Node.js o Docker. El tamaño del buzón y adjuntos determina cuánto disco hace falta, no solo los 30.000 mensajes. Los originales MIME incluyen adjuntos. Antes de empezar, revisa el espacio disponible y protege el disco con cifrado del sistema. No instales en una carpeta compartida o sincronizada sin quererlo.

## 2. Descargar

En GitHub puedes usar el repositorio original, hacer tu copia pública o importarlo como privado. Para una copia privada utiliza **+ → Import repository → Private**; un fork público no es la vía para privatizarlo.

Abre **Code → Download ZIP**, descomprime y abre una terminal en la carpeta que contiene `run.py`. No pongas credenciales en commits aunque tu repositorio sea privado.

## 3. Ejecutar

### Windows

Instala Python desde python.org y vuelve a abrir PowerShell. Ejecuta:

```powershell
py --version
py run.py
```

También puedes abrir `Iniciar-Windows.bat`. No cambies la política de ejecución de PowerShell. Si `py` no existe pero `python --version` muestra una versión compatible, usa `python run.py`.

### macOS

Instala Python desde python.org, abre Terminal en la carpeta del proyecto:

```sh
python3 --version
python3 run.py
```

También hay `Iniciar-macOS.command`, si tu sistema permite ejecutarlo. Si macOS restringe archivos descargados, utiliza el comando de Terminal en lugar de desactivar protecciones del sistema.

### Linux

Comprueba `python3 --version`. En Debian/Ubuntu, si faltan paquetes:

```sh
sudo apt update
sudo apt install python3 python3-venv python3-pip gnome-keyring libsecret-1-0
python3 run.py
```

La versión debe ser 3.11 o posterior. En otras distribuciones usa sus paquetes oficiales. Por SSH puede no haber un llavero operativo: no rebajes a almacenamiento de tokens sin protección.

**Qué ocurre:** `run.py` crea `.venv`, instala Gmail y scikit-learn y abre el asistente de terminal. Todavía no autoriza cuentas ni cambia Gmail. No hay interfaz web pública: los resultados se abren como un informe HTML local.

## 4. Autorizar Gmail

1. En [Google Cloud Console](https://console.cloud.google.com/) crea un proyecto personal.
2. Habilita **Gmail API**.
3. Configura **Google Auth Platform**, nombre y correo de contacto.
4. En modo **Testing / Pruebas**, añade tu dirección como usuario de prueba.
5. Crea un cliente OAuth de tipo **Desktop app / Aplicación de escritorio**.
6. Descarga el JSON como `data/credentials.json`. Crea `data` si hace falta. No lo publiques ni lo pegues en un chat.
7. En el asistente elige **Descargar Gmail y analizar todo**. Se abre el navegador para elegir cuenta y autorizar lectura.

Se descarga todo lo accesible por Gmail, incluidos spam/papelera. Para excluirlos utiliza el comando avanzado de la guía de operación. La descarga inicial puede tardar bastante: guarda cada mensaje y se puede reanudar. Después utiliza el historial de Gmail; si caduca, vuelve a enumerar y reconcilia.

**La descarga no modifica Gmail.** El token de lectura se guarda en el llavero bajo `email-organizer`, cuenta `readonly`. La escritura se solicita por separado cuando decidas aplicar un plan y usa la cuenta `default` del mismo servicio. Si no hay llavero compatible, se detiene. La aplicación mantiene una sesión por modalidad; no es un gestor OAuth multicuenta simultáneo.

En proyectos de pruebas puede caducar la autorización. Una distribución OAuth a otros usuarios puede requerir verificación de Google; una cuenta de empresa puede restringir aplicaciones.

## 5. Elegir motor

- **Neural multilingüe:** el asistente puede instalar PyTorch CPU, Sentence Transformers y Transformers 4.x. Después descarga `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` desde Hugging Face. Descarga bibliotecas y pesos, no sube tu correo. El texto largo se fragmenta sin recortar al primer bloque.
- **Ligero:** TF-IDF + LSA con scikit-learn. Sirve como referencia local, no equivale a comprensión neural multilingüe.

Para la primera instalación neural se pide confirmación explícita en el PC por su tamaño. No necesitas una cuenta de Hugging Face para el modelo público; se puede aplicar un límite de descarga sin autenticar. Mantén HTTPS/TLS y no aceptes ejecutar código remoto de modelos.

No se promete que un motor sea el mejor en tu histórico: se compara con ejemplos revisados. Una vez entrenada la estructura local, las actualizaciones reutilizan sus vectores y categorías; no redescubren carpetas cada vez.

## 6. Revisar y aplicar

El asistente genera `data/plans/ID.html` y `ID.csv`. El navegador muestra el informe. Las rutas se imprimen en la terminal.

Revisa nombres de grupos, ejemplos, mensajes que requieren revisión y motivos de candidatos. Puedes salir sin cambios. Para probar, escribe `si` solo en unas pocas filas de la columna `aprobar`, conserva el CSV UTF-8 con comas y cierra la hoja antes de continuar. No cambies ID, plan ni hash.

El asistente permite aprobar esas filas o confirmar todo el plan y aplica como máximo 100 mensajes en esa ejecución. Antes de escribir pide otra autorización OAuth con `gmail.modify`. No se borra ni archiva. El informe puede contener fragmentos privados: no lo publiques.

## 7. ChatGPT/Claude opcionales para nombres humanos

El análisis neural principal es local. Opcionalmente una API puede nombrar grupos usando sus términos y hasta dos fragmentos representativos de 1500 caracteres por grupo. Esos fragmentos pueden contener información sensible; autoriza solo si aceptas enviarla al proveedor.

El propio asistente ofrece este paso después del análisis: puedes pulsar Enter para omitirlo o elegir proveedor, modelo, consentimiento y clave oculta. Si falla, conserva la estructura previa y permite seguir revisando. También existe el comando avanzado siguiente.

Una suscripción a ChatGPT no es una clave API. Para OpenAI usa [platform.openai.com](https://platform.openai.com/); para Claude, [Anthropic Console](https://console.anthropic.com/). Facturación separada. Elige un modelo disponible en tu cuenta y sustituye `TU_MODELO`.

Desde el Python de `.venv`:

```sh
python scripts/name_topics.py --provider openai --api-model TU_MODELO --max-calls 4 --consent-send-examples
```

En Windows el ejecutable es `.venv\Scripts\python.exe`; en macOS/Linux `.venv/bin/python`. El asistente pide una clave con entrada oculta y no la guarda en disco. También reutiliza `EMAIL_ORGANIZER_AI_KEY` si ya está configurada, sin imprimirla. No carga `.env` automáticamente.

Se permiten diez grupos por llamada; el límite debe cubrir el catálogo completo. No es un presupuesto en euros. Cambiar nombres produce una versión nueva y obliga a revisar otro plan. No cambia los centroides ni autoriza acciones remotas. Se han probado sus límites con respuestas simuladas, no una cuenta de pago real.

## 8. Actualizar y detener

Vuelve a ejecutar `run.py`, opción **Actualizar Gmail con la estructura existente**, o utiliza `refresh` según [OPERACION.md](OPERACION.md). Por defecto solo crea propuestas. Para automatizar etiquetas conocidas hace falta una política explícitamente aprobada. El programa no instala un servicio de fondo: puedes programar `refresh` con el programador de tareas del sistema.

Ctrl+C detiene el proceso; conserva pasos confirmados y caché. La fase de ajuste de grupos puede recomenzar si se interrumpe antes de guardar su versión. Conserva `data` de forma privada al actualizar código. El ZIP no se actualiza solo.

## 9. Errores y retirada de acceso

- Comprueba Python, carpeta del proyecto y espacio libre. Usa `scripts/check_setup.py` con el Python de `.venv` para diagnóstico sin valores de secretos.
- No eludas TLS, llavero o permisos. Si falla un modelo, revisa red/espacio; puedes escoger el motor ligero explícitamente.
- Si Google deniega acceso, revisa Gmail API, cliente de escritorio, usuarios de prueba y políticas de empresa.
- Si falla la IA externa, revisa modelo y facturación en su consola, sin pegar claves en chats.
- Para retirar Gmail, usa [Conexiones de tu cuenta](https://myaccount.google.com/connections) y elimina tokens `readonly`/`default` del llavero si procede.
- Revocar acceso no elimina etiquetas ni datos locales. Revoca claves API desde la consola si sospechas exposición.
- Las instrucciones de cada sistema no equivalen a una validación en todos ellos. Comparte errores anonimizados, no logs con correo real.
