# Execução da skill `/refactor-arch` — task-manager-api

Saída do Claude Code em modo headless (`claude -p "/refactor-arch"`, seguido de `claude -p "y" --resume <sessão>`).

## Fases 1 e 2 (análise e auditoria, pausa para confirmação)

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (versão não declarada; ambiente local 3.9.6)
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1 (declarada, não usada), requests 2.31.0 (declarada, não usada), python-dotenv 1.0.0 (declarada, não usada), smtplib (stdlib)
Database:      SQLite (`sqlite:///tasks.db`) via SQLAlchemy ORM (Flask-SQLAlchemy)
Domain:        Task Manager API (tarefas, usuários, categorias, relatórios)
Architecture:  Camadas parciais — existem `models/`, `routes/`, `services/`, `utils/`, mas os handlers em `routes/*.py` fazem validação, regras, queries e serialização; `services/` e `utils/` não são usados; não há config nem tratamento de erros centralizados
Entry point:   app.py (`python seed.py && python app.py`, porta 5000)
Source files:  15 files analyzed (~1158 lines)
DB tables:     users, tasks, categories
Endpoints:     22 routes
================================

| # | Método + path | Handler |
|---|---|---|
| 1 | GET /health | app.py:22 |
| 2 | GET / | app.py:26 |
| 3 | GET /tasks | routes/task_routes.py:11 |
| 4 | GET /tasks/<id> | routes/task_routes.py:65 |
| 5 | POST /tasks | routes/task_routes.py:85 |
| 6 | PUT /tasks/<id> | routes/task_routes.py:156 |
| 7 | DELETE /tasks/<id> ⚠️ | routes/task_routes.py:225 |
| 8 | GET /tasks/search | routes/task_routes.py:240 |
| 9 | GET /tasks/stats | routes/task_routes.py:273 |
| 10 | GET /users | routes/user_routes.py:10 |
| 11 | GET /users/<id> | routes/user_routes.py:27 |
| 12 | POST /users | routes/user_routes.py:42 |
| 13 | PUT /users/<id> | routes/user_routes.py:92 |
| 14 | DELETE /users/<id> ⚠️ (apaga as tasks do usuário em cascata) | routes/user_routes.py:134 |
| 15 | GET /users/<id>/tasks | routes/user_routes.py:153 |
| 16 | POST /login | routes/user_routes.py:185 |
| 17 | GET /reports/summary | routes/report_routes.py:12 |
| 18 | GET /reports/user/<id> | routes/report_routes.py:103 |
| 19 | GET /categories | routes/report_routes.py:157 |
| 20 | POST /categories | routes/report_routes.py:167 |
| 21 | PUT /categories/<id> | routes/report_routes.py:190 |
| 22 | DELETE /categories/<id> ⚠️ | routes/report_routes.py:211 |

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (SQLite via Flask-SQLAlchemy)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-11-10

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 6 | LOW: 5

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP05 | Hash de senha exposto nas respostas da API | models/user.py:21 |
| 2 | CRITICAL | AP01 | `SECRET_KEY` hardcoded | app.py:13 |
| 3 | CRITICAL | AP01 | Credenciais SMTP hardcoded | services/notification_service.py:7-10 |
| 4 | CRITICAL | AP06 | Senhas com MD5 sem salt | models/user.py:3, 29, 32 |
| 5 | HIGH | AP11 | Token falso, role livre e rotas privilegiadas sem proteção | routes/user_routes.py:52, 71-72, 210 |
| 6 | HIGH | AP12 | Debug ligado, bind 0.0.0.0, CORS aberto, DB fixo | app.py:11, 15, 34 |
| 7 | HIGH | AP07 | Regras de negócio nos handlers (Fat Controller) | routes/task_routes.py, routes/user_routes.py, routes/report_routes.py |
| 8 | HIGH | AP08 | Sem app factory; dependências criadas no import | app.py:9-31, seed.py:2, services/notification_service.py:5-15 |
| 9 | MEDIUM | AP13 | Queries N+1 e COUNTs repetidos | task_routes.py:41-57, 275-279; user_routes.py:22, 140-142; report_routes.py:19-28, 55-56, 159-163 |
| 10 | MEDIUM | AP15 | Validação de entrada ausente/inconsistente | task_routes.py:93-100, 113, 166-184, 260-264; user_routes.py:102-103, 124-125; report_routes.py:196-202 |
| 11 | MEDIUM | AP16 | `except:` genérico e sem handler central | task_routes.py:62, 137, 151, 204, 221, 236; user_routes.py:87, 130, 149; report_routes.py:186, 207, 221 |
| 12 | MEDIUM | AP14 | Regra de "overdue", serialização e validações duplicadas | task_routes.py:17-39, 71-80, 110, 177, 283-287; user_routes.py:61, 71, 106, 120, 171-180; report_routes.py:34-36, 132-135 |
| 13 | MEDIUM | AP19 | Delete de categoria deixa tasks órfãs | report_routes.py:211-223; models/task.py:13-14, 20-21 |
| 14 | MEDIUM | AP17 | APIs deprecated (`Query.get`, `datetime.utcnow`) | 16× `query.get`, 20× `utcnow` (ver seção Deprecated APIs) |
| 15 | LOW | AP22 | Imports não usados e código morto | app.py:7; task_routes.py:7; user_routes.py:6; report_routes.py:7-8; models/task.py:3; utils/helpers.py:2-116 |
| 16 | LOW | AP20 | Magic numbers e strings | task_routes.py:96, 99, 104, 113, 182; user_routes.py:64, 115; report_routes.py:24-28, 129, 180 |
| 17 | LOW | AP23 | `print` no lugar de logging | task_routes.py:149, 153, 219, 234; user_routes.py:83, 89, 147; notification_service.py:21, 24; helpers.py:39-41 |
| 18 | LOW | AP24 | Condicionais verbosas e aninhadas | models/task.py:38-60; models/user.py:34-38; task_routes.py:30-39, 141, 210; helpers.py:103 |
| 19 | LOW | AP21 | Nomenclatura ruim | report_routes.py:24-28; models/category.py:14; task_routes.py:16, 51 |

