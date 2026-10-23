# Guía: de tu copia privada a Gmail organizado

Para empezar desde cero, usa primero [INSTALACION_PC.md](INSTALACION_PC.md): incluye Windows, macOS, Linux y la diferencia entre ChatGPT y la API. El código puede ser público o privado; los datos y secretos son siempre locales. Esta página describe el flujo actual de cabeceras, no el motor semántico completo pendiente.

Para históricos grandes, antes de decidir carpetas consulta la [guía de ontología e IA](ONTOLOGIA_E_IA.md). Explica cómo inventariar todos los mensajes importados, proponer una estructura personalizada y distinguir análisis parcial de cobertura completa de cabeceras. Los pasos de esta página siguen siendo el recorrido básico sin IA; el catálogo de ejemplo no sustituye al descubrimiento de tu estructura personal.

## 1. Crea una copia privada en GitHub

No necesitas una copia privada para ejecutar el programa, pero puedes crearla para personalizarlo.

1. En GitHub, inicia sesión y elige **+ → Import repository**.
2. Como repositorio de origen, introduce `https://github.com/beabustor/email_organizer`.
3. Elige un nombre, por ejemplo `mi-organizador-email`.
4. Marca **Private** e inicia la importación.
5. Espera a que aparezcan el README, `config` y `email_organizer`.

No uses «Fork» si necesitas privacidad: un fork de un repositorio público normalmente conserva su visibilidad pública. La importación necesita que el código ya esté publicado en el repositorio de origen.

**Qué sucede:** solo se copia el código. No se conecta Gmail ni se copia ningún correo.

## 2. Descárgalo en tu PC

