"""Comandos del flujo completo; las rutas antiguas quedan para compatibilidad."""
import json
from pathlib import Path

COMMANDS = {'extract-attachments', 'import-full', 'gmail-download', 'analyze', 'predict', 'plan', 'approve-plan', 'apply-plan', 'undo-plan', 'evaluate', 'name-topics', 'authorize-automation', 'refresh'}


def register(sub):
    p = sub.add_parser('extract-attachments', help='Reextrae originales locales sin descargarlos otra vez; invalida planes afectados')
    p.add_argument('--source')
    p.add_argument('--retry', action='store_true', help='Reintenta también adjuntos tras instalar OCR/lectores')
    p = sub.add_parser('name-topics', help='IA opcional: nombres humanos a grupos descubiertos localmente')
    p.add_argument('--model-dir', default='data/semantic')
    p.add_argument('--provider', choices=['openai', 'anthropic'], required=True)
    p.add_argument('--api-model', required=True)
    p.add_argument('--max-calls', type=int, default=4)
    p.add_argument('--consent-send-examples', action='store_true')
    p = sub.add_parser('authorize-automation', help='Autoriza etiquetas futuras de una estructura revisada, sin limpieza automática')
    p.add_argument('plan_id')
    p.add_argument('--output', default='data/automation.json')
    p.add_argument('--max-changes', type=int, default=100)
    p.add_argument('--confirm', action='store_true')
    p = sub.add_parser('refresh', help='Descarga novedades y clasifica con el modelo guardado; aplicar es opcional')
    p.add_argument('--credentials', default='data/credentials.json')
    p.add_argument('--model-dir', default='data/semantic')
    p.add_argument('--policy', help='Política explícitamente autorizada; omitir solo genera propuestas')
    p = sub.add_parser('import-full', help='Importa originales MIME y cuerpos de un MBOX')
    p.add_argument('file')
    p = sub.add_parser('gmail-download', help='Descarga Gmail completo y reanuda con historial incremental')
    p.add_argument('--credentials', default='data/credentials.json')
    p.add_argument('--exclude-spam-trash', action='store_true')
    for name in ('analyze', 'predict'):
        p = sub.add_parser(name, help='Descubre estructura con cuerpos completos' if name == 'analyze' else 'Clasifica con la estructura ya guardada')
        p.add_argument('--model-dir', default='data/semantic')
        p.add_argument('--source')
        if name == 'analyze':
            p.add_argument('--backend', choices=['lsa', 'neural'], default='lsa')
            p.add_argument('--neural-model', default='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            p.add_argument('--max-topics', type=int, default=40)
            p.add_argument('--threshold', type=float, default=.25)
    p = sub.add_parser('plan', help='Genera informe HTML y CSV con acciones exactas')
    p.add_argument('--source')
    p.add_argument('--output', default='data/plans')
    p = sub.add_parser('approve-plan', help='Aprueba un plan exacto, invalidando CSV obsoletos')
    p.add_argument('plan_id')
    p.add_argument('--csv')
    p.add_argument('--all', action='store_true')
    p.add_argument('--confirm', action='store_true')
    for name in ('apply-plan', 'undo-plan'):
        p = sub.add_parser(name)
        p.add_argument('plan_id')
        p.add_argument('--credentials', default='data/credentials.json')
        p.add_argument('--max-changes', type=int, default=100)
        p.add_argument('--confirm', action='store_true')
    p = sub.add_parser('evaluate', help='Evalúa etiquetas humanas del CSV, sin inventar precisión')
    p.add_argument('file')
    p.add_argument('--output', default='data/evaluation.json')


def execute(args, db):
    if args.command == 'extract-attachments':
        from .content import reextract
        print('Mensajes reextraídos:', reextract(db, args.source, args.retry))
    elif args.command == 'name-topics':
        if not args.consent_send_examples:
            raise ValueError('Requiere --consent-send-examples: envía palabras clave y hasta dos ejemplos de 1500 caracteres por grupo al proveedor elegido.')
        from .naming import name_topics
        print('Versión con nombres:', name_topics(db, args.model_dir, args.provider, args.api_model, args.max_calls))
    elif args.command == 'authorize-automation':
        from .automation import authorize
        if not args.confirm:
            raise ValueError('Requiere --confirm: habilita cambios futuros en categorías aprobadas. No acredita calidad independiente.')
        authorize(db, args.plan_id, args.output, args.max_changes)
        print('Política local guardada. No aplica limpieza ni categorías nuevas automáticamente.')
    elif args.command == 'refresh':
        from .gmail import service
        from .automation import refresh
        print('Resultado:', refresh(db, service(args.credentials, writable=False), args.model_dir, args.policy,
                                  service(args.credentials, writable=True) if args.policy else None))
    elif args.command == 'import-full':
        from .content import import_mbox
        print('Origen:', import_mbox(db, args.file))
    elif args.command == 'gmail-download':
        from .gmail import service
        from .content import sync_full
        sync_full(db, service(args.credentials, writable=False), include_spam_trash=not args.exclude_spam_trash)
    elif args.command == 'analyze':
        from .semantic import fit
        fit(db, args.model_dir, args.source, args.backend, args.neural_model, args.max_topics, args.threshold)
    elif args.command == 'predict':
        from .semantic import classify
        print('Mensajes con resultado:', classify(db, args.model_dir, args.source))
    elif args.command == 'plan':
        from .plans import create
        print('Plan:', create(db, args.output, args.source))
    elif args.command == 'approve-plan':
        from .plans import approve
        if not args.confirm or (args.all == bool(args.csv)):
            raise ValueError('Usa --confirm y elige --all o --csv ARCHIVO, solo una opción.')
        print('Propuestas aprobadas:', approve(db, args.plan_id, args.csv, args.all))
    elif args.command in ('apply-plan', 'undo-plan'):
        from .gmail import service
        from .plans import apply
        if not args.confirm:
            raise ValueError('Requiere --confirm; revisa el informe y la cuenta antes de continuar.')
        apply(db, service(args.credentials, writable=True), args.plan_id, args.max_changes, args.command == 'undo-plan')
    elif args.command == 'evaluate':
        from .evaluation import evaluate
        result = evaluate(db, args.file)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))
