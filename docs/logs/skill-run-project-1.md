# Execução da skill `/refactor-arch` — code-smells-project

Saída do Claude Code em modo headless (`claude -p "/refactor-arch"`, seguido de `claude -p "y" --resume <sessão>`).

## Fases 1 e 2 (análise e auditoria, pausa para confirmação)

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (versão não declarada no projeto; Python 3.9.6 disponível no host)
Framework:     Flask 3.1.1
Dependencies:  flask==3.1.1, flask-cors==5.0.1, sqlite3 (stdlib)
Database:      SQLite (`loja.db`) via driver puro `sqlite3`, SQL manual, conexão global única
Domain:        API de e-commerce (produtos, usuários, pedidos, itens de pedido, relatório de vendas)
Architecture:  Pseudo-camadas — `models.py`/`controllers.py` têm nomes de camada, mas `models.py` concentra SQL concatenado + regras (estoque, desconto), `controllers.py` mistura HTTP, validação, notificação e SQL direto (health), e `app.py` tem rotas admin com SQL inline
Entry point:   app.py (`python app.py`, 0.0.0.0:5000, debug=True)
Source files:  4 files analyzed (~780 lines)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 routes
================================

**Inventário de endpoints** (⚠ = destrutivo/perigoso)

| Método | Path | Handler |
|---|---|---|
| GET | `/` | app.py:32 (`index`) |
| GET | `/produtos` | app.py:11 → controllers.py:5 |
| GET | `/produtos/busca` | app.py:12 → controllers.py:111 |
| GET | `/produtos/<int:id>` | app.py:13 → controllers.py:14 |
| POST | `/produtos` | app.py:14 → controllers.py:24 |
| PUT | `/produtos/<int:id>` | app.py:15 → controllers.py:64 |
| DELETE | `/produtos/<int:id>` | app.py:16 → controllers.py:98 |
| GET | `/usuarios` | app.py:18 → controllers.py:128 |
| GET | `/usuarios/<int:id>` | app.py:19 → controllers.py:136 |
| POST | `/usuarios` | app.py:20 → controllers.py:146 |
| POST | `/login` | app.py:21 → controllers.py:167 |
| POST | `/pedidos` | app.py:23 → controllers.py:188 |
| GET | `/pedidos` | app.py:24 → controllers.py:229 |
| GET | `/pedidos/usuario/<int:usuario_id>` | app.py:25 → controllers.py:222 |
| PUT | `/pedidos/<int:pedido_id>/status` | app.py:26 → controllers.py:237 |
| GET | `/relatorios/vendas` | app.py:28 → controllers.py:257 |
| GET | `/health` | app.py:30 → controllers.py:264 |
| POST | `/admin/reset-db` ⚠ | app.py:47 (`reset_database`) — apaga todas as tabelas |
| POST | `/admin/query` ⚠ | app.py:59 (`executar_query`) — executa SQL arbitrário |

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1 (SQLite via sqlite3)
Files:   4 analyzed | ~780 lines of code
Date:    2026-11-10

