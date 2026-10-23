"""Descubrimiento local reproducible. Artefactos JSON/NumPy, sin pickle ejecutable."""
import hashlib
import json
import math
import re
import time
from collections import Counter
from pathlib import Path
from functools import lru_cache
import unicodedata
import os

STOPWORDS = '''a al algo algunas algunos ante antes aquí asi así como con contra cual cuando de del desde donde dos el ella ellas ellos en entre era es esa esas ese eso esos esta estaba estado estan estar estas este esto estos fue ha han hasta hay la las le les lo los más mas me mi mis mucho muy ni no nos o otra otras otro otros para pero poco por porque que quien qué se ser si sin sobre son su sus también te tiene todo todos tu tus un una uno unos unas ya y the a an and or is are was were be been to of for on in at by from with as this that these those it its we you your our us not can will would have has do does did more all any so if about into out up down re fw fwd http https www com unsubscribe email correo message mensaje regards gracias hola hello please favor aviso legal confidencial confidential enviado sent mail original escribió wrote'''.split()
STOPWORDS = sorted(set(''.join(c for c in unicodedata.normalize('NFKD', w) if not unicodedata.combining(c)) for w in STOPWORDS))
STOPWORDS = sorted(set(STOPWORDS) | {'documento', 'document', 'ejemplo', 'example', 'informacion', 'information'})


def load_documents(db, source=None):
    where = 'WHERE m.source=?' if source else ''
    rows = db.execute(f'''SELECT m.*,c.text,c.status AS content_status,c.content_hash,c.attachments,length(c.raw) AS size_bytes
        FROM messages m LEFT JOIN content c ON c.source=m.source AND c.id=m.id {where}
        ORDER BY m.source,m.id''', (source,) if source else ()).fetchall()
    return rows


def document(row):
    # No truncar el cuerpo: la vía neural lo fragmenta mediante el tokenizer real.
    return ((row['subject'] or '') + '\n' + (row['text'] or '')).strip()


@lru_cache(maxsize=1)
def neural_encoder(model_name, cache_dir, revision=None):
    # Configurar antes de importar HF: también su caché Xet debe ser local y escribible.
    cache_root = str(Path(cache_dir).resolve())
    os.environ.setdefault('HF_HOME', cache_root)
    os.environ.setdefault('HF_XET_CACHE', str(Path(cache_root) / 'xet'))
    from sentence_transformers import SentenceTransformer
    import torch
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    return SentenceTransformer(model_name, cache_folder=str(cache_dir), trust_remote_code=False, revision=revision, device='cpu',
                                model_kwargs={'use_safetensors': True})


def encode_token_chunks(model, chunks):
    import torch
    tokenizer = model.tokenizer
    # La ruta soportada usa BERT/MiniLM o RoBERTa con delimitadores CLS/SEP.
    # Construir todos los campos con la misma longitud evita diferencias entre tokenizers 4.x/5.x.
    begin = tokenizer.cls_token_id
    end = tokenizer.sep_token_id
    if begin is None or end is None:
        raise ValueError('Este encoder necesita un modelo con tokens CLS/SEP; usa el modelo multilingüe predeterminado.')
    inputs = [[begin, *chunk, end] for chunk in chunks]
    width = max(map(len, inputs))
    features = {'input_ids': torch.tensor([ids + [tokenizer.pad_token_id or 0] * (width-len(ids)) for ids in inputs], device=model.device),
                'attention_mask': torch.tensor([[1]*len(ids) + [0]*(width-len(ids)) for ids in inputs], device=model.device)}
    if 'token_type_ids' in tokenizer.model_input_names:
        features['token_type_ids'] = torch.zeros_like(features['input_ids'])
    model.eval()
    with torch.inference_mode():
        vectors = model(features)['sentence_embedding']
        vectors = torch.nn.functional.normalize(vectors, p=2, dim=1)
    return vectors.cpu().numpy()


