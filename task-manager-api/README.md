# task-manager-api

API de Task Manager em Python/Flask (SQLite via Flask-SQLAlchemy), organizada em MVC.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # ajuste SECRET_KEY e demais variáveis
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (configurável por `HOST`/`PORT`; no macOS a porta 5000 costuma estar ocupada pelo AirPlay Receiver, então use outra, ex.: `PORT=5055 python app.py`). O `seed.py` popula o banco SQLite (`instance/tasks.db`, configurável por `DATABASE_URL`) com usuários, categorias e tasks de exemplo. **Rode-o antes do primeiro boot.**

Sem `SECRET_KEY` no ambiente, uma chave efêmera é gerada a cada boot e os tokens emitidos deixam de valer após um restart.

## Estrutura

```
app.py                  # create_app(): composition root + entry point
config/settings.py      # configuração lida de variáveis de ambiente (.env.example)
database.py             # instância do SQLAlchemy + PersistenceMixin (save/delete transacionais)
models/                 # entidades, regras da entidade (ex.: Task.is_overdue), consultas e constantes de domínio
controllers/            # casos de uso e validação de entrada (validators.py)
routes/                 # blueprints finos: mapeiam rota -> controller e declaram a proteção de cada rota
services/               # NotificationService (e-mail desligado por padrão) e TokenService (tokens assinados)
middlewares/            # error_handler (erros de domínio -> JSON) e auth (require_auth)
utils/dates.py          # utcnow() e parse_date()
seed.py                 # dados de exemplo
```

## Autenticação

`POST /login` devolve um `token` assinado (expira em `TOKEN_MAX_AGE` segundos). Envie-o como `Authorization: Bearer <token>`.

| Rota | Credencial |
|---|---|
| `GET /users`, `DELETE /users/<id>` | papel `admin` |
| `GET /users/<id>`, `PUT /users/<id>`, `GET /reports/user/<id>` | papel `admin` ou o próprio usuário (só `admin` altera `role`/`active`) |
| `POST /users` com `role` diferente de `user` | papel `admin` (cadastro com `role: user` é público) |
| `GET /reports/summary` | papel `admin` |
| `POST /categories`, `PUT /categories/<id>`, `DELETE /categories/<id>` | papel `admin` |

As demais rotas (`/`, `/health`, `/tasks*`, `GET /users/<id>/tasks`, `GET /categories`, `POST /login`) são públicas.
