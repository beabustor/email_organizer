"""Exporta solo métricas agregadas y versiones; no nombres de etiquetas o mensajes."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess


def main():
    parser = argparse.ArgumentParser(description='Informe agregado para revisión antes de compartir al proyecto público.')
    parser.add_argument('--evaluation', default='data/evaluation.json')
    parser.add_argument('--output', default='data/public-validation.json')
    args = parser.parse_args()
    raw = json.loads(Path(args.evaluation).read_text(encoding='utf-8'))
    fields = ('reviewed', 'exact_match', 'exact_match_interval_95', 'macro_f1', 'independent_test')
    result = {'metrics': {name: raw[name] for name in fields}, 'versions': {}, 'system': platform.system(),
              'python': platform.python_version(), 'scope': 'Acuerdo revisado; no asumir validación independiente.',
              'manual_review_required_before_sharing': True}
    for name in ('email-organizer-local', 'sentence-transformers', 'torch', 'scikit-learn', 'numpy'):
        try:
            result['versions'][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
    result['commit'] = commit.stdout.strip() if commit.returncode == 0 else None
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Informe agregado guardado en {args.output}. Revísalo; no se ha publicado nada.')


if __name__ == '__main__':
    main()
