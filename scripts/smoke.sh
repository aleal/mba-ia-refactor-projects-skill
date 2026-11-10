#!/usr/bin/env bash
# Smoke test dos projetos refatorados: sobe a API com banco temporário, chama todas
# as rotas originais e confere o status esperado de cada chamada. As rotas
# privilegiadas são testadas sem credencial (401/403) e com credencial.
#
# Uso: scripts/smoke.sh <code-smells-project|ecommerce-api-legacy|task-manager-api>
# Pré-requisito: dependências instaladas (.venv com requirements.txt, ou node_modules).
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${1:?informe o projeto}"
DIR="$ROOT/$PROJECT"
TMP="$(mktemp -d)"
PORT="${PORT:-5077}"
BASE="http://127.0.0.1:$PORT"
ADMIN_TOKEN="smoke-admin-token"
PID=""
PASS=0
FAIL=0

cleanup() {
  if [ -n "$PID" ]; then kill "$PID" 2>/dev/null; wait "$PID" 2>/dev/null; fi
  rm -rf "$TMP"
}
trap cleanup EXIT

# check STATUS_ESPERADO MÉTODO PATH [CORPO_JSON] [HEADER...]
check() {
  local expected="$1" method="$2" path="$3" body="${4:-}"
  shift 4 2>/dev/null || shift $#
  local args=(-s -o "$TMP/resp" -w "%{http_code}" -X "$method" -H "Content-Type: application/json")
  local auth="-"
  for h in "$@"; do args+=(-H "$h"); auth="${h%%:*}"; done
  [ -n "$body" ] && args+=(-d "$body")
  local code mark
  code=$(curl "${args[@]}" "$BASE$path")
  if [ "$code" = "$expected" ]; then mark="ok"; PASS=$((PASS + 1)); else mark="FAIL (esperado $expected)"; FAIL=$((FAIL + 1)); fi
  printf "%-6s %-38s %-14s -> %s %-4s %s\n" "$method" "$path" "[$auth]" "$code" "$mark" "$(head -c 90 "$TMP/resp" | tr '\n' ' ')"
}

wait_ready() {
  for _ in $(seq 40); do
    curl -s -o /dev/null "$BASE$1" && return 0
    sleep 0.5
  done
  echo "ERRO: a aplicação não subiu"; cat "$TMP/server.log"; exit 1
}

cd "$DIR" || exit 1
echo "== $PROJECT (porta $PORT) =="

