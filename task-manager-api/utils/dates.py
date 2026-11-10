from datetime import datetime, timezone

DATE_FORMAT = '%Y-%m-%d'


def utcnow():
    """Agora em UTC, sem tzinfo, compatível com as colunas DateTime já gravadas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_date(value):
    """Converte 'YYYY-MM-DD' em datetime; devolve None se o formato for inválido."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        return None
