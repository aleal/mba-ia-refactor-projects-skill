# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

A configuração vem de variáveis de ambiente, documentadas em `.env.example` (porta, host, caminho do banco, CORS, debug, tokens). Exemplo:

```bash
ADMIN_TOKEN=um-token-longo PORT=8080 python app.py
```

## Rotas privilegiadas

Exigem o header `X-Admin-Token` com o valor de `ADMIN_TOKEN`. Sem `ADMIN_TOKEN` configurado, respondem sempre 401.

- `POST /produtos`, `PUT /produtos/<id>`, `DELETE /produtos/<id>`
- `GET /usuarios`, `GET /usuarios/<id>`
- `GET /pedidos`, `GET /pedidos/usuario/<id>`, `PUT /pedidos/<id>/status`
- `GET /relatorios/vendas`
- `POST /admin/reset-db` (também exige `ENABLE_ADMIN_RESET=true`)
- `POST /admin/query` (também exige `ENABLE_ADMIN_QUERY=true`; só aceita `SELECT`, em conexão somente leitura)

## Usuários de exemplo

- `joao@email.com` / `123456` e `maria@email.com` / `senha123` (clientes)
- `admin@loja.com`: senha definida por `SEED_ADMIN_PASSWORD` no primeiro boot (aleatória se a variável não existir)

As senhas são gravadas com hash (`werkzeug.security`). Bancos antigos com senha em texto puro são migrados no boot.

## Estrutura

```
app.py                 # entry point: create_app() + app.run()
src/
  app.py               # composition root (create_app)
  errors.py            # exceções de domínio
  config/settings.py   # leitura das variáveis de ambiente
  database/            # conexão por requisição, schema, seed
  models/              # acesso a dados (SQL parametrizado) e regras de entidade
  controllers/         # casos de uso e validação de entrada
  views/               # blueprints (rotas finas) e proteção de rotas
  services/            # notificações
  middlewares/         # tratamento de erros e autenticação administrativa
```
