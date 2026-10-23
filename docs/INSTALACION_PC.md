# Instalar en tu ordenador, paso a paso

## 1. Qué debes tener

| Requisito | Para qué |
| --- | --- |
| Windows, macOS o Linux con sesión personal protegida | Ejecutar el programa local |
| Python 3.11 o posterior; 3.12 es una opción inicial razonable | Ejecutar el código y crear un entorno aislado |
| Navegador e Internet | Descargar dependencias y autorizar Gmail |
| Cuenta Google con acceso a Gmail y Google Cloud Console | Crear tu cliente OAuth personal |
| Llavero del sistema operativo | Guardar tokens OAuth sin archivo de texto plano |
| Excel o LibreOffice, opcional | Revisar las propuestas CSV |
| Cuenta API OpenAI/Anthropic, opcional | Los comandos IA externos actuales |
| Git, opcional | Clonar y actualizar; no hace falta si descargas ZIP |

No necesitas MySQL, Docker, Node.js, GPU ni un servidor para la versión actual. El motor local de embeddings aún no está implementado: no instales modelos por adelantado. Para esa fase se medirán RAM y disco; disponer de 16 GB de RAM sería una preferencia inicial, no un requisito demostrado ni una garantía de rendimiento.

El espacio necesario depende del volumen real del buzón, cuerpos, adjuntos y modelos, no solo de tener 30.000 mensajes. Comprueba el tamaño de tu correo y deja espacio para una copia y sus índices. La versión actual solo guarda cabeceras y no tiene cifrado propio de SQLite. Usa cifrado de disco y evita carpetas compartidas o sincronizadas si no quieres copias externas.

**Resultado de esta instalación:** podrás probar el flujo de cabeceras. No instala el motor semántico completo pendiente. Esta guía no supone que se haya validado el programa en los tres sistemas; las pruebas de desarrollo realizadas aquí son Linux con Python 3.12.

## 2. Copia el código, público o privado

1. En GitHub abre el repositorio de origen.
2. Si quieres tu propia copia pública, puedes hacer un fork. Si la quieres privada, utiliza **+ → Import repository** y selecciona **Private**; un fork público no es la vía para privatizarlo.
3. Abre tu repositorio y pulsa **Code → Download ZIP**.
4. Descomprime el ZIP en una carpeta personal; entra donde están `README.md` y `pyproject.toml`.
5. Abre una terminal en esa carpeta.

Copiar código no conecta Gmail. No incluyas `data`, claves, CSV, correos o índices al subir cambios a GitHub, sea público o privado. Los archivos ignorados no se cifran ni se protegen frente a subidas manuales.

## 3. Instala Python y dependencias

### Windows