## Findings

### #1 [CRITICAL] Hash de senha exposto nas respostas da API (AP05)
File: models/user.py:21
Description: `User.to_dict()` inclui `'password': self.password`. Ele é usado em `GET /users/<id>` (routes/user_routes.py:33), `POST /users` (:85), `PUT /users/<id>` (:129) e no `POST /login` (:209). Quatro endpoints devolvem o hash MD5 da senha.
Evidence:
```python
'password': self.password,
```
Impact: qualquer cliente lê o hash de qualquer usuário. Somado ao MD5 sem salt (#4), recuperar as senhas em texto é trivial (as do seed são `1234`, `abcd`, `pass`).
Recommendation: tirar `password` da serialização pública (Playbook P9).

### #2 [CRITICAL] `SECRET_KEY` hardcoded (AP01)
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` fica literal no código versionado.
Evidence:
```python
app.config['SECRET_KEY'] = 'super-secret-key-123'
```
Impact: quem tem acesso ao repositório consegue forjar qualquer coisa assinada com essa chave (sessões e, depois da correção de #5, tokens). Rotacionar exige deploy.
Recommendation: ler de variável de ambiente num módulo `config`, com `.env.example` (Playbook P1).

### #3 [CRITICAL] Credenciais SMTP hardcoded (AP01)
File: services/notification_service.py:7-10
Description: o construtor de `NotificationService` guarda host, porta, usuário `taskmanager@gmail.com` e senha `'senha123'` como literais.
Evidence:
```python
self.email_user = 'taskmanager@gmail.com'
self.email_password = 'senha123'
```
Impact: a conta de e-mail fica comprometida para qualquer pessoa com acesso ao código e pode ser usada para spam/phishing em nome do produto.
Recommendation: mover para config via env e injetar no service (Playbook P1, P5).

### #4 [CRITICAL] Senhas armazenadas com MD5 sem salt (AP06)
File: models/user.py:3, 29, 32
Description: `set_password`/`check_password` usam `hashlib.md5(pwd.encode()).hexdigest()`, sem salt e sem fator de custo. A severidade base (HIGH) subiu um nível porque o fluxo é de autenticação e o hash ainda é exposto pela API (#1).
Evidence:
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
Impact: hashes iguais para senhas iguais e quebra instantânea via rainbow tables.
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash` (já vem com o Flask), migrando hashes MD5 legados no login (Playbook P9).

### #5 [HIGH] Autenticação falsa, role livre e rotas privilegiadas sem proteção (AP11)
File: routes/user_routes.py:52, 71-72, 210
Description: o login devolve `'fake-jwt-token-' + str(user.id)`, um token previsível que nenhuma rota valida. `POST /users` aceita `role` livre (`admin` incluso), então qualquer anônimo se cadastra como admin. Nenhuma rota exige credencial. Rotas privilegiadas sem proteção:
- `GET /users` (lista dados pessoais de todos)
- `GET /users/<id>` (dados pessoais de terceiros)
- `PUT /users/<id>` (altera terceiros, inclusive `role`/`active`)
- `DELETE /users/<id>` (apaga usuário e as tasks dele)
- `POST /users` (só quando `role` ≠ `user`: escalada de privilégio)
- `GET /reports/summary` (relatório gerencial com produtividade por usuário)
- `GET /reports/user/<id>` (relatório com e-mail do usuário)
- `POST /categories`
- `PUT /categories/<id>`
- `DELETE /categories/<id>`

Classificadas como públicas: `GET /`, `GET /health`, `POST /login`, `POST /users` com role `user` (signup) e as rotas de tasks (`/tasks*`, `GET /users/<id>/tasks`). Tasks são o fluxo de trabalho colaborativo do produto, sem modelo de dono (`user_id` é só o responsável, e é opcional). Exigir admin ali quebraria o uso principal da API.
Evidence:
```python
'token': 'fake-jwt-token-' + str(user.id)
```
Impact: qualquer cliente anônimo vira admin, apaga usuários, altera categorias e lê dados pessoais e relatórios.
Recommendation: token assinado de verdade (`itsdangerous`, que já vem com o Flask, usando `SECRET_KEY`) emitido no login + decorator `require_auth` exigindo `Bearer` válido com papel `admin` (ou o próprio usuário em `GET/PUT /users/<id>` e `GET /reports/user/<id>`) em cada rota listada (Playbook P10).

### #6 [HIGH] Configuração insegura (AP12)
File: app.py:11, 15, 34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` fixo, `CORS(app)` sem restrição de origens, `SQLALCHEMY_DATABASE_URI` literal.
Evidence:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```
Impact: o debugger do Werkzeug exposto na rede permite execução remota de código. CORS aberto permite que qualquer site chame a API.
Recommendation: `DEBUG`, `HOST`, `PORT`, `DATABASE_URL` e `CORS_ORIGINS` vindos de env com defaults seguros (Playbook P1).

### #7 [HIGH] Regras de negócio nos handlers (Fat Controller) (AP07)
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299; routes/user_routes.py:42-90, 92-132, 153-183; routes/report_routes.py:12-101, 103-155
Description: cada handler faz parse, validação, checagem de FKs, regra de "overdue", agregações de estatística, persistência e serialização no mesmo corpo. `create_task` tem 70 linhas e `summary_report` tem 90 linhas de agregação. `report_routes.py` também abriga o CRUD de categorias, que é outro domínio.
Impact: nenhuma regra pode ser testada sem HTTP, e a regra de overdue já está copiada em 6 lugares (#12).
Recommendation: controllers/services por domínio (`task`, `user`, `category`, `report`), com rotas finas que só delegam (Playbook P4).

### #8 [HIGH] Acoplamento forte sem injeção de dependência / sem app factory (AP08)
File: app.py:9-31; seed.py:2; services/notification_service.py:5-15
Description: o `app` é criado, configurado e faz `db.create_all()` no momento do import do módulo. `seed.py` importa esse objeto global. `NotificationService` lê credenciais literais no construtor e instancia `smtplib.SMTP` direto em `send_email`, sem como trocar o transporte.
Impact: impossível subir o app com outra config (teste ou produção) sem editar código, e impossível testar o service sem SMTP real.
Recommendation: `create_app(config)` como composition root; service recebendo config/transporte por parâmetro (Playbook P5).

### #9 [MEDIUM] Queries N+1 e COUNTs repetidos (AP13)
File: routes/task_routes.py:41-57, 275-279; routes/user_routes.py:22, 140-142; routes/report_routes.py:19-28, 55-56, 159-163
Description: `GET /tasks` faz `User.query.get` e `Category.query.get` para cada task (1 + 2N). `GET /users` faz `len(u.tasks)` por usuário. O summary faz 9 `COUNT` separados por status/prioridade e uma query de tasks por usuário. `GET /categories` faz um `COUNT` por categoria. `/tasks/stats` faz 5 `COUNT` + `all()`.
Impact: o número de queries cresce linearmente com os dados, e a latência dos relatórios explode.
Recommendation: `joinedload`/`selectinload`, `GROUP BY` com `func.count` (Playbook P7).

### #10 [MEDIUM] Validação de entrada ausente ou inconsistente (AP15)
File: routes/task_routes.py:93-100, 113, 166-184, 260-264; routes/user_routes.py:102-103, 124-125; routes/report_routes.py:196-202
Description: `priority < 1` com `priority` string do JSON gera `TypeError` → 500. `len(data['title'])` no PUT quebra com `null`/número. `int(request.args['priority'])` em `/tasks/search` gera `ValueError` → 500. `update_category` não checa `if not data` (`'name' in None` → 500) nem valida `color` (`is_valid_color` existe e não é usado). `update_user` aceita `name` vazio e `active` de qualquer tipo. O create de task faz `strip` só em helpers, nunca chamado.
Impact: entradas inválidas viram 500 ou dados corrompidos.
Recommendation: validadores centralizados por entidade, usados em create e update, devolvendo 400 (Playbook P13).

### #11 [MEDIUM] Tratamento de erros genérico e sem handler central (AP16)
File: routes/task_routes.py:62, 137, 151, 204, 221, 236; routes/user_routes.py:87, 130, 149; routes/report_routes.py:186, 207, 221
Description: nove `except:` puros e três `except Exception` que engolem o erro. `get_tasks` (:62) mascara qualquer bug como `{'error': 'Erro interno'}` sem log. Não existe `@app.errorhandler`, e cada handler repete `try/rollback/return 500`.
Impact: bugs somem sem rastro, e o formato de erro depende do handler.
Recommendation: exceções de domínio (`NotFound`, `ValidationError`, `Conflict`) + error handler central com log (Playbook P8).

### #12 [MEDIUM] Código duplicado (AP14)
File: routes/task_routes.py:17-39, 71-80, 110, 177, 283-287; routes/user_routes.py:61, 71, 106, 120, 171-180; routes/report_routes.py:34-36, 132-135
Description: a regra "atrasada" (due_date < agora e status ∉ {done, cancelled}) é reimplementada em 6 lugares, ignorando `Task.is_overdue` (models/task.py:50-60). A serialização de task em `get_tasks` duplica `Task.to_dict`. A lista de status aparece em task_routes.py:110, 177, models/task.py:39 e utils/helpers.py:75, 110. O regex de e-mail e a lista de roles estão duplicados em create/update e em `helpers.py`. `process_task_data` (helpers.py:57-108) reimplementa a validação de task e não é usada.
Impact: correções precisam ser feitas em N lugares, e as versões já divergem (mensagens de erro diferentes entre create e update).
Recommendation: regra no model, constantes únicas e um validador por entidade (Playbook P13).

### #13 [MEDIUM] Integridade referencial ausente (AP19)
File: routes/report_routes.py:211-223; models/task.py:13-14, 20-21
Description: `DELETE /categories/<id>` apaga a categoria e deixa as tasks com `category_id` apontando para um registro inexistente (o SQLite não aplica FKs por padrão e não há `ondelete`). O delete de usuário faz cascata manual em loop (user_routes.py:140-142) em vez de declarar a relação.
Impact: tasks órfãs com `category_id` inválido e relatórios inconsistentes.
Recommendation: tratar os filhos na regra de deleção (desassociar `category_id`) e declarar `cascade` no relacionamento user→tasks (Playbook P11).

### #14 [MEDIUM] Uso de APIs deprecated (AP17)
File: ver tabela da seção Deprecated APIs
Description: 16 chamadas a `Model.query.get(id)` (legacy no SQLAlchemy 2.x, com `LegacyAPIWarning`) e 20 usos de `datetime.utcnow` (deprecated no Python 3.12).
Impact: warnings hoje e quebra quando a API for removida.
Recommendation: `db.session.get(Model, id)` e um helper `utcnow()` baseado em `datetime.now(timezone.utc)` (Playbook P12).

### #15 [LOW] Imports não usados e código morto (AP22)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; models/task.py:3; utils/helpers.py:2-116
Description: `os, sys, json` (app.py), `json, os, sys, time` (task_routes), `hashlib, json` (user_routes), `format_date, calculate_percentage, json` (report_routes) e `json` (models/task.py) não são usados. Em helpers.py, `os, json, sys, math, hashlib` também não, e nenhuma função ou constante do módulo é chamada fora dele. `Task.validate_status`, `validate_priority`, `is_overdue` e `User.is_admin` nunca são chamados, e `NotificationService` nunca é instanciado.
Impact: ruído que esconde a lógica real e dá falsa impressão de que a validação existe.
Recommendation: remover os imports e o código morto, ou reaproveitar o que tiver valor (Playbook P14).

### #16 [LOW] Magic numbers e strings (AP20)
File: routes/task_routes.py:96, 99, 104, 113, 182; routes/user_routes.py:64, 115; routes/report_routes.py:24-28, 129, 180
Description: limites literais de título (3/200), prioridade (1..5, default 3), senha mínima 4, "alta prioridade" = `priority <= 2`, cor default `'#000000'` e o mapeamento 1..5 → `critical..minimal` solto no relatório. As constantes de helpers.py:110-116 existem, mas ninguém as usa.
Impact: regras espalhadas que divergem quando alguém altera uma delas.
Recommendation: constantes de domínio num módulo único (Playbook P13).

### #17 [LOW] `print` no lugar de logging (AP23)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39-41
Description: eventos e erros vão para stdout via `print`, sem nível nem contexto.
Impact: sem filtragem por nível e sem integração com agregadores de log.
Recommendation: `logging.getLogger(__name__)` (Playbook P14).

### #18 [LOW] Condicionais verbosas e aninhamento desnecessário (AP24)
File: models/task.py:38-60; models/user.py:34-38; routes/task_routes.py:30-39, 141, 210; utils/helpers.py:103
Description: `if x: return True else: return False` em `validate_status`, `validate_priority` e `is_admin`. Três níveis de `if` aninhados em `is_overdue` e nas cópias da regra. `type(tags) == list` em vez de `isinstance`.
Impact: ruído de leitura e mais pontos onde errar.
Recommendation: expressões booleanas diretas e `isinstance` (Playbook P14).

### #19 [LOW] Nomenclatura ruim (AP21)
File: routes/report_routes.py:24-28; models/category.py:14; routes/task_routes.py:16, 51
Description: `p1..p5` para contagens por prioridade, `d` no `to_dict` de categoria, `t`/`u`/`c`/`cat` em loops longos.
Impact: leitura mais lenta. Nada de grave.
Recommendation: nomes descritivos nas variáveis internas, sem tocar nos campos do contrato (Playbook P14).

## Deprecated APIs
| Location | Deprecated API | Modern replacement |
|---|---|---|
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227 | `Model.query.get(id)` (legacy SQLAlchemy 2.0) | `db.session.get(Model, id)` |
| routes/user_routes.py:29, 94, 136, 155 | `Model.query.get(id)` | `db.session.get(Model, id)` |
| routes/report_routes.py:105, 192, 213 | `Model.query.get(id)` | `db.session.get(Model, id)` |
| models/task.py:15, 16, 52; models/user.py:14; models/category.py:11 | `datetime.utcnow` (deprecated no Python 3.12) | `datetime.now(timezone.utc)` |
| routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133 | `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| utils/helpers.py:38; services/notification_service.py:35; seed.py:66, 67, 69, 70, 74 | `datetime.utcnow()` | `datetime.now(timezone.utc)` |

Também verificado, sem ocorrências: `before_first_request`, `JSONEncoder`/`json_encoder`, `from flask import escape/Markup`, `engine.execute`/SQL string em `session.execute`, `marshmallow missing=/default=`, `pkg_resources`.

## Architecture Notes
- Current: camadas parciais. As pastas existem, mas `routes/*.py` concentra validação, regras, queries e serialização. `services/` e `utils/` estão mortos, não há app factory, config nem tratamento de erros centralizado, e não existe autenticação real. Não classifiquei como God File (AP03): cada arquivo de rotas cobre basicamente um domínio e tem menos de 300 linhas, então o problema é de Fat Controller (#7).
- Target: `config.py` + `create_app()` → `routes/` (blueprints finos) → `controllers/` (validação + regras por domínio) → `models/` (ORM + regras de entidade), com `middlewares/` (auth + error handler) e `services/` (notificação injetável).

================================
Total: 19 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

## Resposta do usuário

```
y
```

## Fase 3 (refatoração e validação)

````text
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
task-manager-api/
├── app.py                       # create_app() (composition root) + entry point; ainda expõe `app` para o seed
├── seed.py
├── .env.example
├── config/settings.py
├── database.py                  # db + PersistenceMixin (save/delete com rollback)
├── models/
│   ├── constants.py
│   ├── task.py  user.py  category.py
├── controllers/
│   ├── validators.py
│   ├── task_controller.py  user_controller.py  auth_controller.py
│   ├── category_controller.py  report_controller.py
├── routes/                      # View: blueprints finos + proteção declarada por rota
│   ├── responses.py  system_routes.py  task_routes.py
│   ├── user_routes.py  category_routes.py  report_routes.py
├── services/
│   ├── notification_service.py  token_service.py
├── middlewares/
│   ├── error_handler.py  auth.py
└── utils/dates.py               # utils/helpers.py removido (código morto)
```

## Findings Resolved
- #1 AP05 — Hash exposto nas respostas: `User.to_dict()` não inclui mais `password` nos quatro endpoints (P9).
- #2 AP01 — `SECRET_KEY` hardcoded: agora vem de `config/settings.py` via env. Sem a variável, a chave é efêmera (P1).
- #3 AP01 — Credenciais SMTP hardcoded: vêm de env (`SMTP_*`) e são injetadas via `EmailSettings` (P1, P5).
- #4 AP06 — MD5 sem salt: troquei por werkzeug (scrypt). Um hash MD5 legado é aceito uma vez no login e regravado no formato novo, migração validada (P9).
- #5 AP11 — Auth falsa: o token agora é assinado (`itsdangerous` + `SECRET_KEY`, com expiração), e `require_auth` está aplicado nas 10 rotas da lista (P10).
- #6 AP12 — Config insegura: `DEBUG` desligado, host `127.0.0.1`, `PORT`, `DATABASE_URL` e `CORS_ORIGINS` vêm de env (P1).
- #7 AP07 — Fat controllers: a lógica foi para controllers por domínio, e as rotas só delegam. A regra de overdue mora em `Task.is_overdue`. Categorias saíram de `report_routes` para arquivo próprio (P4).
- #8 AP08 — Sem DI: `create_app()` monta config, db, `TokenService`, `NotificationService` e controllers, e o service recebe o `smtp_factory` (P5).
- #9 AP13 — N+1: `joinedload` em `GET /tasks`; `GROUP BY` em users, categorias, stats e relatórios (P7).
- #10 AP15 — Validação: `controllers/validators.py` é compartilhado por create e update. Os casos que davam 500 agora dão 400 (P13).
- #11 AP16 — Erros: nenhum `except:` restou. O handler central converte exceções de domínio em `{'error': ...}`; erro inesperado vira 500 genérico com stack trace no log e rollback (P8).
- #12 AP14 — Duplicação: um só lugar para regra de overdue, serialização (`to_dict*`), constantes e validadores (P13).
- #13 AP19 — Integridade: cascade user→tasks declarado no relacionamento (fim do loop manual) e FKs com `ondelete`. Correção do relatório: o backref padrão do ORM já anulava `category_id` no delete original (testei no baseline). O risco real era menor do que descrevi; o que mudou foi tornar o comportamento explícito (P11).
- #14 AP17 — Deprecated: `db.session.get`/`db.select` e `utils.dates.utcnow()`. App e seed sobem com `-W error::DeprecationWarning` sem erro (P12).
- #15 AP22 — Código morto: imports não usados removidos e `utils/helpers.py` apagado. `NotificationService` agora é usado: notifica na atribuição de task, com envio desligado por padrão (P14).
- #16 AP20 — Magic numbers: `models/constants.py` (P13).
- #17 AP23 — `print`: virou `logging` em todo o código da aplicação (P14).
- #18 AP24 — Condicionais: expressões booleanas diretas e `isinstance` (P14).
- #19 AP21 — Nomenclatura: nomes descritivos nas variáveis internas, sem tocar no contrato (P14).

## Protected Routes
- GET /users — Bearer + papel `admin`
- GET /users/<id> — Bearer + `admin` ou o próprio usuário
- PUT /users/<id> — Bearer + `admin` ou o próprio usuário (só `admin` altera `role`/`active`)
- DELETE /users/<id> — Bearer + `admin`
- POST /users (quando `role` ≠ `user`) — Bearer + `admin`
- GET /reports/summary — Bearer + `admin`
- GET /reports/user/<id> — Bearer + `admin` ou o próprio usuário
- POST /categories — Bearer + `admin`
- PUT /categories/<id> — Bearer + `admin`
- DELETE /categories/<id> — Bearer + `admin`

## Not Fully Resolved
None.

Uma decisão de escopo que vale você revisar: as rotas de `/tasks*` continuam públicas, porque tasks não têm dono no modelo de dados (`user_id` é só o responsável, e é opcional). Se quiser exigir login ali, é um decorator por rota.

## Intentional Contract Changes
- `password` saiu das respostas de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` (em `user`).
- O campo `token` do `POST /login` continua com o mesmo nome, mas agora é um token assinado com expiração em vez de `fake-jwt-token-<id>`. Ele é exigido como `Authorization: Bearer` nas 10 rotas acima, que respondem 401 sem token e 403 sem o papel exigido.
- Entradas de tipo inválido que antes estouravam 500 agora devolvem 400 (`priority` string, `?priority=abc`, `title: null` no PUT, PUT de categoria sem body). Cor inválida em categoria também passou a dar 400.
- 404/405 de rota inexistente agora vêm em JSON (`{'error': ...}`) em vez de HTML.

## Validation
  ✓ Application boots without errors (`python seed.py && PORT=5055 python app.py`, sem stack trace, com `-W error::DeprecationWarning`)
  ✓ All endpoints respond correctly (43/43 match baseline). O cenário cobre os 22 endpoints em 43 passos. Status e mensagens de erro são idênticos em todos; 38 têm shape idêntico e os outros 5 diferem só pelo `password` removido, que é intencional.
  ✓ Zero CRITICAL/HIGH anti-patterns remaining. Na re-varredura não sobrou nenhum segredo literal, `except:`, `global`, `print`, `utcnow`, `query.get` nem query em loop. O único `md5` é a leitura do hash legado.
  ✓ As 10 rotas protegidas (17 chamadas no cenário) dão 401 sem credencial e respondem igual ao baseline com Bearer de admin
  ✓ 403 com token de papel `user`, acesso do próprio usuário liberado, token adulterado ou o antigo `fake-jwt-token-1` dão 401
  ✓ Hash MD5 legado migrado para scrypt no primeiro login
  ✓ Delete de usuário remove as tasks dele; delete de categoria não deixa `category_id` órfão
  ✓ Erro inesperado devolve `{'error': 'Erro interno'}` com stack trace só no log
  ✓ `compileall` sem erros
  ✓ Limpeza feita: temporários e bancos apagados, porta 5055 liberada, nenhum `instance/` deixado no projeto

## How to run
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # defina SECRET_KEY
.venv/bin/python seed.py
.venv/bin/python app.py       # http://127.0.0.1:5000; no macOS a 5000 é do AirPlay: use PORT=5055
```
================================
````