case "$PROJECT" in
  code-smells-project)
    ADM="X-Admin-Token: $ADMIN_TOKEN"
    PORT=$PORT DATABASE_PATH="$TMP/loja.db" ADMIN_TOKEN=$ADMIN_TOKEN ENABLE_ADMIN_QUERY=true ENABLE_ADMIN_RESET=true \
      .venv/bin/python app.py > "$TMP/server.log" 2>&1 & PID=$!
    wait_ready /health
    echo "-- rotas públicas"
    check 200 GET /
    check 200 GET /health
    check 200 GET /produtos
    check 200 GET "/produtos/busca?q=Mouse&preco_max=100"
    check 200 GET /produtos/1
    check 404 GET /produtos/999
    check 201 POST /usuarios '{"nome":"Ana","email":"ana@x.com","senha":"s3nh4"}'
    check 200 POST /login '{"email":"ana@x.com","senha":"s3nh4"}'
    check 401 POST /login "{\"email\":\"admin@loja.com' --\",\"senha\":\"x\"}"
    check 201 POST /pedidos '{"usuario_id":2,"itens":[{"produto_id":2,"quantidade":2}]}'
    check 400 POST /pedidos '{"usuario_id":2,"itens":[{"produto_id":2,"quantidade":-5}]}'
    echo "-- rotas privilegiadas (finding AP11): sem credencial e com X-Admin-Token"
    check 401 POST /produtos '{"nome":"Caneca","preco":30,"estoque":5,"categoria":"geral"}'
    check 201 POST /produtos '{"nome":"Caneca","preco":30,"estoque":5,"categoria":"geral"}' "$ADM"
    check 401 PUT /produtos/11 '{"nome":"Caneca","preco":31,"estoque":5,"categoria":"geral"}'
    check 200 PUT /produtos/11 '{"nome":"Caneca","preco":31,"estoque":5,"categoria":"geral"}' "$ADM"
    check 401 GET /usuarios
    check 200 GET /usuarios '' "$ADM"
    check 401 GET /usuarios/2
    check 200 GET /usuarios/2 '' "$ADM"
    check 401 GET /pedidos
    check 200 GET /pedidos '' "$ADM"
    check 401 GET /pedidos/usuario/2
    check 200 GET /pedidos/usuario/2 '' "$ADM"
    check 401 PUT /pedidos/1/status '{"status":"aprovado"}'
    check 200 PUT /pedidos/1/status '{"status":"aprovado"}' "$ADM"
    check 401 GET /relatorios/vendas
    check 200 GET /relatorios/vendas '' "$ADM"
    check 401 DELETE /produtos/11
    check 200 DELETE /produtos/11 '' "$ADM"
    check 401 POST /admin/query '{"sql":"SELECT COUNT(*) AS n FROM produtos"}'
    check 200 POST /admin/query '{"sql":"SELECT COUNT(*) AS n FROM produtos"}' "$ADM"
    check 401 POST /admin/reset-db ''
    check 200 POST /admin/reset-db '' "$ADM"
    ;;

  ecommerce-api-legacy)
    ADM="X-Admin-Token: $ADMIN_TOKEN"
    PORT=$PORT ADMIN_TOKEN=$ADMIN_TOKEN node src/app.js > "$TMP/server.log" 2>&1 & PID=$!
    wait_ready /api/checkout
    echo "-- rotas públicas"
    check 200 POST /api/checkout '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
    check 400 POST /api/checkout '{"usr":"João","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}'
    check 404 POST /api/checkout '{"usr":"X","eml":"x@t.com","pwd":"x","c_id":99,"card":"4111"}'
    check 400 POST /api/checkout '{"usr":"X"}'
    echo "-- rotas privilegiadas (finding AP11): sem credencial e com X-Admin-Token"
    check 401 GET /api/admin/financial-report
    check 403 GET /api/admin/financial-report '' "X-Admin-Token: errado"
    check 200 GET /api/admin/financial-report '' "$ADM"
    check 401 DELETE /api/users/1
    check 200 DELETE /api/users/1 '' "$ADM"
    check 200 GET /api/admin/financial-report '' "$ADM"
    ;;

  task-manager-api)
    export PORT DATABASE_URL="sqlite:///$TMP/tasks.db"
    .venv/bin/python seed.py | tail -4
    .venv/bin/python app.py > "$TMP/server.log" 2>&1 & PID=$!
    wait_ready /health
    login() {  # imprime o token do usuário
      curl -s -X POST -H "Content-Type: application/json" -d "{\"email\":\"$1\",\"password\":\"$2\"}" "$BASE/login" \
        | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])"
    }
    ADMIN="Authorization: Bearer $(login joao@email.com 1234)"   # role admin no seed
    USER="Authorization: Bearer $(login maria@email.com abcd)"   # role user no seed
    echo "-- rotas públicas"
    check 200 GET /
    check 200 GET /health
    check 200 GET /tasks
    check 200 GET /tasks/1
    check 404 GET /tasks/999
    check 200 GET "/tasks/search?q=login&status=in_progress"
    check 200 GET /tasks/stats
    check 201 POST /tasks '{"title":"Nova task","priority":2,"user_id":1,"category_id":1,"tags":["a","b"],"due_date":"2026-12-01"}'
    check 400 POST /tasks '{"title":"x"}'
    check 200 PUT /tasks/11 '{"status":"in_progress"}'
    check 200 DELETE /tasks/11
    check 200 GET /users/1/tasks
    check 200 GET /categories
    check 201 POST /users '{"name":"Ana","email":"ana@x.com","password":"abcd"}'
    check 200 POST /login '{"email":"joao@email.com","password":"1234"}'
    echo "-- rotas privilegiadas (finding AP11): sem token, token falso, papel user e admin"
    check 401 GET /users
    check 401 GET /users '' "Authorization: Bearer fake-jwt-token-1"
    check 403 GET /users '' "$USER"
    check 200 GET /users '' "$ADMIN"
    check 401 GET /users/1
    check 200 GET /users/1 '' "$ADMIN"
    check 401 PUT /users/4 '{"name":"Ana B"}'
    check 200 PUT /users/4 '{"name":"Ana B"}' "$ADMIN"
    check 401 POST /users '{"name":"Eve","email":"eve@x.com","password":"abcd","role":"admin"}'
    check 201 POST /users '{"name":"Eve","email":"eve@x.com","password":"abcd","role":"admin"}' "$ADMIN"
    check 401 GET /reports/summary
    check 200 GET /reports/summary '' "$ADMIN"
    check 401 GET /reports/user/1
    check 200 GET /reports/user/1 '' "$ADMIN"
    check 401 POST /categories '{"name":"QA","color":"#123456"}'
    check 201 POST /categories '{"name":"QA","color":"#123456"}' "$ADMIN"
    check 401 PUT /categories/5 '{"name":"QA2"}'
    check 200 PUT /categories/5 '{"name":"QA2"}' "$ADMIN"
    check 401 DELETE /categories/5
    check 200 DELETE /categories/5 '' "$ADMIN"
    check 401 DELETE /users/4
    check 200 DELETE /users/4 '' "$ADMIN"
    ;;

  *) echo "projeto desconhecido: $PROJECT"; exit 1 ;;
esac

echo "-- resultado: $PASS/$((PASS + FAIL)) verificações ok; tracebacks no log do servidor: $(grep -c Traceback "$TMP/server.log")"
[ "$FAIL" -eq 0 ]