Descarga Python desde [python.org](https://www.python.org/downloads/), ejecuta el instalador y habilita PATH si ofrece esa opción. Cierra y abre PowerShell. Ejecuta en la carpeta del proyecto:

```powershell
py --version
py -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[gmail]"
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe scripts/check_setup.py
```

No hace falta activar scripts de PowerShell ni cambiar su política de ejecución. Si `py` no existe pero `python --version` muestra 3.11 o posterior, puedes usar `python -m venv .venv`.

### macOS

Instala Python desde [python.org](https://www.python.org/downloads/macos/). Usa Terminal en la carpeta del proyecto:

```sh
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[gmail]'
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_setup.py
```

### Linux

Comprueba `python3 --version`. En Debian/Ubuntu, si necesitas Python y soporte de entornos virtuales:

```sh
sudo apt update
sudo apt install python3 python3-venv python3-pip gnome-keyring libsecret-1-0
```

Si la versión disponible es anterior a 3.11, utiliza una versión de Python compatible instalada por el método recomendado para tu distribución. Otras distribuciones tienen nombres de paquetes diferentes. El llavero debe estar disponible y desbloqueado en tu sesión gráfica; instalar paquetes no garantiza que esté operativo, especialmente por SSH.

Después, en la carpeta del proyecto:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[gmail]'
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_setup.py
```

**Qué sucede:** se crea `.venv`, se instalan bibliotecas oficiales de Google y soporte del llavero y se ejecutan pruebas con datos ficticios. El comprobador no lee claves ni inicia sesiones; sus resultados son diagnósticos, no una certificación de seguridad. Si los tests fallan, resuelve el error antes de conectar cuentas. No uses `sudo pip`, no desactives TLS y no cambies a un almacén de tokens en texto plano.

## 4. Configura Gmail OAuth

No uses tu contraseña de Gmail ni una contraseña de aplicación.

1. Abre [Google Cloud Console](https://console.cloud.google.com/) y crea un proyecto personal.
2. Habilita **Gmail API** en la biblioteca de APIs.
3. Configura la aplicación en **Google Auth Platform**, con nombre y correo de contacto.
4. Configura la audiencia. En modo **Testing / Pruebas**, añade tu cuenta en **Test users / Usuarios de prueba**.
5. Crea un cliente OAuth de tipo **Desktop app / Aplicación de escritorio**.
6. Descarga el JSON y guárdalo como `data/credentials.json`, dentro del proyecto. Crea la carpeta `data` si hace falta.
7. Comprueba que el archivo no acaba en `.json.json` y que está excluido de Git.

No publiques el JSON, aunque el cliente sea de escritorio. La aplicación solicita actualmente `gmail.modify`, que permite modificar correo: **la autorización de Google es más amplia que las acciones que usa este código**. Añadir un modo de adquisición de solo lectura es una mejora de seguridad pendiente. La versión actual usa ese permiso para etiquetar, pero no contiene comandos de borrado o archivado.

En Windows:

```powershell
.venv\Scripts\python.exe -m email_organizer.cli gmail-sync
.venv\Scripts\python.exe -m email_organizer.cli inventory
```

En macOS/Linux:

```sh
.venv/bin/python -m email_organizer.cli gmail-sync
.venv/bin/python -m email_organizer.cli inventory
```

Se abre el navegador para elegir cuenta y autorizar; luego se importan cabeceras. No se cambia Gmail. El token va al llavero del sistema, no al JSON de credenciales. Actualmente hay una sesión OAuth por usuario del sistema. Google puede exigir nueva autorización en proyectos en pruebas; una aplicación distribuida puede necesitar verificación y una cuenta de empresa puede imponer restricciones.

**Antes de clasificar, espera a que termine la importación.** Repetirla conserva IDs ya importados, pero todavía no refleja los cambios posteriores de esos mensajes. Para probar sin OAuth puedes importar un MBOX; consulta la guía de comandos. Nunca adjuntes ese MBOX al chat o al repositorio.

## 5. IA opcional: OpenAI o Anthropic

Para OpenAI se configura una **clave API de [platform.openai.com](https://platform.openai.com/)**, no el usuario/contraseña de ChatGPT. ChatGPT Plus/Pro y la facturación API son servicios separados. Para Claude, usa una clave de [Anthropic Console](https://console.anthropic.com/). No necesitas las dos.

1. Crea la clave desde la consola del proveedor y revisa su configuración de facturación, uso y tratamiento de datos.
2. Elige un identificador de modelo disponible en tu cuenta. No se incluye un modelo predeterminado para evitar invocar uno incompatible o caro sin decisión explícita.
3. Usa el asistente local siguiente: pide la clave sin mostrarla ni escribirla en el historial del terminal. No la guarda en disco. Se conserva en memoria del proceso y del comando hijo mientras se ejecutan.

Windows, sustituyendo `TU_MODELO`:

```powershell
.venv\Scripts\python.exe scripts/run_ai.py ai-ontology --provider openai --model TU_MODELO --max-calls 1 --consent-send-headers
```

macOS/Linux:

```sh
.venv/bin/python scripts/run_ai.py ai-ontology --provider openai --model TU_MODELO --max-calls 1 --consent-send-headers
```

El prompt de clave requiere un terminal interactivo y no muestra caracteres al escribir o pegar. Para Claude sustituye `--provider openai` por `--provider anthropic` y usa su modelo y clave. No pases la clave como argumento del comando. Si ya configuraste `EMAIL_ORGANIZER_AI_KEY` en el entorno, el asistente la reutiliza sin imprimirla. No se carga automáticamente ningún archivo `.env`.

**Qué sucede:** el comando actual envía al proveedor dominios, asuntos truncados y frecuencias, incluidos asuntos protegidos. No envía cuerpos ni adjuntos porque todavía no los importa. Puede haber datos sensibles en un asunto. El límite de una llamada es solo una primera prueba y produce normalmente un borrador parcial, no la ontología completa. No sigas sin revisar costes, datos enviados y cobertura.

Se guarda `data/ontology-draft.json`. Lee [ONTOLOGIA_E_IA.md](ONTOLOGIA_E_IA.md) antes de continuar: explica reanudación, revisión y clasificación con la taxonomía aprobada. No interpretes `complete_headers=true` como contenido completo analizado.

## 6. Qué hacer después de instalar

Si tu objetivo es el sistema semántico completo, el siguiente paso es continuar el desarrollo con [CONTINUAR_AQUI.md](../CONTINUAR_AQUI.md). **No ejecutes etiquetado masivo para compensar que aún falta el motor de contenido.**

Si quieres probar la base actual de reglas y CSV, sigue los pasos 5–9 de [GUIA_PASO_A_PASO.md](GUIA_PASO_A_PASO.md). La secuencia es clasificar → revisar → aprobar unas pocas filas → aplicar con confirmación. Ningún proceso queda trabajando en segundo plano. El ordenador debe estar encendido y sin suspensión mientras se ejecuta un comando.

## 7. Retirar acceso y proteger tu copia

- Google: retira el acceso desde [Conexiones de tu cuenta](https://myaccount.google.com/connections). Elimina también la entrada del llavero `email-organizer`, cuenta `default`, si quieres borrar el token local.
- IA: revoca la clave desde la consola del proveedor si deja de usarse o sospechas exposición.
- Revocar accesos no elimina etiquetas, CSV ni la base local. Guarda o elimina tus datos desde tu PC, con una política de copias que entiendas.
- No pegues diagnósticos completos sin revisarlos. Comparte errores anonimizados, versiones y estado, nunca claves ni contenido real.

## Solución de problemas iniciales

- **Python incorrecto:** comprueba la versión y usa siempre el ejecutable de `.venv`.
- **Archivo no encontrado:** abre la terminal en la raíz que contiene `pyproject.toml`.
- **Llavero no compatible:** revisa la sesión y configuración de tu sistema; no rebajes a texto plano.
- **Google deniega acceso:** revisa API habilitada, cliente de escritorio, usuario de prueba y políticas de organización.
- **IA devuelve error de modelo o facturación:** comprueba el identificador y acceso en su consola. No pegues la clave para diagnosticarlo.
- **ZIP antiguo:** descarga una versión nueva. No mezcles archivos de distintas versiones; conserva `data` como información privada y haz copia antes de migrar.
