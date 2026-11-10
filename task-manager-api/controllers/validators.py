"""Validação de entrada compartilhada por create e update. Mensagens preservadas da API original."""
from middlewares.error_handler import ValidationError
from models.constants import (COLOR_PATTERN, DEFAULT_CATEGORY_COLOR, DEFAULT_PRIORITY, DEFAULT_ROLE,
                              DEFAULT_TASK_STATUS, EMAIL_PATTERN, MAX_PRIORITY, MAX_TITLE_LENGTH, MIN_PASSWORD_LENGTH,
                              MIN_PRIORITY, MIN_TITLE_LENGTH, TASK_STATUSES, USER_ROLES)
from utils.dates import parse_date


def require_object(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def parse_int(value, message):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(message)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


# ---- tasks ----

def _title(value):
    if not isinstance(value, str):
        raise ValidationError('Título inválido')
    if len(value) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(value) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return value


def _status(value):
    if value not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return value


def _priority(value):
    if not _is_int(value):
        raise ValidationError('Prioridade inválida')
    if not MIN_PRIORITY <= value <= MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return value


def _reference(value, message):
    if value is not None and not _is_int(value):
        raise ValidationError(message)
    return value


def _due_date(value, message):
    if not value:
        return None
    parsed = parse_date(value)
    if parsed is None:
        raise ValidationError(message)
    return parsed


def _tags(value):
    return ','.join(value) if isinstance(value, list) else value


def validate_new_task(data):
    require_object(data)
    if not data.get('title'):
        raise ValidationError('Título é obrigatório')
    fields = {
        'title': _title(data['title']),
        'description': data.get('description', ''),
        'status': _status(data.get('status', DEFAULT_TASK_STATUS)),
        'priority': _priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': _reference(data.get('user_id'), 'Usuário inválido'),
        'category_id': _reference(data.get('category_id'), 'Categoria inválida'),
        'due_date': _due_date(data.get('due_date'), 'Formato de data inválido. Use YYYY-MM-DD'),
    }
    if data.get('tags'):
        fields['tags'] = _tags(data['tags'])
    return fields


def validate_task_changes(data):
    require_object(data)
    rules = {
        'title': _title,
        'description': lambda value: value,
        'status': _status,
        'priority': _priority,
        'user_id': lambda value: _reference(value, 'Usuário inválido'),
        'category_id': lambda value: _reference(value, 'Categoria inválida'),
        'due_date': lambda value: _due_date(value, 'Formato de data inválido'),
        'tags': _tags,
    }
    return {field: rule(data[field]) for field, rule in rules.items() if field in data}


# ---- users ----

def _email(value):
    if not isinstance(value, str) or not EMAIL_PATTERN.match(value):
        raise ValidationError('Email inválido')
    return value


def _role(value):
    if value not in USER_ROLES:
        raise ValidationError('Role inválido')
    return value


def validate_new_user(data):
    require_object(data)
    for field, message in (('name', 'Nome é obrigatório'), ('email', 'Email é obrigatório'),
                           ('password', 'Senha é obrigatória')):
        if not data.get(field):
            raise ValidationError(message)
    password = data['password']
    _email(data['email'])
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    return {'name': data['name'], 'email': data['email'], 'password': password,
            'role': data.get('role', DEFAULT_ROLE)}


def validate_user_changes(data):
    require_object(data)
    changes = {}
    if 'name' in data:
        if not isinstance(data['name'], str) or not data['name'].strip():
            raise ValidationError('Nome é obrigatório')
        changes['name'] = data['name']
    if 'email' in data:
        changes['email'] = _email(data['email'])
    if 'password' in data:
        if not isinstance(data['password'], str) or len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        changes['password'] = data['password']
    if 'role' in data:
        changes['role'] = _role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Active deve ser booleano')
        changes['active'] = data['active']
    return changes


def validate_role(value):
    return _role(value)


def validate_credentials(data):
    require_object(data)
    if not data.get('email') or not data.get('password'):
        raise ValidationError('Email e senha são obrigatórios')
    return data['email'], data['password']


# ---- categories ----

def _color(value):
    if value is not None and (not isinstance(value, str) or not COLOR_PATTERN.match(value)):
        raise ValidationError('Cor inválida')
    return value


def _category_name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError('Nome é obrigatório')
    return value


def validate_new_category(data):
    require_object(data)
    if not data.get('name'):
        raise ValidationError('Nome é obrigatório')
    return {
        'name': _category_name(data['name']),
        'description': data.get('description', ''),
        'color': _color(data.get('color', DEFAULT_CATEGORY_COLOR)),
    }


def validate_category_changes(data):
    require_object(data)
    rules = {'name': _category_name, 'description': lambda value: value, 'color': _color}
    return {field: rule(data[field]) for field, rule in rules.items() if field in data}
