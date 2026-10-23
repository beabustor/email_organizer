"""Exportación SKOS de la estructura descubierta; sin datos de mensajes."""
import hashlib
import json
from pathlib import Path


def export(metadata, directory):
    prefix = 'urn:email-organizer:' + metadata['version'] + ':'
    scheme = prefix + 'scheme'
    graph = [{'@id': scheme, '@type': 'skos:ConceptScheme', 'prefLabel': {'es': 'Organización personal del correo'}}]
    parents = {}
    for topic in metadata['topics']:
        parent, leaf = topic['path'].split('/', 1)
        if parent not in parents:
            identifier = prefix + 'parent:' + hashlib.sha256(parent.encode()).hexdigest()[:12]
            parents[parent] = identifier
            graph.append({'@id': identifier, '@type': 'skos:Concept', 'prefLabel': {'es': parent}, 'inScheme': scheme})
        graph.append({'@id': prefix + 'topic:' + str(topic['id']), '@type': 'skos:Concept',
                      'prefLabel': {'es': leaf}, 'broader': parents[parent], 'inScheme': scheme})
    result = {'@context': {'skos': 'http://www.w3.org/2004/02/skos/core#',
                          'prefLabel': {'@id': 'skos:prefLabel', '@container': '@language'},
                          'broader': {'@id': 'skos:broader', '@type': '@id'}, 'inScheme': {'@id': 'skos:inScheme', '@type': '@id'}}, '@graph': graph}
    Path(directory, 'ontology.skos.jsonld').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result
