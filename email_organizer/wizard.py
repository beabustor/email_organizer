import json
import os
from pathlib import Path
import subprocess
import sys
import webbrowser
import getpass
import warnings

from .core import connect


def neural_install():
    import importlib.util
    import importlib.metadata
    if importlib.util.find_spec('sentence_transformers'):
        try:
            if int(importlib.metadata.version('transformers').split('.')[0]) == 4:
                return
        except importlib.metadata.PackageNotFoundError:
            pass
    print('El motor neural necesita PyTorch CPU, Sentence Transformers y un modelo multilingüe.')
    print('La descarga puede ocupar varios GB. No se enviará tu correo al proveedor del modelo.')
    if input('¿Instalar las bibliotecas ahora? Escribe INSTALAR: ').strip() != 'INSTALAR':
        raise ValueError('Instalación neural cancelada. Puedes escoger el motor ligero.')
    if sys.platform != 'darwin':
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'torch>=2.6,<3', '--index-url', 'https://download.pytorch.org/whl/cpu'], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.[neural]'], check=True)


def main():
    from .locking import database_lock
    with database_lock('data/organizer.sqlite'):
        _main()


def _main():
    from .content import import_mbox, sync_full
    from .semantic import fit, classify
    from .plans import create, approve, apply
    from .gmail import service
    print('\nEMAIL ORGANIZER — análisis local del contenido y limpieza revisable')
    print('No borra ni archiva correos. Los candidatos no son decisiones de borrado.')
    print('1. Descargar Gmail y analizar todo\n2. Importar MBOX y analizar todo\n3. Analizar la base ya descargada\n4. Actualizar Gmail con la estructura existente\n5. Deshacer etiquetas de un plan\n0. Salir')
    choice = input('Elige: ').strip()
    if choice == '0':
        return
    if choice not in ('1', '2', '3', '4', '5'):
        raise ValueError('Opción no válida')
    data = Path('data')
    data.mkdir(exist_ok=True)
    if os.name != 'nt':
        data.chmod(0o700)
    credentials = 'data/credentials.json'
    db = connect(data / 'organizer.sqlite')
    try:
        source = None
        if choice in ('1', '4', '5'):
            if not Path(credentials).exists():
                print('Crea tu cliente OAuth de escritorio siguiendo docs/INSTALACION_PC.md.')
                credentials = input('Ruta local del JSON de Google (no su contenido): ').strip().strip('"')
                if not Path(credentials).is_file():
                    raise ValueError('No se encuentra el JSON de Google')
        if choice == '5':
            identifier = input('ID del plan que quieres deshacer: ').strip()
            if input('Solo quitará etiquetas añadidas por ese plan. Escribe DESHACER: ').strip() == 'DESHACER':
                apply(db, service(credentials, writable=True), identifier, max_changes=100, undo=True)
            return
        if choice in ('1', '4'):
            print('La descarga incluye todos los mensajes accesibles, también spam/papelera. Puede tardar; puedes reanudar.')
            source = sync_full(db, service(credentials, writable=False))
        elif choice == '2':
            source = import_mbox(db, input('Ruta del archivo MBOX: ').strip().strip('"'))
        else:
            sources = [r[0] for r in db.execute('SELECT DISTINCT source FROM messages')]
            if len(sources) != 1:
                raise ValueError('No hay una sola cuenta importada. Usa los comandos con --source.')
            source = sources[0]
        if choice == '4':
            classify(db, data / 'semantic', source)
        else:
            print('1. Neural multilingüe: embeddings locales; requiere descargar modelo.\n2. Ligero: TF-IDF + LSA; no requiere modelo externo.')
            backend_choice = input('Motor [1]: ').strip() or '1'
            if backend_choice not in ('1', '2'):
                raise ValueError('Motor no válido')
            backend = 'neural' if backend_choice == '1' else 'lsa'
            if backend == 'neural':
                neural_install()
                print('El modelo se descargará por HTTPS. Si falta red o memoria se detendrá, sin cambiar Gmail.')
            fit(db, data / 'semantic', source, backend=backend)
            print('Opcional: OpenAI/Claude puede poner nombres humanos a los grupos enviando ejemplos de texto. Tiene coste API separado de ChatGPT.')
            if input('¿Quieres hacerlo ahora? Escribe SI o Enter para mantener los nombres por términos: ').strip().upper() == 'SI':
                from .naming import name_topics
                provider = input('Proveedor (openai / anthropic): ').strip().lower()
                if provider not in ('openai', 'anthropic'):
                    raise ValueError('Proveedor no válido')
                api_model = input('Identificador del modelo disponible en tu cuenta API: ').strip()
                consent = input('Se enviarán hasta dos ejemplos de 1500 caracteres por grupo. Para autorizar escribe ENVIAR: ').strip()
                if consent == 'ENVIAR':
                    previous_key = os.environ.get('EMAIL_ORGANIZER_AI_KEY')
                    try:
                        if not previous_key:
                            with warnings.catch_warnings():
                                warnings.simplefilter('error', getpass.GetPassWarning)
                                os.environ['EMAIL_ORGANIZER_AI_KEY'] = getpass.getpass('Clave API (oculta, no se guarda): ').strip()
                        name_topics(db, data / 'semantic', provider, api_model)
                    except Exception as error:
                        print(f'No se completó el renombrado ({type(error).__name__}). Se conserva la estructura anterior; puedes continuar revisándola.')
                    finally:
                        if previous_key is None:
                            os.environ.pop('EMAIL_ORGANIZER_AI_KEY', None)
                        else:
                            os.environ['EMAIL_ORGANIZER_AI_KEY'] = previous_key
        identifier = create(db, data / 'plans', source)
        path = data / 'plans' / (identifier + '.html')
        print(f'Plan: {identifier}\nInforme: {path}\nCSV: {path.with_suffix(".csv")}')
        print('Abre el informe y revisa ejemplos, temas, entidades y motivos de limpieza.')
        webbrowser.open(path.resolve().as_uri())
        if not source.startswith('gmail:'):
            print('MBOX: análisis terminado. No se conecta Gmail ni se modifica el archivo.')
            return
        print('Para una primera prueba, aprueba unas pocas filas del CSV. No edites IDs ni hashes.')
        action = input('Escribe CSV para aprobar sus filas marcadas, TODO para aprobar el plan completo, o Enter para salir sin cambios: ').strip()
        if action == 'CSV':
            count = approve(db, identifier, path.with_suffix('.csv'))
        elif action == 'TODO':
            if input('¿Has revisado la estructura? Escribe APROBAR para aprobar todas las propuestas: ').strip() != 'APROBAR':
                return
            count = approve(db, identifier, all_rows=True)
        else:
            return
        print(f'{count} propuestas aprobadas. Se omitirán mensajes protegidos al aplicar.')
        if input('Para añadir etiquetas a un máximo de 100 mensajes, escribe APLICAR: ').strip() == 'APLICAR':
            apply(db, service(credentials, writable=True), identifier, max_changes=100)
            print('Si quedan propuestas, repite apply-plan con este ID. No se han borrado correos.')
    finally:
        db.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nDetenido; se conservan los pasos guardados.')
    except Exception as error:
        # Mensajes propios ValueError son seguros; errores de API no se vuelcan con datos del correo.
        print(str(error) if isinstance(error, ValueError) else f'Operación detenida ({type(error).__name__}). Consulta la guía y repite para reanudar.', file=sys.stderr)
        raise SystemExit(1)