def neural_vectors(texts, model_name, cache_dir, revision=None):
    import numpy as np
    model = neural_encoder(model_name, str(cache_dir), revision)
    resolved_revision = getattr(getattr(getattr(model, '_first_module', lambda: None)(), 'auto_model', None), 'config', None)
    identity = model_name + ':' + str(getattr(resolved_revision, '_commit_hash', revision))
    capacity = max(16, min(model.max_seq_length, 512) - 8)
    tokenizer = model.tokenizer
    vectors = []
    for index, text in enumerate(texts):
        key = hashlib.sha256((identity + '\0' + text).encode()).hexdigest()
        path = Path(cache_dir) / 'vectors' / (key + '.npy')
        if path.exists():
            vectors.append(np.load(path, allow_pickle=False))
            continue
        tokens = tokenizer.encode(text, add_special_tokens=False, truncation=False, verbose=False)
        # Todos los tokens, sin muestreo del principio del correo. Sin solapamiento para no sobreponderar citas.
        acc, weight = None, 0
        for start in range(0, max(1, len(tokens)), capacity * 32):
            slices = [tokens[s:s + capacity] for s in range(start, min(len(tokens), start + capacity * 32), capacity)] or [[]]
            # Pasar IDs exactos evita retokenización y truncado oculto en límites WordPiece.
            embeddings = encode_token_chunks(model, slices)
            for chunk, vector in zip(slices, embeddings):
                w = max(1, len(chunk))
                acc = vector * w if acc is None else acc + vector * w
                weight += w
        vector = acc / max(weight, 1)
        vector = vector / max(np.linalg.norm(vector), 1e-12)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, vector, allow_pickle=False)
        vectors.append(vector)
        if (index + 1) % 100 == 0:
            print(f'Embeddings: {index + 1}/{len(texts)} textos completos', flush=True)
    return np.asarray(vectors)


def terms(matrix, indices, vocabulary, limit=3):
    import numpy as np
    scores = np.asarray(matrix[indices].sum(axis=0)).ravel()
    order = scores.argsort()[::-1]
    return [str(vocabulary[i]) for i in order if scores[i] > 0][:limit] or ['sin términos']


def fit(db, directory, source=None, backend='lsa', neural_model='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', max_topics=40, threshold=.25):
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=4):
        return _fit(db, directory, source, backend, neural_model, max_topics, threshold)