## Summary
CRITICAL: 9 | HIGH: 6 | MEDIUM: 6 | LOW: 5

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP04 | Endpoints perigosos sem proteção (SQL arbitrário, reset) | app.py:47-57, 59-78 |
| 2 | CRITICAL | AP02 | SQL Injection | models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-166, 174, 188, 192, 220, 224, 279-281, 289-297 |
| 3 | CRITICAL | AP05 | Health check expõe secret key e config interna | controllers.py:284-290 |
| 4 | CRITICAL | AP06 | Senhas armazenadas e comparadas em texto puro | models.py:109-111, 126-129; database.py:75-83 |
| 5 | CRITICAL | AP05 | Senhas devolvidas nas respostas de usuários | models.py:83, 99 |
| 6 | CRITICAL | AP01 | SECRET_KEY hardcoded | app.py:7 |
| 7 | CRITICAL | AP10 | Criação de pedido sem transação (fluxo de dinheiro) | models.py:133-169 |
| 8 | CRITICAL | AP03 | God File: models.py | models.py:1-314 |
| 9 | CRITICAL | AP03 | Entry point com rotas e SQL direto | app.py:1-88 |
| 10 | HIGH | AP11 | Rotas privilegiadas sem autenticação/autorização | app.py:14-16, 18-19, 24-26, 28, 47, 59 |
| 11 | HIGH | AP12 | Configuração insegura (debug, CORS aberto, bind fixo) | app.py:8-9, 88; database.py:5 |
| 12 | HIGH | AP15 | Validação de entrada ausente em pedidos e produtos | controllers.py:43-46, 81-90, 116-121, 169-170, 195-201, 239-240 |
| 13 | HIGH | AP09 | Conexão global mutável compartilhada entre threads | database.py:4, 7-11 |
| 14 | HIGH | AP08 | Acoplamento direto a get_db() e ausência de app factory | models.py:5-286; controllers.py:3, 266; app.py:4, 6, 49, 66 |
| 15 | HIGH | AP07 | Fat controllers (validação, regras e notificação nos handlers) | controllers.py:24-62, 64-96, 188-220, 237-255 |
| 16 | MEDIUM | AP16 | try/except genérico que vaza str(e) | controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78 |
| 17 | MEDIUM | AP13 | Queries N+1 | models.py:139-166, 187-199, 219-231, 239-254 |
| 18 | MEDIUM | AP19 | Integridade referencial ausente | database.py:36-53; models.py:65-70 |
| 19 | MEDIUM | AP14 | Serialização e montagem de pedidos duplicadas | models.py:12-21, 31-40, 304-313, 79-86, 95-102, 171-201, 203-233 |
| 20 | MEDIUM | AP14 | Validação de produto duplicada | controllers.py:28-50, 72-90 |
| 21 | MEDIUM | AP18 | Notificações inline no fluxo | controllers.py:208-210, 247-250 |
| 22 | LOW | AP20 | Magic numbers e strings | models.py:247-262; controllers.py:47-52, 242, 285-286 |
| 23 | LOW | AP23 | print no lugar de logging | controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 219; app.py:56, 83-86 |
| 24 | LOW | AP22 | Imports não usados | models.py:2; database.py:2 |
| 25 | LOW | AP21 | Nomenclatura ruim | controllers.py:56, 160; models.py:24, 89, 187-193 |
| 26 | LOW | AP24 | Retornos e condicionais redundantes | controllers.py:200; models.py:63, 70, 283 |

## Findings

### #1 [CRITICAL] Endpoints perigosos sem proteção (AP04)
File: app.py:47-57, 59-78
Description: `POST /admin/query` executa qualquer SQL vindo do corpo (`dados.get("sql")`) e faz `commit` em não-SELECT; `POST /admin/reset-db` faz `DELETE` em todas as 4 tabelas. Nenhuma das duas tem autenticação, papel ou flag de ambiente.
Evidence:
```python
query = dados.get("sql", "")
cursor.execute(query)
```
Impact: qualquer cliente anônimo lê a tabela `usuarios` inteira (com senhas), altera preços ou apaga o banco com um request.
Recommendation: exigir token administrativo da config (`ADMIN_TOKEN`) via decorator nas duas rotas; tirar o SQL de `app.py` para um controller/model de admin (Playbook P10).

### #2 [CRITICAL] SQL Injection (AP02)
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-166, 174, 188, 192, 220, 224, 279-281, 289-297
Description: todas as queries com valor externo são montadas por concatenação. Campos de texto livre exploráveis: `email`/`senha` no login (109-111), `nome`/`descricao`/`categoria` em criar/atualizar produto (47-50, 57-61), `nome`/`email`/`senha` no cadastro (126-129), `termo` e `categoria` da busca em `LIKE '%...%'` (291, 293). Os demais concatenam ids/números com `str()`.
Evidence:
```python
"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
```
Impact: login com `' OR '1'='1' --` entra como o primeiro usuário (Admin); a busca permite `UNION SELECT` em `usuarios`.
Recommendation: placeholders `?` com tupla de parâmetros em todas as queries; busca com `LIKE ?` e `f"%{termo}%"` como parâmetro (Playbook P2).

