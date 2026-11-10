# Execução da skill `/refactor-arch` — ecommerce-api-legacy

Saída do Claude Code em modo headless (`claude -p "/refactor-arch"`, seguido de `claude -p "y" --resume <sessão>`).

## Fases 1 e 2 (análise e auditoria, pausa para confirmação)

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js — sem "engines" declarado; runtime local v26.11.1)
Framework:     Express ^4.18.2
Dependencies:  express ^4.18.2, sqlite3 ^5.1.6
Database:      SQLite em memória (':memory:') via driver puro sqlite3 (callbacks, SQL manual)
Domain:        LMS com checkout (usuários, cursos, matrículas, pagamentos, logs de auditoria)
Architecture:  Monolítica / God Class — AppManager.js concentra conexão, schema, seeds, rotas, queries e regras de checkout/relatório
Entry point:   src/app.js (npm start → node src/app.js, porta 3000)
Source files:  3 files analyzed (~180 lines)
DB tables:     users, courses, enrollments, payments, audit_logs
Endpoints:     3 routes
================================
```

| Método | Path | Handler | Observação |
|---|---|---|---|
| POST | /api/checkout | src/AppManager.js:28 | escrita em vários passos (user + enrollment + payment + audit) |
| GET | /api/admin/financial-report | src/AppManager.js:80 | ⚠ admin, expõe receita e nomes de alunos |
| DELETE | /api/users/:id | src/AppManager.js:131 | ⚠ **destrutivo**: apaga usuário e deixa registros órfãos |

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express 4 (SQLite in-memory, sqlite3 driver)
Files:   3 analyzed | ~180 lines of code
Date:    2026-11-10

## Summary
CRITICAL: 6 | HIGH: 4 | MEDIUM: 5 | LOW: 5

| # | Severity | ID | Finding | Location |
|---|---|---|---|---|
| 1 | CRITICAL | AP01 | Credenciais e segredos hardcoded | src/utils.js:2-5 |
| 2 | CRITICAL | AP05 | Número do cartão e chave do gateway em log | src/AppManager.js:45 |
| 3 | CRITICAL | AP11 | Rotas privilegiadas sem autenticação/autorização | src/AppManager.js:80, 131 |
| 4 | CRITICAL | AP06 | Armazenamento inseguro de senhas | src/utils.js:17-23; src/AppManager.js:18, 68-69 |
| 5 | CRITICAL | AP10 | Checkout em múltiplos passos sem transação / callback hell | src/AppManager.js:37-77 |
| 6 | CRITICAL | AP03 | God Class AppManager | src/AppManager.js:4-139 |
| 7 | HIGH | AP07 | Regras de negócio dentro das rotas | src/AppManager.js:43-75, 89-127 |
| 8 | HIGH | AP08 | Acoplamento forte sem injeção de dependência | src/AppManager.js:7; src/app.js:8-10 |
| 9 | HIGH | AP09 | Estado global mutável | src/utils.js:9-10, 12-15, 25 |
| 10 | HIGH | AP12 | Configuração fixa no código | src/utils.js:6; src/AppManager.js:7 |
| 11 | MEDIUM | AP13 | Queries N+1 no relatório financeiro | src/AppManager.js:83, 92, 104, 106 |
| 12 | MEDIUM | AP15 | Validação de entrada ausente | src/AppManager.js:29-35, 46, 132 |
| 13 | MEDIUM | AP16 | Tratamento de erros silencioso e inconsistente | src/AppManager.js:35-70, 57, 92-93, 104-106, 133-135; src/app.js:5-10 |
| 14 | MEDIUM | AP19 | Integridade referencial ausente | src/AppManager.js:13-15, 133-135 |
| 15 | MEDIUM | AP18 | Cobrança no gateway inline no handler | src/AppManager.js:45-46, 59 |
| 16 | LOW | AP17 | API do sqlite3 só com callbacks | src/AppManager.js:37-135 |
| 17 | LOW | AP20 | Magic numbers e magic strings | src/AppManager.js:21, 46, 48, 68, 108; src/utils.js:19-22 |
| 18 | LOW | AP21 | Nomenclatura ruim | src/AppManager.js:4, 26, 29-33; src/utils.js:17 |
| 19 | LOW | AP22 | Código morto e imports não usados | src/utils.js:2-3, 5, 9-10, 14; src/AppManager.js:2 |
| 20 | LOW | AP23 | console.log no lugar de logger | src/app.js:13; src/utils.js:13; src/AppManager.js:45 |

## Findings

### #1 [CRITICAL] Credenciais e segredos hardcoded (AP01)
File: src/utils.js:2-5
Description: O objeto `config` guarda literais sensíveis: `dbPass` = `"senha_super_secreta_prod_123"`, `paymentGatewayKey` = `"pk_live_1234567890abcdef"` (prefixo de chave live), além de `dbUser` e `smtpUser`. Não há leitura de `process.env`.
Evidence:
```js
dbPass: "senha_super_secreta_prod_123",
paymentGatewayKey: "pk_live_1234567890abcdef",
```
Impact: qualquer pessoa com acesso ao repositório obtém a chave do gateway de pagamento e a senha do banco; rotação exige commit + deploy.
Recommendation: mover para módulo `config` lido de variáveis de ambiente, com `.env.example` só com placeholders; remover os segredos não usados (Playbook P1).

### #2 [CRITICAL] Exposição de dados sensíveis em logs (AP05)
File: src/AppManager.js:45
Description: o checkout imprime o número completo do cartão (`cc`, vindo de `req.body.card`) junto com `config.paymentGatewayKey` no stdout a cada requisição.
Evidence:
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
Impact: violação direta de PCI-DSS (PAN em log) e vazamento da chave do gateway para qualquer agregador de logs.
Recommendation: nunca logar cartão nem chave; no máximo os 4 últimos dígitos mascarados (Playbook P9).

### #3 [CRITICAL] Rotas privilegiadas sem autenticação/autorização (AP11)
File: src/AppManager.js:80, 131
Description: nenhuma rota tem middleware de autenticação; o projeto não possui sistema de login. Rotas privilegiadas sem proteção:
- GET /api/admin/financial-report
- DELETE /api/users/:id

A primeira é `/admin/*` sem middleware (sinal de AP04) e devolve receita por curso e nomes de alunos; a segunda apaga qualquer usuário (destrutiva). Severidade elevada de HIGH para CRITICAL por envolver dados financeiros e pessoais. `POST /api/checkout` é pública (ação do próprio cliente).
Evidence:
```js
app.get('/api/admin/financial-report', (req, res) => {
app.delete('/api/users/:id', (req, res) => {
```
Impact: qualquer cliente anônimo lê o faturamento e a lista de alunos, e apaga contas de terceiros.
Recommendation: middleware `requireAdmin` que exige token de administrador (`ADMIN_TOKEN` da config) aplicado às duas rotas (Playbook P10).

### #4 [CRITICAL] Armazenamento inseguro de senhas (AP06)
File: src/utils.js:17-23; src/AppManager.js:18, 68-69
Description: `badCrypto` faz base64 da senha, pega 2 caracteres, repete 10000 vezes e trunca em 10 — é codificação reversível/colidível, sem salt. Se `pwd` não vier, usa senha default `"123456"` (AppManager.js:68). O seed grava `'123'` em texto puro (AppManager.js:18).
Evidence:
```js
hash += Buffer.from(pwd).toString('base64').substring(0, 2);
let hash = badCrypto(p || "123456");
```
Impact: o "hash" depende só dos 2 primeiros caracteres da senha (colisões triviais); usuários sem senha ficam todos com a mesma senha conhecida.
Recommendation: `crypto.scrypt` com salt aleatório (nativo do Node, sem dependência nova); sem senha default (Playbook P9).

### #5 [CRITICAL] Checkout em múltiplos passos sem transação / callback hell (AP10)
File: src/AppManager.js:37-77
Description: o checkout encadeia 5 callbacks (`get course` → `get user` → `INSERT users` → `INSERT enrollments` → `INSERT payments` → `INSERT audit_logs`) sem `BEGIN/COMMIT/ROLLBACK`. O `err` do insert de auditoria (linha 57) é ignorado. Elevado de HIGH para CRITICAL por ser fluxo de dinheiro.
Evidence:
```js
this.db.run("INSERT INTO enrollments ...", [userId, cid], function(err) {
    self.db.run("INSERT INTO payments ...", [enrId, course.price, status], function(err) {
```
Impact: se o insert de pagamento falhar, a matrícula já está gravada — aluno matriculado sem pagamento; usuário criado mesmo quando o pagamento é recusado.
Recommendation: wrapper com Promises + `async/await` e transação única para usuário/matrícula/pagamento/auditoria (Playbook P11).

### #6 [CRITICAL] God Class AppManager (AP03)
File: src/AppManager.js:4-139
Description: a classe `AppManager` faz conexão com o banco (7), DDL (12-16), seeds (18-21), registro de rotas (25-137), queries, regra de pagamento (46), criação de usuário e agregação do relatório financeiro.
Evidence:
```js
initDb() { this.db.serialize(() => { this.db.run("CREATE TABLE users ...
setupRoutes(app) {
```
Impact: impossível testar uma regra sem subir HTTP + banco; qualquer mudança afeta todo o sistema.
Recommendation: separar em `config/`, `db/` (conexão + schema + seed), `models/`, `controllers/`, `routes/`, `middlewares/` (Playbook P3).

### #7 [HIGH] Regras de negócio dentro das rotas (AP07)
File: src/AppManager.js:43-75, 89-127
Description: o handler de `/api/checkout` decide aprovação do pagamento (`cc.startsWith("4")`), cria usuário e matrícula; o de `/api/admin/financial-report` soma receita só de pagamentos `PAID` e monta a lista de alunos com contadores manuais (`coursesPending`, `enrPending`).
Evidence:
```js
let status = cc.startsWith("4") ? "PAID" : "DENIED";
if (payment && payment.status === 'PAID') { courseData.revenue += payment.amount; }
```
Impact: regras de cobrança e de receita não são reutilizáveis nem testáveis sem HTTP.
Recommendation: mover para controllers/serviços (`checkoutController`, `reportController`), deixando as rotas finas (Playbook P4).

### #8 [HIGH] Acoplamento forte sem injeção de dependência (AP08)
File: src/AppManager.js:7; src/app.js:8-10
Description: o construtor instancia `new sqlite3.Database(':memory:')` diretamente; o mesmo objeto dono do banco registra as rotas (`manager.setupRoutes(app)`); não há app factory.
Evidence:
```js
this.db = new sqlite3.Database(':memory:');
manager.setupRoutes(app);
```
Impact: impossível trocar o banco por ambiente ou injetar um fake em testes.
Recommendation: composition root (`createApp({ db, config })`) que cria a conexão e a injeta nos models/controllers (Playbook P5).

### #9 [HIGH] Estado global mutável (AP09)
File: src/utils.js:9-10, 12-15, 25
Description: `let globalCache = {}` é mutado por `logAndCache` a cada checkout e exportado; `let totalRevenue = 0` é exportado como estado de módulo.
Evidence:
```js
let globalCache = {};
let totalRevenue = 0;
```
Impact: cache sem limite cresce indefinidamente (vazamento de memória por e-mail/usuário) e é compartilhado entre requisições.
Recommendation: remover o cache global (não é lido em lugar nenhum) e o contador morto (Playbook P6).

### #10 [HIGH] Configuração fixa no código (AP12)
File: src/utils.js:6; src/AppManager.js:7
Description: `port: 3000` e o caminho do banco `':memory:'` são literais, sem variável de ambiente. Não há debug nem CORS configurados (não aplicável).
Evidence:
```js
port: 3000
```
Impact: não é possível mudar porta ou banco por ambiente sem editar código.
Recommendation: `PORT` e `DB_PATH` lidos de `process.env` com defaults seguros (Playbook P1).

### #11 [MEDIUM] Queries N+1 no relatório financeiro (AP13)
File: src/AppManager.js:83, 92, 104, 106
Description: 1 query de cursos + 1 query de matrículas por curso + 2 queries (usuário e pagamento) por matrícula: 1 + C + 2E queries.
Evidence:
```js
courses.forEach(c => { this.db.all("SELECT * FROM enrollments WHERE course_id = ?", ...
this.db.get("SELECT name, email FROM users WHERE id = ?", ...
```
Impact: latência cresce linearmente com o número de matrículas.
Recommendation: uma única query com `LEFT JOIN` courses/enrollments/users/payments e agregação em memória (Playbook P7).

### #12 [MEDIUM] Validação de entrada ausente (AP15)
File: src/AppManager.js:29-35, 46, 132
Description: só verifica presença de `usr`, `eml`, `c_id`, `card`. Não valida tipo: `card` numérico (`4111...` sem aspas) faz `cc.startsWith` lançar `TypeError` dentro do callback do sqlite3, o que **derruba o processo**. `eml` sem validação de formato; `:id` do DELETE não é validado.
Evidence:
```js
if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");
```
Impact: uma requisição malformada derruba a API inteira (DoS trivial).
Recommendation: validação explícita de tipos/formatos no controller, devolvendo 400 (Playbook P13).

### #13 [MEDIUM] Tratamento de erros silencioso e inconsistente (AP16)
File: src/AppManager.js:35-70, 57, 92-93, 104-106, 133-135; src/app.js:5-10
Description: erros em texto puro (`res.send("Erro DB")`) misturados com sucesso em JSON; `err` ignorado nas linhas 57, 92 (se falhar, `enrollments.length` lança), 104, 106 e 133 (DELETE responde sucesso mesmo com erro ou id inexistente); não há middleware `(err, req, res, next)`.
Evidence:
```js
this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
    res.send("Usuário deletado, ...");
```
Impact: falhas somem, o cliente recebe sucesso falso e exceções em callbacks derrubam o processo.
Recommendation: `async/await` + middleware central de erros com resposta JSON padronizada (Playbook P8).

### #14 [MEDIUM] Integridade referencial ausente (AP19)
File: src/AppManager.js:13-15, 133-135
Description: `enrollments.user_id`, `enrollments.course_id` e `payments.enrollment_id` não têm `FOREIGN KEY`; o DELETE de usuário não trata matrículas/pagamentos — a própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco".
Evidence:
```js
res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
```
Impact: o relatório financeiro passa a mostrar alunos "Unknown" com receita de usuários inexistentes.
Recommendation: FKs com `ON DELETE CASCADE` + `PRAGMA foreign_keys = ON`, ou delete de filhos na mesma transação (Playbook P11).

### #15 [MEDIUM] Cobrança no gateway inline no handler (AP18)
File: src/AppManager.js:45-46, 59
Description: a "chamada" ao gateway de pagamento (log com a chave + decisão de aprovação) e o cache de último checkout (`logAndCache`) acontecem no meio do handler, sem abstração injetável.
Evidence:
```js
let status = cc.startsWith("4") ? "PAID" : "DENIED";
logAndCache(`last_checkout_${userId}`, course.title);
```
Impact: impossível trocar o gateway simulado pelo real ou desligá-lo em testes.
Recommendation: `paymentGateway` como dependência injetada no controller de checkout (Playbook P4).

### #16 [LOW] API do sqlite3 só com callbacks (AP17)
File: src/AppManager.js:37-135
Description: todo acesso a dados usa a API de callbacks do `sqlite3` (`db.get/run/all` com callback), padrão legado em código novo. Rebaixado para LOW: estilo, sem remoção prevista; o efeito estrutural já está coberto no #5.
Evidence:
```js
this.db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [cid], (err, course) => {
```
Impact: favorece o callback hell e dificulta transações e tratamento de erros.
Recommendation: wrapper com Promises (`util.promisify`/funções `run/get/all` async) (Playbook P12).

### #17 [LOW] Magic numbers e magic strings (AP20)
File: src/AppManager.js:21, 46, 48, 68, 108; src/utils.js:19-22
Description: regra de aprovação por prefixo `"4"`; status `"PAID"`/`"DENIED"` como strings soltas repetidas; senha default `"123456"`; `10000` e `10` no `badCrypto`.
Evidence:
```js
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```
Impact: regras escondidas em literais; typo num status quebra a soma de receita silenciosamente.
Recommendation: constantes nomeadas (`PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`) (Playbook P13).

### #18 [LOW] Nomenclatura ruim (AP21)
File: src/AppManager.js:4, 26, 29-33; src/utils.js:17
Description: variáveis `u`, `e`, `p`, `cid`, `cc`; `const self = this`; classe genérica `AppManager`; função `badCrypto`. Os campos do contrato (`usr`, `eml`, `pwd`, `c_id`, `card`) serão mantidos — só as variáveis internas mudam.
Evidence:
```js
let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd;
```
Impact: leitura e revisão difíceis.
Recommendation: nomes descritivos (`name`, `email`, `password`, `courseId`, `cardNumber`) (Playbook P14).

### #19 [LOW] Código morto e imports não usados (AP22)
File: src/utils.js:2-3, 5, 9-10, 14; src/AppManager.js:2
Description: `config.dbUser`, `config.dbPass` e `config.smtpUser` nunca são lidos; `totalRevenue` é importado em AppManager.js:2 e nunca usado; `globalCache` é escrito (utils.js:14) e nunca lido. Confirmado com `grep` no projeto.
Evidence:
```js
const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');
```
Impact: ruído e segredos que existem só para vazar.
Recommendation: remover (Playbook P14).

### #20 [LOW] console.log no lugar de logger (AP23)
File: src/app.js:13; src/utils.js:13; src/AppManager.js:45
Description: banner de inicialização, log de cache e log de pagamento via `console.log`, sem níveis.
Evidence:
```js
console.log(`[LOG] Salvando no cache: ${key}`);
```
Impact: sem nível nem controle de verbosidade em produção.
Recommendation: logger mínimo com níveis (`console.info/error` encapsulado em `utils/logger`), sem dados sensíveis (Playbook P14).

## Deprecated APIs
| Location | Deprecated API | Modern replacement |
|---|---|---|
| src/AppManager.js:37-135 | sqlite3 API só de callbacks (padrão legado) | wrapper com Promises + `async/await` |

Verificado também, sem ocorrências: `new Buffer(` (o código usa `Buffer.from`), `url.parse(`, `crypto.createCipher(`, `fs.exists(`, `body-parser` (usa `express.json()`), `res.send(status, body)`/`res.json(obj, status)`/`req.param()`/`app.del(`, pacotes `request`/`node-uuid`.

## Architecture Notes
- Current: Monolítica / God Class — `AppManager` é dono do banco e das rotas, com checkout e relatório em callbacks aninhados sem transação.
- Target: `src/{config, db, models, controllers, routes, middlewares, services}` com `createApp()` como composition root; `src/app.js` continua sendo o entry point de `npm start`.

================================
Total: 20 findings
================================
````

Ponto que vale destacar: o `#12` não é só cosmético. Um `"card": 4111...` numérico lança `TypeError` dentro do callback do sqlite3 e **mata o processo**, ou seja, qualquer cliente anônimo derruba a API com um POST. E nenhuma query tem SQL injection: todas usam `?`. A interpolação da linha 57 está no parâmetro, não no SQL.

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
ecommerce-api-legacy/
├── .env.example
├── README.md
├── api.http
├── package.json                  # "start": "node src/app.js" (inalterado)
└── src/
    ├── app.js                    # entry point: config → openDatabase → createApp → listen
    ├── server.js                 # composition root (createApp)
    ├── config/
    │   ├── index.js              # PORT, DB_PATH, ADMIN_TOKEN, PAYMENT_GATEWAY_KEY, LOG_LEVEL
    │   └── constants.js          # PAYMENT_STATUS, APPROVED_CARD_PREFIX, UNKNOWN_STUDENT
    ├── database/
    │   ├── connection.js         # wrapper Promise (run/get/all) + transaction() serializada
    │   └── schema.js             # DDL com FKs ON DELETE CASCADE + seed
    ├── models/
    │   ├── userModel.js  courseModel.js  enrollmentModel.js
    │   ├── paymentModel.js  auditLogModel.js
    │   └── reportModel.js        # relatório financeiro em 1 query
    ├── services/
    │   ├── checkoutService.js    # orquestra o checkout numa transação
    │   └── paymentGateway.js     # gateway simulado, injetável
    ├── controllers/
    │   ├── checkoutController.js  reportController.js  userController.js
    ├── routes/
    │   ├── index.js  checkoutRoutes.js  reportRoutes.js  userRoutes.js
    ├── middlewares/
    │   ├── errorHandler.js       # AppError, asyncHandler, handler central
    │   └── auth.js               # requireAdmin (X-Admin-Token, fail-closed)
    └── utils/
        ├── logger.js             # logger com níveis
        └── password.js           # scrypt + salt

## Findings Resolved
#1  AP01 — Segredos hardcoded — config/index.js lê process.env, segredos não usados removidos, .env.example só com placeholders (P1)
#2  AP05 — Cartão e chave em log — gateway loga só os 4 últimos dígitos, nunca a chave (P9)
#3  AP11 — Rotas privilegiadas sem auth — requireAdmin aplicado nas 2 rotas, na definição da rota (P10)
#4  AP06 — Senhas inseguras — scrypt com salt aleatório; seed com hash; sem default "123456" (gera senha aleatória) (P9)
#5  AP10 — Checkout sem transação — async/await + transaction() com BEGIN/COMMIT/ROLLBACK serializada; rollback testado (P11)
#6  AP03 — God Class AppManager — quebrada em config/database/models/services/controllers/routes; AppManager.js apagado (P3)
#7  AP07 — Regras nas rotas — pagamento no PaymentGateway, fluxo no CheckoutService, agregação no ReportModel (P4)
#8  AP08 — Sem DI — createApp({ db, config, logger }) injeta tudo; openDatabase recebe o path (P5)
#9  AP09 — Estado global — globalCache/logAndCache/totalRevenue removidos (nunca eram lidos) (P6)
#10 AP12 — Config fixa — PORT e DB_PATH por variável de ambiente (P1)
#11 AP13 — N+1 no relatório — um único LEFT JOIN + agregação em memória (P7)
#12 AP15 — Validação ausente — parseCheckout valida tipos e e-mail; DELETE valida o id; card numérico agora dá 400, não derruba o processo (P13)
#13 AP16 — Erros silenciosos — nenhum err ignorado; middleware central em texto puro (formato original); JSON malformado → 400 (P8)
#14 AP19 — Integridade referencial — FKs com ON DELETE CASCADE + PRAGMA foreign_keys = ON (P11)
#15 AP18 — Gateway inline — PaymentGateway injetado no CheckoutService (P4)
#16 AP17 — sqlite3 só callbacks — wrapper com Promises em database/connection.js (P12)
#17 AP20 — Magic strings — config/constants.js (P13)
#18 AP21 — Nomes ruins — name/email/password/courseId/cardNumber internamente; contrato usr/eml/pwd/c_id/card mantido (P14)
#19 AP22 — Código morto — dbUser/dbPass/smtpUser, totalRevenue, globalCache removidos; utils.js apagado (P14)
#20 AP23 — console.log — utils/logger.js com níveis (LOG_LEVEL) (P14)

## Protected Routes
GET /api/admin/financial-report — header X-Admin-Token == ADMIN_TOKEN (comparação em tempo constante; 401 sem header, 403 inválido; ADMIN_TOKEN vazio = sempre bloqueado)
DELETE /api/users/:id — header X-Admin-Token == ADMIN_TOKEN (idem)

## Not Fully Resolved
None

## Intentional Contract Changes
- GET /api/admin/financial-report e DELETE /api/users/:id: 401 sem X-Admin-Token, 403 com token inválido (segurança, AP11).
- DELETE /api/users/:id: texto mudou de "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco." para "Usuário deletado, junto com suas matrículas e pagamentos." (o texto antigo passaria a ser falso). Status 200 mantido, inclusive para id inexistente.
- Integridade (AP19): apagar um usuário remove as matrículas e os pagamentos dele, então o relatório deixa de mostrar alunos "Unknown" e a receita fantasma.
- Integridade (AP10): checkout com pagamento recusado não cria mais o usuário (antes ficava um usuário "lixo").
- Entradas inválidas que antes derrubavam o processo (card não-string), davam 500 (JSON malformado) ou um falso 200 (DELETE /api/users/abc) agora dão 400 "Bad Request".

## Validation
  ✓ Application boots without errors (npm start, com e sem ADMIN_TOKEN)
  ✓ All endpoints respond correctly (10/10 match baseline em status + shape; 3 payloads diferem, todos pelas mudanças intencionais acima)
  ✓ Protected routes: 8/8 checagens sem credencial ou com credencial inválida deram 401/403; com token válido, mesmo resultado do baseline; sem ADMIN_TOKEN, fail-closed confirmado
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (re-varredura AP01/02/05/06/09/13 limpa; único match de AP01 é falso positivo, um typeof)
  ✓ Rollback de transação: falha forçada no INSERT de payments deixa users/enrollments/payments intactos
  ✓ Senha do seed gravada como scrypt$salt$hash e verificável
  ✓ node --check em todos os 23 arquivos .js
  ✓ Limpeza: servidores mortos, porta 3000 livre, diretório temporário apagado

## How to run
npm install
ADMIN_TOKEN=troque-este-token npm start
curl -H 'X-Admin-Token: troque-este-token' localhost:3000/api/admin/financial-report
================================
````
