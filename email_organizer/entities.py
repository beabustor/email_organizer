"""Entidad por dominio observado; no se inventa una organización verificada."""
import re
from email.utils import parseaddr


def domain(sender):
    address = parseaddr(sender)[1].lower()
    name = address.rsplit('@', 1)[-1] if '@' in address else ''
    return name if re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?', name) and '.' in name else ''