### #3 [CRITICAL] Exposição de dados sensíveis no health check (AP05)
File: controllers.py:284-290
Description: `health_check` devolve `secret_key` literal, `db_path`, `debug: True` e `ambiente: "producao"` para qualquer cliente.
Evidence:
```python
"db_path": "loja.db",
"debug": True,
"secret_key": "minha-chave-super-secreta-123"
```
Impact: o segredo de assinatura de sessão do Flask vaza por um endpoint público; permite forjar cookies de sessão.
Recommendation: remover `secret_key`, `db_path` e `debug` da resposta, mantendo `status`, `database`, `counts`, `versao` (Playbook P9).

### #4 [CRITICAL] Senhas armazenadas e comparadas em texto puro (AP06)
File: models.py:109-111, 126-129; database.py:75-83
Description: `criar_usuario` grava `senha` sem hash; `login_usuario` compara `WHERE senha = '...'` no SQL; o seed grava `admin123`, `123456`, `senha123` em claro, inclusive a conta `admin`. O seed roda em todo boot de produção, então não há rebaixamento.
Evidence:
```python
("Admin", "admin@loja.com", "admin123", "admin"),
```
Impact: qualquer leitura do banco (ou via #1/#2) expõe todas as senhas; credencial de admin é pública no repositório.
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash`; login busca por email e verifica o hash em Python; migrar senhas legadas em texto puro no boot (Playbook P9).

### #5 [CRITICAL] Senhas devolvidas nas respostas de usuários (AP05)
File: models.py:83, 99
Description: `get_todos_usuarios` e `get_usuario_por_id` incluem `"senha": row["senha"]` no dict, que `GET /usuarios` e `GET /usuarios/<id>` (controllers.py:128-144) devolvem direto.
Evidence:
```python
"senha": row["senha"],
```
Impact: listagem pública com email + senha de todos os usuários (dados pessoais, LGPD).
Recommendation: serializador de usuário sem o campo `senha` (Playbook P9).

### #6 [CRITICAL] Segredo hardcoded (AP01)
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` literal no código (repetido em controllers.py:289, ver #3).
Evidence:
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```
Impact: quem tem acesso ao repositório tem a chave; rotação exige deploy.
Recommendation: módulo `config` lendo `SECRET_KEY` de variável de ambiente, com `.env.example` (Playbook P1).

### #7 [CRITICAL] Criação de pedido em múltiplos passos sem transação (AP10)
File: models.py:133-169
Description: `criar_pedido` faz INSERT em `pedidos`, N INSERTs em `itens_pedido` e N UPDATEs de estoque sem transação explícita nem rollback; uma exceção no meio (ex.: `item["quantidade"]` ausente na 2ª volta) deixa pedido sem itens pendente na conexão global, que o próximo `commit` de outra requisição grava. A checagem de estoque (144) e a baixa (163-166) não são atômicas. Severidade subida de HIGH para CRITICAL por ser fluxo de dinheiro/estoque.
Evidence:
```python
cursor.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (" + ...
```
Impact: pedidos órfãos, estoque baixado sem pedido, overselling em concorrência.
Recommendation: `with conn:` (commit/rollback automáticos) envolvendo todo o fluxo; baixa de estoque condicional `WHERE estoque >= ?` (Playbook P11).

### #8 [CRITICAL] God File: models.py (AP03)
File: models.py:1-314
Description: 314 linhas cobrindo produtos, usuários, pedidos e relatórios num só módulo, misturando queries, serialização, regras de negócio (validação de estoque e cálculo de total em 139-146, faixas de desconto em 256-262) e autenticação (`login_usuario`).
Impact: impossível testar regras de pedido/desconto sem banco; qualquer mudança toca o arquivo de todos os domínios.
Recommendation: separar `models/` por entidade (só acesso a dados) e mover regras para `controllers/` (Playbook P3).

### #9 [CRITICAL] Entry point com rotas e SQL direto (AP03)
File: app.py:1-88
Description: `app.py` concentra configuração (7-9), registro de todas as rotas (11-30), handlers com SQL inline (`reset_database`, `executar_query`, 47-78) e bootstrap do banco (82).
Impact: o composition root também é camada de dados e de rotas; nada pode ser montado em teste sem subir tudo.
Recommendation: `create_app()` em um módulo de app que só monta config, blueprints e error handlers; `app.py` apenas chama a factory (Playbook P3).

### #10 [HIGH] Autenticação/autorização ausente (AP11)
File: app.py:14, 15, 16, 18, 19, 24, 25, 26, 28, 47, 59
Description: o projeto tem `POST /login`, mas ele não emite token nenhum e nenhuma rota exige credencial. Rotas privilegiadas sem proteção:
- `POST /produtos`
- `PUT /produtos/<int:id>`
- `DELETE /produtos/<int:id>`
- `GET /usuarios`
- `GET /usuarios/<int:id>`
- `GET /pedidos`
- `GET /pedidos/usuario/<int:usuario_id>`
- `PUT /pedidos/<int:pedido_id>/status`
- `GET /relatorios/vendas`
- `POST /admin/reset-db`
- `POST /admin/query`

Impact: qualquer anônimo altera catálogo e preços, aprova/cancela pedidos de terceiros, lê dados pessoais e o faturamento.
Recommendation: decorator `require_admin` validando `X-Admin-Token` contra `ADMIN_TOKEN` da config (comparação em tempo constante), aplicado a cada rota acima (Playbook P10).

### #11 [HIGH] Configuração insegura (AP12)
File: app.py:8-9, 88; database.py:5
Description: `DEBUG = True` fixo e `app.run(host="0.0.0.0", port=5000, debug=True)` expõem o debugger do Werkzeug na rede; `CORS(app)` sem origens; caminho do banco `db_path = "loja.db"` fixo.
Evidence:
```python
app.run(host="0.0.0.0", port=5000, debug=True)
```
Impact: debugger Werkzeug acessível = execução remota de código; qualquer site consome a API.
Recommendation: `DEBUG`, `HOST`, `PORT`, `DATABASE_PATH`, `CORS_ORIGINS` lidos do ambiente com defaults seguros (Playbook P1).

### #12 [HIGH] Validação de entrada ausente ou inconsistente (AP15)
File: controllers.py:43-46, 81-90, 116-121, 169-170, 195-201, 239-240
Description: `criar_pedido` não valida `itens` (sem checar `produto_id`/`quantidade`, tipo ou `quantidade > 0`): quantidade negativa gera total negativo e *aumenta* o estoque. `preco < 0` compara valor do JSON sem checar tipo (string → `TypeError` → 500). `atualizar_produto` não aplica a whitelist de categoria nem o tamanho do nome que `criar_produto` aplica. `login` e `atualizar_status_pedido` chamam `dados.get` sem checar `None` (500 com corpo vazio). `float(preco_min)` sem tratamento → 500. Subido de MEDIUM para HIGH por afetar valores de pedido e estoque.
Evidence:
```python
total = total + (produto["preco"] * item["quantidade"])
```
Impact: pedidos com valor negativo, manipulação de estoque, 500 em entradas triviais.
Recommendation: validadores centrais por recurso, reutilizados em criar/atualizar, com checagem de tipo e faixa (Playbook P13).

### #13 [HIGH] Estado global mutável (AP09)
File: database.py:4, 7-11
Description: `db_connection = None` reatribuída com `global` e aberta com `check_same_thread=False`; uma única conexão e cursor compartilhados por todas as threads do servidor.
Evidence:
```python
global db_connection
db_connection = sqlite3.connect(db_path, check_same_thread=False)
```
Impact: transações de requisições concorrentes se misturam (um commit grava escrita parcial de outra requisição, ver #7).
Recommendation: conexão por requisição em `flask.g` fechada no `teardown_appcontext` (Playbook P6).

### #14 [HIGH] Acoplamento forte sem injeção de dependência (AP08)
File: models.py:5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286; controllers.py:3, 266; app.py:4, 6, 49, 66
Description: cada função de `models.py` chama `get_db()` (singleton global); `controllers.health_check` faz SQL direto via `get_db()`; o `app` é criado na importação do módulo, sem factory.
Impact: impossível apontar para outro banco em testes ou por ambiente.
Recommendation: app factory que configura o caminho do banco; models recebem a conexão do provedor por requisição (Playbook P5).

### #15 [HIGH] Fat controllers (AP07)
File: controllers.py:24-62, 64-96, 188-220, 237-255
Description: os handlers HTTP fazem leitura de `request`, validação, regras de domínio (whitelist de categorias, transições de status), chamada ao model, notificações e serialização no mesmo corpo; `criar_produto` tem 39 linhas de validação inline.
Impact: regras não testáveis sem HTTP e duplicadas entre criar/atualizar.
Recommendation: rotas finas em `views`/blueprints; validação e regras em controllers puros que não conhecem `request` (Playbook P4).

### #16 [MEDIUM] Tratamento de erros genérico que vaza detalhes (AP16)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292; app.py:77-78
Description: 17 cópias de `except Exception as e: return jsonify({"erro": str(e)}), 500`; a mensagem da exceção do sqlite (nomes de tabela/colunas, SQL) vai para o cliente. Não há error handler central.
Evidence:
```python
except Exception as e:
    return jsonify({"erro": str(e)}), 500
```
Impact: vazamento de estrutura do banco, ajudando a explorar #2; formato de erro inconsistente.
Recommendation: `errorhandler` central com exceções de domínio (`ValidationError` → 400, `NotFound` → 404) e 500 genérico com log (Playbook P8).

### #17 [MEDIUM] Queries N+1 (AP13)
File: models.py:139-166, 187-199, 219-231, 239-254
Description: `get_todos_pedidos` e `get_pedidos_usuario` fazem 1 query de pedidos + 1 por pedido para itens + 1 por item para o nome do produto (1 + N + N×M); `criar_pedido` consulta cada produto duas vezes (140 e 155); `relatorio_vendas` faz 5 queries onde um `GROUP BY` resolve.
Impact: latência cresce linearmente com os pedidos; `GET /pedidos` degrada com o volume.
Recommendation: `JOIN itens_pedido/produtos` em uma query agrupada em Python; agregação única no relatório (Playbook P7).

### #18 [MEDIUM] Integridade referencial ausente (AP19)
File: database.py:36-53; models.py:65-70
Description: `pedidos.usuario_id`, `itens_pedido.pedido_id` e `itens_pedido.produto_id` sem `FOREIGN KEY`; `deletar_produto` apaga o produto mesmo com itens de pedido referenciando-o — o código já prevê o órfão com `"Desconhecido"` (models.py:196).
Impact: histórico de pedidos perde o produto; pedidos para `usuario_id` inexistente são aceitos.
Recommendation: validar existência de usuário/produto nas escritas e manter o fallback de leitura; FKs só no schema novo sem quebrar bancos existentes (Playbook P11).

### #19 [MEDIUM] Código duplicado em models.py (AP14)
File: models.py:12-21, 31-40, 304-313, 79-86, 95-102, 171-201, 203-233
Description: o dict de produto é montado 3 vezes, o de usuário 2 vezes, e `get_pedidos_usuario`/`get_todos_pedidos` são quase idênticas (30 linhas cada) diferindo só no `WHERE`.
Impact: correção (ex.: remover `senha`) precisa ser feita em vários lugares; já divergem (`login_usuario` omite senha, os outros não).
Recommendation: funções `_produto_from_row`, `_usuario_from_row` e uma consulta de pedidos parametrizada (Playbook P13).

### #20 [MEDIUM] Validação de produto duplicada (AP14)
File: controllers.py:28-50, 72-90
Description: os mesmos checks de `nome`/`preco`/`estoque` obrigatórios e não negativos são copiados entre `criar_produto` e `atualizar_produto`, e já divergem (atualizar não valida categoria nem tamanho do nome).
Impact: regras divergentes conforme o endpoint.
Recommendation: um único validador de payload de produto (Playbook P13).

### #21 [MEDIUM] Efeitos colaterais inline (AP18)
File: controllers.py:208-210, 247-250
Description: "envio" de e-mail/SMS/push e notificações de aprovação/cancelamento são `print` no meio do handler.
Evidence:
```python
print("ENVIANDO EMAIL: Pedido " + str(resultado["pedido_id"]) + ...)
```
Impact: quando virar integração real, uma falha no envio derruba a requisição; não dá para desligar em testes.
Recommendation: serviço de notificação injetado, chamado pelo controller após o commit (Playbook P4).

### #22 [LOW] Magic numbers e strings (AP20)
File: models.py:247-262; controllers.py:47-52, 242, 285-286
Description: faixas de desconto `10000/5000/1000` e taxas `0.1/0.05/0.02` literais; limites de nome `2`/`200`; listas de categorias e status inline; `"versao": "1.0.0"` e `"ambiente": "producao"` literais.
Impact: regras de negócio escondidas em literais.
Recommendation: constantes nomeadas em um módulo de domínio (Playbook P13).

### #23 [LOW] print no lugar de logging (AP23)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 219; app.py:56, 83-86
Description: eventos e erros via `print`, incluindo email do usuário em login falho (182) e banner de boot.
Impact: sem níveis, sem destino configurável; PII em stdout.
Recommendation: módulo `logging` com logger por módulo (Playbook P14).

### #24 [LOW] Imports não usados (AP22)
File: models.py:2; database.py:2
Description: `import sqlite3` em models.py e `import os` em database.py nunca usados.
Impact: ruído.
Recommendation: remover (Playbook P14).

### #25 [LOW] Nomenclatura ruim (AP21)
File: controllers.py:56, 160; models.py:24, 89, 187-193
Description: `id` sobrescreve o builtin; `cursor2`/`cursor3`/`prod` sem significado; mistura `get_todos_*` (inglês/português).
Impact: legibilidade.
Recommendation: renomear variáveis internas sem tocar o contrato (Playbook P14).

### #26 [LOW] Retornos e condicionais redundantes (AP24)
File: controllers.py:200; models.py:63, 70, 283
Description: `if not itens or len(itens) == 0` é redundante; `atualizar_produto`, `deletar_produto` e `atualizar_status_pedido` retornam `True` incondicionalmente (valor ignorado e sem sentido).
Impact: ruído; o `True` sugere um sinal de sucesso que não existe.
Recommendation: simplificar a condição e retornar `rowcount` ou nada (Playbook P14).

## Deprecated APIs
Nenhuma API deprecated encontrada. Verificado: `before_first_request`, `flask.json.JSONEncoder`/`app.json_encoder`, `from flask import escape/Markup` (Flask 3.1.1), `datetime.utcnow`/`utcfromtimestamp`, `pkg_resources`, SQLAlchemy legacy (`Model.query`, `engine.execute`) — não usados; o projeto usa `sqlite3` puro sem adapters de datetime.

## Architecture Notes
- Current: Pseudo-camadas — `models.py` é um God File com SQL concatenado e regras de negócio, `controllers.py` é a camada HTTP inchada, `app.py` mistura config, rotas e SQL, `database.py` junta conexão global + DDL + seed.
- Target: `app.py` (só chama `create_app`) → `src/config.py`, `src/database.py` (conexão por request + schema/seed), `src/models/` (acesso a dados parametrizado), `src/controllers/` (validação e regras), `src/views/` (blueprints finos), `src/middlewares/` (auth admin + error handlers), `src/services/` (notificações).

================================
Total: 26 findings
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
code-smells-project/
├── app.py                         # entry point: create_app() + app.run()
├── .env.example
├── requirements.txt               # inalterado
├── README.md                      # atualizado
└── src/
    ├── app.py                     # create_app(): composition root
    ├── errors.py                  # AppError, ValidationError, NotFoundError, Unauthorized/Forbidden
    ├── config/settings.py
    ├── database/connection.py     # conexão por request (g), conexão read-only, schema, seed, migração de senhas
    ├── models/
    │   ├── produto_model.py
    │   ├── usuario_model.py
    │   ├── pedido_model.py
    │   └── admin_model.py
    ├── controllers/
    │   ├── produto_controller.py
    │   ├── usuario_controller.py
    │   ├── pedido_controller.py
    │   ├── relatorio_controller.py
    │   ├── sistema_controller.py
    │   └── admin_controller.py
    ├── views/
    │   ├── produto_routes.py
    │   ├── usuario_routes.py
    │   ├── pedido_routes.py
    │   ├── relatorio_routes.py
    │   ├── sistema_routes.py
    │   └── admin_routes.py
    ├── services/notification_service.py
    └── middlewares/
        ├── error_handler.py
        └── auth.py
```
Removed: `controllers.py`, `models.py`, `database.py`.

## Findings Resolved
- #1 AP04 — Endpoints perigosos — `require_admin_token` nas duas rotas, desligadas por padrão (`ENABLE_ADMIN_QUERY`/`ENABLE_ADMIN_RESET`); a query só aceita SELECT, em conexão `query_only`, e o reset roda numa transação (P10)
- #2 AP02 — SQL Injection — todas as queries com `?`; busca com `LIKE ?`; a injeção no login agora dá 401 (antes, 200) (P2)
- #3 AP05 — Health expõe segredo — `secret_key`, `db_path` e `debug` removidos da resposta (P9)
- #4 AP06 — Senhas em texto puro — werkzeug scrypt; seed com hash; senhas em texto puro migradas no boot (P9)
- #5 AP05 — Senha nas respostas — `usuario_to_dict` sem `senha` (P9)
- #6 AP01 — SECRET_KEY hardcoded — vem de `Settings` (env; aleatória se ausente); `.env.example` (P1)
- #7 AP10 — Pedido sem transação — `with db:` + baixa condicional `estoque >= ?`; rollback verificado (P11)
- #8 AP03 — God File models.py — um model por entidade; regras de desconto e total ficam no pedido_model (P3)
- #9 AP03 — Entry point com SQL — `app.py` só chama `create_app()`; o admin foi para model/controller/view (P3)
- #10 AP11 — Rotas privilegiadas sem auth — as 11 rotas exigem `X-Admin-Token`, fail-closed (P10)
- #11 AP12 — Config insegura — debug off, bind 127.0.0.1, porta/banco via env, CORS só com `CORS_ORIGINS` (P1)
- #12 AP15 — Validação ausente — quantidade inteira > 0, tipos de preço/estoque, mesmo validador em criar e atualizar, `None` tratado, `preco_min`/`preco_max` validados (P13)
- #13 AP09 — Conexão global — `flask.g` + `teardown_appcontext`; sem `global`/`check_same_thread` (P6)
- #14 AP08 — Acoplamento — models recebem o provedor de conexão; controllers recebem models e notifier por construtor; app factory (P5)
- #15 AP07 — Fat controllers — views só extraem o request; controllers puros (sem Flask) validam e orquestram (P4)
- #16 AP16 — Erros que vazam detalhes — handler central; 500 genérico com stack só no log; chave `erro` preservada (P8)
- #17 AP13 — N+1 — listagem de pedidos com 1 JOIN; relatório com 1 query agregada; criação de pedido com 1 `IN (...)` (P7)
- #19 AP14 — Duplicação nos models — `produto_to_dict`, `usuario_to_dict`, `_agrupar_pedidos` (P13)
- #20 AP14 — Validação duplicada — `validar_produto` único (P13)
- #21 AP18 — Notificações inline — `NotificationService` injetado, chamado após o commit, com falha isolada (P4)
- #22 AP20 — Magic numbers — `FAIXAS_DESCONTO`, `STATUS_VALIDOS`, `CATEGORIAS_VALIDAS`, `NOME_MIN_LEN`/`NOME_MAX_LEN`, versão/ambiente na config (P13)
- #23 AP23 — print — `logging` configurado no composition root; o email do usuário não vai mais para o log (P14)
- #24 AP22 — Imports não usados — arquivos removidos; nenhum import não usado no código novo (P14)
- #25 AP21 — Nomenclatura — `produto_id`/`usuario_id` no lugar de `id`; fim de `cursor2`/`cursor3` (P14)
- #26 AP24 — Condicionais redundantes — `return True` sem sentido removido; condição de itens simplificada (P14)

## Protected Routes
- POST /produtos — X-Admin-Token
- PUT /produtos/<int:id> — X-Admin-Token
- DELETE /produtos/<int:id> — X-Admin-Token
- GET /usuarios — X-Admin-Token
- GET /usuarios/<int:id> — X-Admin-Token
- GET /pedidos — X-Admin-Token
- GET /pedidos/usuario/<int:usuario_id> — X-Admin-Token
- PUT /pedidos/<int:pedido_id>/status — X-Admin-Token
- GET /relatorios/vendas — X-Admin-Token
- POST /admin/reset-db — X-Admin-Token + `ENABLE_ADMIN_RESET=true`
- POST /admin/query — X-Admin-Token + `ENABLE_ADMIN_QUERY=true` (só SELECT)

## Not Fully Resolved
- #18 AP19 — FKs (`pedidos.usuario_id`, `itens_pedido.pedido_id ON DELETE CASCADE`) só valem para bancos novos; um `loja.db` existente não é migrado (o SQLite não adiciona FK com ALTER). `itens_pedido.produto_id` ficou sem FK de propósito: excluir um produto continua deixando o item apontando para ele, com "Desconhecido" na listagem, como na API original. Fechar isso exige soft delete (`ativo=0`), e isso mudaria o `GET /produtos/<id>` depois do DELETE. A existência do usuário no pedido agora é validada.

## Intentional Contract Changes
- As 11 rotas acima respondem 401 sem `X-Admin-Token` válido; `/admin/*` responde 403 se a flag estiver desligada.
- `GET /usuarios` e `GET /usuarios/<id>` não devolvem mais `senha`.
- `GET /health` não devolve mais `secret_key`, `db_path` nem `debug`.
- `POST /login` com payload de SQL injection agora responde 401 (antes, 200 logado como Admin).
- `POST /admin/query` só aceita SELECT (escrita → 400); SQL inválido → 400 "Query inválida" (antes, 500 com o erro do sqlite).
- `POST /pedidos` rejeita quantidade ≤ 0 ou não inteira, e `usuario_id` inexistente → 400.
- `POST/PUT /produtos` rejeitam preço/estoque não numéricos → 400 (antes, 500); o PUT agora aplica a whitelist de categoria e o tamanho do nome, como o POST.
- Erros 500 devolvem `{"erro": "Erro interno do servidor"}` em vez do `str(e)` interno; 404/405 de rota viram JSON.
- Defaults de execução: bind `127.0.0.1` (antes 0.0.0.0), debug off, CORS desligado sem `CORS_ORIGINS`.
- A senha do `admin@loja.com` no seed vem de `SEED_ADMIN_PASSWORD` (aleatória se ausente); `admin123` deixou de ser o padrão.

## Validation
  ✓ Application boots without errors (`python app.py`, 0 tracebacks no log de boot)
  ✓ All endpoints respond correctly (34/38 requisições idênticas ao baseline em status + shape, cobrindo as 19 rotas; as 4 diferenças são as mudanças intencionais acima)
  ✓ Rotas AP04/AP11: 18/18 requisições → 401 sem credencial e com token errado; com token, o mesmo resultado do baseline; dados intactos após as tentativas sem credencial
  ✓ Fail-closed: sem `ADMIN_TOKEN` configurado → 401; com token e flags desligadas → 403
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (re-varredura AP01/02/04/05/09/12/13/23: só falsos positivos, analisados acima)
  ✓ Transação: pedido que falha no 2º item faz rollback (estoque e contagem de pedidos inalterados)
  ✓ Banco legado com senha em texto puro: migrado para scrypt no boot e o login continua funcionando
  ✓ Erro 500 forçado: o cliente recebe a mensagem genérica; o stack vai só para o log
  ✓ `compileall` OK; diretório temporário, bancos e processos de validação removidos; porta liberada
  ✗ Porta padrão 5000 não testada: ocupada pelo AirPlay Receiver do macOS (ControlCenter). Validei em `PORT=5055`; o default do código continua 5000.

## How to run
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
ADMIN_TOKEN=<token-longo> .venv/bin/python app.py      # http://localhost:5000
# rotas privilegiadas:
curl -H "X-Admin-Token: <token-longo>" localhost:5000/relatorios/vendas
```
================================
````