1. Abre tu nuevo repositorio privado.
2. Pulsa **Code → Download ZIP**.
3. Descomprime el ZIP en una carpeta de tu usuario, fuera de carpetas compartidas.
4. Instala Python 3.11 o posterior desde [python.org](https://www.python.org/downloads/). En Windows activa la opción para añadir Python a PATH, si aparece.
5. Abre una terminal dentro de la carpeta descomprimida, donde está `README.md`.

Esta versión se usa desde la terminal; todavía no incluye una aplicación con ventanas. Los siguientes ejemplos son para Windows PowerShell. En macOS/Linux sustituye `py` por `python3` para crear el entorno y `.venv\Scripts\python.exe` por `.venv/bin/python` en los demás comandos.

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[gmail]"
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**Qué sucede:** se crea un entorno local, se instalan las bibliotecas de Google y se ejecutan pruebas con datos ficticios. No hay acceso a Gmail todavía. No necesitas activar PowerShell ni cambiar su política de ejecución.

## 3. Prepara la conexión con Google

Necesitas acceso a tu cuenta de Google y permiso para autorizar aplicaciones. En cuentas de empresa el administrador puede restringirlo.

1. Abre [Google Cloud Console](https://console.cloud.google.com/) y crea un proyecto para tu uso personal.
2. En **APIs y servicios → Biblioteca**, busca **Gmail API** y habilítala.
3. En **Google Auth Platform** configura el nombre de la aplicación y tu correo de contacto. Los nombres de las pantallas pueden variar.
4. Configura la audiencia para tu cuenta. Si la aplicación está en modo **Testing / Pruebas**, añade tu dirección en **Test users / Usuarios de prueba**.
5. En **Clients / Clientes**, crea un cliente OAuth de tipo **Desktop app / Aplicación de escritorio**.
6. Descarga su archivo JSON. Crea la carpeta `data` dentro del proyecto y guarda el archivo como `data/credentials.json`.

No compartas este archivo ni lo pegues en chats. El repositorio lo excluye de Git, pero debes evitar subirlo manualmente. No necesitas una contraseña de aplicación, una clave de OpenAI ni una suscripción a ChatGPT.

**Qué sucede:** Google identifica tu instalación. Todavía no se han leído correos. No tienes que publicar la aplicación OAuth para probarla como usuario autorizado; una distribución para otros usuarios puede necesitar verificación de Google.

## 4. Importa las cabeceras de Gmail

```powershell
.venv\Scripts\python.exe -m email_organizer.cli gmail-sync
```

1. Se abre el navegador.
2. Comprueba que autorizas la cuenta correcta.
3. Lee los permisos y autoriza si estás de acuerdo.
4. Regresa a la terminal y espera al final de la importación.

**Qué sucede:** se leen remitentes, asuntos, fechas y señales de clasificación. No se descargan cuerpos ni adjuntos a la base. No se mueve ni etiqueta nada. La base local se guarda en `data/organizer.sqlite` y el token en el llavero seguro de tu sistema. Si el llavero no está disponible, el programa se detiene en lugar de guardar tokens sin protección.

Para decenas de miles de mensajes puede tardar: se hace una petición por mensaje nuevo, además de enumerar el buzón. Ctrl+C detiene el proceso; repetir el comando conserva los mensajes importados y omite sus IDs. No ejecutes dos procesos sobre la misma base al mismo tiempo.

## 5. Personaliza las opciones antes de clasificar

Abre `config/criterios.json` con un editor de texto. Puedes dejar los valores iniciales:

- Newsletters: candidatas a revisar después de 180 días.
- Notificaciones y correo masivo: después de 365 días.
- Palabras de documentos sensibles: se protegen.
- `protected_senders`: añade direcciones o dominios que quieras conservar siempre, por ejemplo `["familia@example.com", "miempresa.example"]`.

Mantén el formato JSON: comillas dobles y sin comentarios. Los criterios se basan en cabeceras; no garantizan que un mensaje carezca de valor. No se propone borrar correo personal solo por ser antiguo.

## 6. Genera la propuesta y mira el tiempo estimado

```powershell
.venv\Scripts\python.exe -m email_organizer.cli classify
.venv\Scripts\python.exe -m email_organizer.cli review
```

**Qué sucede:** el programa clasifica en lotes de 200 y muestra progreso, velocidad y tiempo restante de la clasificación local. Exporta `data/review.csv`. Gmail sigue intacto.

## 7. Revisa exactamente lo que quieres aplicar

1. Abre `data/review.csv` con Excel o LibreOffice. Si aparece una sola columna, impórtalo como CSV UTF-8 separado por comas.
2. Filtra `revisar_para_borrar`: `1` indica candidato; `0`, no candidato.
3. Lee remitente, asunto, categoría y motivo.
4. En `aprobar`, escribe `si` solo en las filas que quieres etiquetar. Para una primera prueba, elige cinco mensajes.
5. No cambies `source` ni `id`. Guarda manteniendo el formato CSV, UTF-8 y separador de comas. Cierra el archivo.

```powershell
.venv\Scripts\python.exe -m email_organizer.cli approve data/review.csv
```

**Qué sucede:** se registra la aprobación local, pero todavía no se cambia Gmail. Aprobar un candidato autoriza añadir «Revisar para borrar», **no eliminarlo**. Las propuestas «Conservar» no se aprueban para aplicar etiquetas.

## 8. Aplica las etiquetas aprobadas

```powershell
.venv\Scripts\python.exe -m email_organizer.cli gmail-apply --confirm
```

**Qué sucede:** se crean las etiquetas necesarias bajo `Organizador/` y se añaden a los mensajes aprobados de la cuenta conectada. Un candidato recibe su categoría y también `Organizador/Revisar para borrar`. Los mensajes destacados o importantes se vuelven a comprobar y se omiten, al igual que enviados, borradores, spam y papelera.

Los mensajes siguen en Recibidos: **no se archivan ni se borran**. Se guarda un registro local de las etiquetas añadidas. Repetir el comando omite las propuestas ya aplicadas.

## 9. Comprueba Gmail

1. Recarga Gmail y busca las nuevas etiquetas en el lateral. Se crean solo las necesarias para las propuestas aplicadas.
2. Abre `Organizador/Newsletters` o `Organizador/Notificaciones`.
3. Abre `Organizador/Revisar para borrar` y revisa los mensajes uno a uno o por grupos.
4. Si decides borrar alguno, hazlo tú desde Gmail. Este programa no ejecuta esa acción.
5. Si una etiqueta no te convence, puedes retirarla de los mensajes en Gmail. No hay deshacer automático en esta versión.

## 10. Repite cuando quieras

Repite los pasos 4, 6, 7 y 8 para mensajes nuevos. Si cambias los criterios, usa lo siguiente antes de volver a revisar y aprobar:

```powershell
.venv\Scripts\python.exe -m email_organizer.cli classify --recalculate
.venv\Scripts\python.exe -m email_organizer.cli review
```

Esto recalcula las propuestas no aplicadas y elimina sus aprobaciones anteriores. No retira etiquetas ya aplicadas. Esta versión no es un servicio de fondo ni sincroniza cambios posteriores de mensajes ya importados; consulta las limitaciones del README.

## Si algo falla

- **Python no encontrado:** comprueba su instalación y vuelve a abrir la terminal.
- **No existe credentials.json:** revisa el nombre, la carpeta `data` y que Windows no lo haya llamado `credentials.json.json`.
- **Google deniega acceso:** revisa Gmail API, el cliente de escritorio, los usuarios de prueba y posibles restricciones del administrador. No ignores avisos que no entiendas.
- **Error de llavero:** utiliza el llavero de tu sesión de usuario. En Linux puede requerir instalar/configurar Secret Service o KWallet. No cambies a un almacén de tokens en texto plano.
- **Límites de Gmail o conexión interrumpida:** el cliente reintenta errores temporales; si termina con error, espera y repite el comando. Conserva el mismo directorio `data`.
- **Autorización caducada:** puede ser normal en proyectos OAuth de pruebas; vuelve a autorizar cuando el navegador lo solicite.

Puedes retirar el acceso desde [las conexiones de tu cuenta de Google](https://myaccount.google.com/connections). Para eliminar también el token local, usa el gestor de credenciales del sistema y borra la entrada del servicio `email-organizer`, cuenta `default`. Revocar acceso no elimina las etiquetas ni tu base local.
