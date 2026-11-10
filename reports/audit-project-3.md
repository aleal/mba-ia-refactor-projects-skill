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