def _fit(db, directory, source, backend, neural_model, max_topics, threshold):
    from .content import reextract
    reextract(db, source)
    import numpy as np
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import normalize
    if not 1 <= max_topics <= 60 or not 0 <= threshold <= 1:
        raise ValueError('Temas entre 1 y 60; similitud entre 0 y 1')
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    rows = load_documents(db, source)
    eligible = [r for r in rows if r['text'] and r['content_status'] in ('complete', 'partial')]
    texts = [document(row) for row in eligible]
    started = time.monotonic()
    # Duplicados exactos del contenido cuentan una vez al descubrir la estructura.
    unique = list(dict.fromkeys(texts))
    metadata = {'backend': backend, 'neural_model': neural_model, 'threshold': threshold, 'topics': [],
                'total_messages': len(rows), 'analyzed_messages': len(eligible), 'unique_texts': len(unique),
                'source': source, 'state': 'draft', 'metrics': 'Similitud geométrica, no probabilidad de acierto',
                'attachments_analyzed': 'supported_formats_with_explicit_coverage'}
    if not rows:
        raise ValueError('No hay mensajes importados. Usa gmail-download o import-full antes de analizar.')
    if not unique:
        # Un buzón solo de imágenes/cifrado debe recibir revisión, no quedar sin resultado.
        unique = ['contenido sin texto interpretable']
        metadata['backend'] = backend = 'lsa'
    vectorizer = TfidfVectorizer(lowercase=True, strip_accents='unicode', stop_words=STOPWORDS,
                                 max_features=30000, sublinear_tf=True, token_pattern=r'(?u)\b[^\W\d_][\w-]{2,}\b')
    try:
        lexical = vectorizer.fit_transform(unique)
    except ValueError:
        # No atribuir significado a texto compuesto solo por símbolos o stopwords.
        unique = ['contenido sin palabras interpretables']
        lexical = vectorizer.fit_transform(unique)
        metadata['backend'] = backend = 'lsa'
    vocabulary = vectorizer.get_feature_names_out()
    components = None
    if backend == 'neural':
        vectors = neural_vectors(unique, neural_model, folder / 'neural-cache')
        encoder = neural_encoder(neural_model, str(folder / 'neural-cache'))
        metadata['neural_revision'] = getattr(encoder._first_module().auto_model.config, '_commit_hash', None)
    elif backend == 'lsa':
        dims = min(128, lexical.shape[0] - 1, lexical.shape[1] - 1)
        if dims >= 2:
            reducer = TruncatedSVD(n_components=dims, random_state=42)
            vectors = normalize(reducer.fit_transform(lexical)).astype('float32')
            components = reducer.components_
        else:
            vectors = normalize(lexical).toarray().astype('float32')
    else:
        raise ValueError('Backend no admitido')
    unique_vectors = len(np.unique(np.round(vectors, 5), axis=0))
    k = min(max_topics, max(1, round(math.sqrt(len(unique) / 2))), unique_vectors)
    clusterer = MiniBatchKMeans(n_clusters=max(1, k), random_state=42, n_init=3, batch_size=1024)
    assignments = clusterer.fit_predict(vectors)
    centers = normalize(clusterer.cluster_centers_)
    parent_count = min(k, 8, max(2, round(math.sqrt(k))))
    if parent_count > 1:
        parent_ids = MiniBatchKMeans(n_clusters=parent_count, random_state=42, n_init=3).fit_predict(centers)
    else:
        parent_ids = np.zeros(k, dtype=int)
    parent_names = {}
    for parent in range(parent_count):
        indices = [i for i, c in enumerate(assignments) if parent_ids[c] == parent]
        parent_names[parent] = f'Tema{parent + 1:02d}-' + '-'.join(terms(lexical, indices, vocabulary, 2))
    for cluster in range(k):
        indices = np.flatnonzero(assignments == cluster)
        keywords = terms(lexical, indices, vocabulary)
        leaf = f'Grupo{cluster + 1:03d}-' + '-'.join(keywords)
        path = parent_names[int(parent_ids[cluster])] + '/' + leaf
        examples = sorted(indices, key=lambda i: -float(vectors[i] @ centers[cluster]))[:5]
        metadata['topics'].append({'id': cluster, 'path': path[:180], 'keywords': keywords,
            'unique_documents': len(indices), 'examples': [hashlib.sha256(unique[i].encode()).hexdigest() for i in examples]})
    metadata['vocabulary'] = {word: int(index) for word, index in vectorizer.vocabulary_.items()}
    metadata['has_svd'] = components is not None
    metadata['seconds'] = round(time.monotonic() - started, 2)
    version = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode() + centers.tobytes()).hexdigest()[:20]
    metadata['version'] = version
    # Directorio de versión inmutable: nunca dejar un modelo activo a medio escribir.
    version_dir = folder / version
    version_dir.mkdir(exist_ok=True)
    np.savez_compressed(version_dir / 'arrays.npz', centers=centers, idf=vectorizer.idf_,
                        components=components if components is not None else np.empty((0, 0)))
    (version_dir / 'model.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    from .ontology import export
    export(metadata, version_dir)
    (folder / 'active.json').write_text(json.dumps({'version': version}), encoding='utf-8')
    classify(db, folder, source=source)
    print(f'Ontología descubierta: {k} grupos, {parent_count} temas; {len(eligible)}/{len(rows)} mensajes con cuerpo analizado. Revisión obligatoria.', flush=True)
    return metadata


def read_model(directory):
    import numpy as np
    folder = Path(directory)
    version = json.loads((folder / 'active.json').read_text())['version']
    if not re.fullmatch(r'[a-f0-9]{20}', version):
        raise ValueError('Identificador de modelo inválido')
    folder = folder / version
    metadata = json.loads((folder / 'model.json').read_text(encoding='utf-8'))
    with np.load(folder / 'arrays.npz', allow_pickle=False) as arrays:
        data = {key: arrays[key] for key in arrays.files}
    return metadata, data


def classify(db, directory, source=None):
    from .content import reextract
    reextract(db, source)
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import normalize
    from .entities import domain
    from .cleanup import load, candidate
    cleanup_rules = load()
    metadata, arrays = read_model(directory)
    if metadata['source'] is not None and source is not None and metadata['source'] != source:
        raise ValueError('El modelo pertenece a otra cuenta')
    if source is None and metadata['source'] is not None:
        source = metadata['source']
    rows = load_documents(db, source)
    vocabulary = metadata['vocabulary']
    vectorizer = TfidfVectorizer(vocabulary=vocabulary, lowercase=True, strip_accents='unicode', stop_words=STOPWORDS,
                                 sublinear_tf=True, token_pattern=r'(?u)\b[^\W\d_][\w-]{2,}\b')
    vectorizer.idf_ = arrays['idf']
    available = [r for r in rows if r['text'] and r['content_status'] in ('complete', 'partial')]
    domain_counts = Counter(domain(r['sender']) for r in rows)
    top_domains = {name for name, count in domain_counts.most_common(50) if name and count >= 20}
    vectors_by_id = {}
    started = time.monotonic()
    # Memoria acotada: nunca construir una matriz densa 30000 x vocabulario.
    for start in range(0, len(available), 128):
        batch = available[start:start + 128]
        texts = [document(r) for r in batch]
        if metadata['backend'] == 'neural':
            vectors = neural_vectors(texts, metadata['neural_model'], Path(directory) / 'neural-cache', metadata.get('neural_revision'))
        else:
            lexical = vectorizer.transform(texts)
            vectors = normalize(lexical @ arrays['components'].T) if metadata['has_svd'] else normalize(lexical).toarray()
        sims = vectors @ arrays['centers'].T
        for row, similarities in zip(batch, sims):
            order = np.argsort(similarities)[::-1]
            score = max(0., min(1., float(similarities[order[0]])))
            labels = []
            status = 'review' if score < metadata['threshold'] or row['content_status'] != 'complete' or len(re.findall(r'\w+', document(row))) < 5 else 'proposed'
            if status == 'proposed':
                for cluster in order[:2]:
                    if float(similarities[cluster]) >= max(metadata['threshold'], score * .9):
                        labels.append('Organizador/Temas/' + metadata['topics'][int(cluster)]['path'])
            vectors_by_id[(row['source'], row['id'])] = (labels, score, status)
        completed = min(start + 128, len(available))
        remaining = (len(available) - completed) * (time.monotonic() - started) / max(1, completed)
        print(f'Clasificados {completed}/{len(available)} cuerpos; tiempo restante aproximado {remaining:.0f}s', flush=True)
    with db:
        for row in rows:
            labels, score, status = vectors_by_id.get((row['source'], row['id']), ([], 0., 'review'))
            if status == 'review':
                labels = ['Organizador/Revision necesaria']
            entity = domain(row['sender'])
            if entity in top_domains:
                labels.append('Organizador/Entidades/' + entity)
            removable, cleanup_reason = candidate(row, cleanup_rules)
            if removable and status == 'proposed':
                labels += [label + '/Candidatos a borrar' for label in labels if label.startswith('Organizador/Temas/')]
            digest = row['content_hash'] or ''
            old = db.execute('SELECT * FROM semantic_results WHERE source=? AND id=?', (row['source'], row['id'])).fetchone()
            serialized = json.dumps(labels, ensure_ascii=False)
            if not old or old['labels'] != serialized or old['content_hash'] != digest or old['model_version'] != metadata['version']:
                db.execute("UPDATE operations SET approved=0 WHERE source=? AND id=? AND state='pending'", (row['source'], row['id']))
            db.execute('''INSERT OR REPLACE INTO semantic_results
              (source,id,model_version,content_hash,labels,score,status,cleanup_reason,size_bytes)
              VALUES (?,?,?,?,?,?,?,?,?)''', (row['source'], row['id'], metadata['version'], digest, serialized, score, status, cleanup_reason, row['size_bytes'] or 0))
    return len(rows)
