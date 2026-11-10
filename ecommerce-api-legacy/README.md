# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
ADMIN_TOKEN=troque-este-token npm start
```

A aplicação sobe em `http://localhost:3000`. Por padrão o banco SQLite é em memória e carrega seeds automaticamente no boot.

Variáveis de ambiente (veja `.env.example`):

| Variável | Default | Uso |
|---|---|---|
| `PORT` | `3000` | porta HTTP |
| `DB_PATH` | `:memory:` | arquivo SQLite (seeds só rodam com o banco vazio) |
| `ADMIN_TOKEN` | vazio | token do header `X-Admin-Token`; vazio = rotas admin bloqueadas |
| `PAYMENT_GATEWAY_KEY` | vazio | chave do gateway de pagamento |
| `LOG_LEVEL` | `info` | `debug`, `info`, `warn`, `error` |

Rotas administrativas (`GET /api/admin/financial-report`, `DELETE /api/users/:id`) exigem o header `X-Admin-Token`: sem ele → 401, token errado → 403.

Exemplos de requisições estão em `api.http`.

## Estrutura

```
src/
├── app.js            # entry point (npm start): config → banco → createApp → listen
├── server.js         # composition root: monta models, services, controllers e rotas
├── config/           # variáveis de ambiente e constantes de domínio
├── database/         # conexão sqlite3 com Promises, transações, schema e seed
├── models/           # acesso a dados por entidade (users, courses, enrollments, payments, audit_logs, relatório)
├── services/         # checkout (transação) e gateway de pagamento
├── controllers/      # validação de entrada e fluxo de cada caso de uso
├── routes/           # mapeamento método + path → controller (camada View)
├── middlewares/      # tratamento central de erros e autenticação admin
└── utils/            # logger e hash de senha (scrypt)
```
