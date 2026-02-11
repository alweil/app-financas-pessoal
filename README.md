# Assessor Financeiro (Backend)

![CI](https://github.com/alweil/app-financas-pessoal/actions/workflows/ci.yml/badge.svg)

Backend modular monolítico para registrar contas, transações, categorias (com subcategorias), orçamentos e ingestão de notificações por email.
Roda em produção no Railway com Postgres e Redis.

Inclui um frontend simples servido em / via FastAPI, com arquivos em app/static.

## Pré-requisitos
- Python 3.11+
- Docker (para Postgres e Redis)

## Quick Start
1. Copie `.env.example` para `.env` e ajuste as variáveis.
2. Suba Postgres e Redis com `docker-compose up -d`.
3. Instale dependências com `python -m pip install -r requirements.txt`.
4. Rode migrações com `alembic upgrade head`.
5. Inicie a API com `uvicorn app.main:app --reload`.

Atalhos (opcional): use `make infra-up`, `make migrate`, `make run`.

## Configuração
1. Copie o arquivo .env.example para .env e ajuste as variáveis.
2. Suba os serviços de banco e fila com Docker Compose.
3. Instale as dependências Python.
4. Execute as migrações do Alembic.
5. Inicie a API.

## Execução sem Docker
Alguns endpoints funcionam sem banco. Para isso:
1. Instale as dependências Python.
2. Inicie a API.

Endpoints que funcionam sem banco:
- GET /health
- POST /email/parse
- POST /email/parse-to-transaction
- POST /ai/categorize

## Scripts principais
- Iniciar API: uvicorn app.main:app --reload
- Migrações Alembic: alembic upgrade head

## Variáveis de ambiente
- APP_NAME
- ENVIRONMENT
- DATABASE_URL
- REDIS_URL
- SECRET_KEY
- ACCESS_TOKEN_EXPIRE_MINUTES
- GMAIL_CLIENT_ID (opcional)
- GMAIL_CLIENT_SECRET (opcional)
- GMAIL_PROJECT_ID (opcional)
- GMAIL_REDIRECT_URI (opcional)

## Endpoints

### Autenticacao
POST /auth/register
Payload:
{
	"email": "user@example.com",
	"password": "secret"
}

POST /auth/token
Form data:
- username
- password

GET /auth/me
Headers:
- Authorization: Bearer <token>

### Saúde
GET /health

### Email Parser
POST /email/parse
Payload:
{
	"message_id": "string",
	"from_address": "string",
	"subject": "string",
	"body": "string",
	"bank_source": "string|null"
}

POST /email/parse-to-transaction
Payload:
{
	"account_id": 1,
	"category_id": 10,
	"email": { ... RawEmailIngest ... }
}

POST /email/parse-and-create
Payload:
{
	"account_id": 1,
	"category_id": 10,
	"email": { ... RawEmailIngest ... }
}

### AI Agent
POST /ai/categorize
Payload:
{
	"merchant": "string|null",
	"description": "string|null"
}

### Contas
POST /accounts
Payload:
{
	"bank_name": "string",
	"account_type": "checking|savings|credit_card|investment",
	"nickname": "string|null"
}

PUT /accounts/{account_id}
Payload:
{
	"bank_name": "string|null",
	"account_type": "checking|savings|credit_card|investment|null",
	"nickname": "string|null"
}

DELETE /accounts/{account_id}

### Categorias
POST /categories
Payload:
{
	"name": "string",
	"parent_id": 1,
	"icon": "string|null",
	"color": "string|null"
}

### Transações
POST /transactions
Payload:
{
	"account_id": 1,
	"amount": 10.5,
	"merchant": "string|null",
	"description": "string|null",
	"transaction_date": "2026-02-04T10:00:00Z",
	"transaction_type": "purchase|pix_in|pix_out|unknown",
	"payment_method": "credit_card|debit_card|pix|boleto",
	"card_last4": "1234",
	"installments_total": 5,
	"installments_current": 2,
	"category_id": 10,
	"raw_email_id": 100
}

GET /transactions?account_id=1&start_date=2026-02-01T00:00:00Z&end_date=2026-02-08T23:59:59Z&category_id=10

PUT /transactions/{transaction_id}
Payload:
{
	"account_id": 1,
	"amount": 10.5,
	"merchant": "string|null",
	"description": "string|null",
	"transaction_date": "2026-02-04T10:00:00Z",
	"transaction_type": "purchase|pix_in|pix_out|unknown|null",
	"payment_method": "credit_card|debit_card|pix|boleto|null",
	"card_last4": "1234|null",
	"installments_total": 5,
	"installments_current": 2,
	"category_id": 10
}

DELETE /transactions/{transaction_id}

### Orçamentos
POST /budgets
Payload:
{
	"category_id": 1,
	"amount_limit": 1000,
	"period": "weekly|monthly|yearly",
	"start_date": "2026-02-01T00:00:00Z"
}

## Frontend (UI)
O frontend em / permite autenticar, criar contas e sincronizar o Gmail.

Passos:
1. Use o bloco Criar Usuario para registrar um email e senha.
2. Use o bloco Login para obter o token via /auth/token.
3. O token fica salvo no navegador e e usado nas chamadas protegidas.
4. O email do usuario logado aparece no bloco Autenticacao.
5. Use o botao Limpar Token para sair.
6. Crie contas no bloco Nova Conta.

## Assessment (Resumo Tecnico)

### Pontos fortes
- Arquitetura modular monolitica bem separada por dominio (router, schemas, service).
- Stack consistente: FastAPI + SQLAlchemy 2.0 + Alembic + Redis.
- Testes com SQLite em memoria e fixtures de limpeza automatica.

### Riscos e falhas prioritarias
- Valores monetarios usam Float, com risco de erro de arredondamento. Preferir Numeric(12,2) ou inteiro em centavos.
- Falta de validacao de senha e rate limit nos endpoints de autenticao.
- Possivel XSS no frontend ao interpolar dados em innerHTML sem escaping.
- Relacionamentos sem cascade podem falhar ao excluir contas/categorias com transacoes.
- Budget summary filtra apenas por categoria e nao garante escopo por usuario.

### Gaps funcionais
- Sem recorrencia de transacoes (assinaturas, aluguel, salario).
- Orçamentos sem alertas de excesso ou proximidade.
- Saldo de conta nao e recalculado a partir das transacoes.
- Exportacao CSV limitada aos dados carregados na tela.

### UX/UI
- Fluxo de autenticacao confuso (tres cards simultaneos).
- Ausencia de controles de paginacao e feedback visual (toasts, loading states).
- Nomenclatura sem acentos PT-BR em diversos textos.

## Roadmap (Implementacao)

### Fase 1 - Seguranca e integridade (1-2 semanas)
- Migrar valores monetarios para Numeric e atualizar schemas.
- Implementar validacao de senha e rate limit em /auth.
- Corrigir XSS com escaping de strings no frontend.
- Ajustar cascades e integridade referencial.

### Fase 2 - Performance e dados (2-3 semanas)
- Adicionar indices em transactions (date, category_id, account_id).
- Padronizar ordenacao por data nas listagens.
- Recalcular saldo da conta a partir de transacoes.
- Corrigir escopo por usuario no budget summary.

### Fase 3 - UX/UI (3-5 semanas)
- Tornar Dashboard o ponto inicial e criar tabs dedicadas.
- Simplificar fluxo de login/registro e esconder cards quando autenticado.
- Adicionar paginacao, toasts e estados de carregamento.
- Corrigir textos PT-BR e adicionar modo escuro.

### Fase 4 - Funcionalidades (5-7 semanas)
- Alertas de orcamento e notificacoes reais.
- Transacoes recorrentes e job scheduler.
- Exportacao server-side de CSV/PDF.
- Charts com biblioteca leve (ex: Chart.js ou uPlot).

### Fase 5 - Producao (7-9 semanas)
- Versionamento de API (/api/v1).
- CORS configuravel.
- Logs estruturados e health check com DB/Redis.
- Criptografar tokens Gmail no Redis.
7. Na aba Transacoes, crie, edite, exclua e filtre transacoes.
8. Na aba Sincronizar, selecione a conta desejada antes de iniciar a sync.

## Seeds de categorias
O arquivo de seeds está em app/seeds/categories.py. A função seed_default_categories está em app/modules/categories/service.py.

## Seed de usuario admin
Use app/seeds/users.py para criar um usuario admin via script, por exemplo:
python -c "from app.core.database import SessionLocal; from app.seeds.users import seed_admin_user; db=SessionLocal(); seed_admin_user(db, 'admin@example.com', 'secret')"

## Observações
- O endpoint /email/parse-and-create depende do banco e grava a transação com vínculo ao email bruto.
- O campo card_last4 é preenchido quando encontrado nos emails.
- O OAuth do Gmail armazena estado e credenciais no Redis.

## Estrutura
- app/modules/accounts
- app/modules/categories
- app/modules/transactions
- app/modules/budgets
- app/modules/email_parser
- app/modules/ai_agent
- app/modules/notifications
