# Assessor Financeiro - Assessment & Roadmap

## 1. Architecture Assessment

### O que esta bom
- Modular monolith claro, com separacao por dominio (router, schemas, service).
- Stack coerente: FastAPI + SQLAlchemy 2.0 + Alembic + Redis.
- Paginacao centralizada e fixtures de testes com SQLite em memoria.

### Falhas tecnicas (com severidade)

| # | Severidade | Falha | Impacto |
|---|-----------|-------|---------|
| 1 | Critica | Valores monetarios em Float | Erros de arredondamento e soma incorreta. | 
| 2 | Critica | Senhas sem validacao de forca | Qualquer senha fraca e aceita. |
| 3 | Alta | Sem rate limit em auth | Brute-force facil e abuse. |
| 4 | Alta | Dependencia get_current_user em router | Acoplamento e risco de circular import. |
| 5 | Alta | state.token inexistente | Fluxo inconsistente no frontend. |
| 6 | Alta | XSS por innerHTML sem escape | Execucao de script via merchant/descricao. |
| 7 | Alta | Falta de cascade delete | Erros de FK ao excluir conta/categoria. |
| 8 | Media | Sem CORS | Bloqueia front separado ou app mobile. |
| 9 | Media | Notificacoes sao stub | Endpoint nao faz envio real. |
|10 | Media | Pagination com count + all | Duas queries por chamada. |
|11 | Media | Sem indices em transacoes | Filtros lentos com volume. |
|12 | Media | Tokens Gmail em Redis sem criptografia | Compromete credenciais. |
|13 | Media | Config Gmail via os.getenv | Inconsistencia com settings. |
|14 | Baixa | Sem timestamps em modelos | Dificulta auditoria. |
|15 | Baixa | Sem versionamento de API | Mudancas quebram clientes. |
|16 | Baixa | Hash pbkdf2 apenas | Melhor com bcrypt/argon2. |
|17 | Baixa | print() em servicos | Falta logging estruturado. |
|18 | Baixa | Budget summary sem scopo por usuario | Pode misturar dados. |

### Gaps funcionais
- Sem transacoes recorrentes (salario, aluguel, assinaturas).
- Orçamentos sem alertas ou notificacoes.
- Saldo de conta nao e recalculado pelas transacoes.
- Exportacao CSV apenas de dados carregados na tela.
- Sem deteccao de duplicidade em transacoes manuais.
- Ordenacao de transacoes nao e garantida por data.

## 2. UX/UI Assessment

### Pontos fortes
- Paleta consistente e tipografia clara.
- Layout responsivo e animacoes leves.
- Dashboard rico (KPIs, tendencia, top categorias).

### Problemas e oportunidades
- Autenticacao confusa: login, registro e token ao mesmo tempo.
- Sem paginacao e sem estados visuais de loading (skeleton/toast).
- Textos sem acentos (Transacoes, Sincronizacao, etc).
- Dashboard fica escondido na aba Contas.
- Sem dark mode.
- Categoria escondida no dashboard, deveria ter aba propria.

## 3. Roadmap Detalhado

### Fase 1 - Seguranca e Integridade (Semana 1-2)
1) Trocar Float por Numeric(12,2) (ou inteiro em centavos)

2) Validacao de senha

3) Rate limit

4) Corrigir XSS

5) Cascades e integridade

 **Status:** Concluído
 
 **Resumo da Implementação:**
 * Todos os campos monetários migrados para Decimal/Numeric (SQLAlchemy, Pydantic, Alembic).
 * Validação de senha forte implementada (mínimo 8 caracteres, sem espaços).
 * Rate limiting adicionado nos endpoints de autenticação com SlowAPI (desabilitado em testes).
 * Todas as strings de usuário escapadas no frontend JS.
 * Exclusão em cascata configurada nas relações ORM.
 * Testes atualizados para novas validações e tipos.
 * Migração e testes executados e validados sem erros.
 * Branch: feature/phase1-security-integrity.
1) Indices
- Indices em transactions.transaction_date, category_id, account_id.

2) Ordenacao padrao
- Listagens de transacoes com order_by desc em data.

3) Corrigir budget summary
- Juntar com Account e filtrar por user_id.

4) Recalcular saldo
- Somar transacoes por conta para last_balance.
- Recalcular apos create/update/delete.

### Fase 3 - UX/UI (Semana 3-5)
1) Simplificar autenticacao
- Tela unica com login/registro.
- Esconder cards quando autenticado.

2) Dashboard separado
- Tab dedicado e default.

3) Feedback visual
- Toasts auto-dismiss.
- Skeleton states para listas.

4) Paginação
- Botao carregar mais ou paginacao numerada.

5) Internacionalizacao basica
- Corrigir textos PT-BR com acentos.

6) Dark mode
- CSS variables e toggle no header.

### Fase 4 - Funcionalidades (Semana 5-7)
1) Alertas de orcamento
- Regras: 80% e 100%.
- Exibir no dashboard e notificar.

2) Transacoes recorrentes
- Nova tabela RecurringTransaction.
- Job diario para gerar transacoes.

3) Exportacao server-side
- Endpoint para CSV/PDF com filtros.

4) Charts melhores
- Integrar Chart.js ou uPlot para trend e categorias.

### Fase 5 - Producao (Semana 7-9)
1) Versionamento /api/v1
2) CORS configuravel
3) Health check com DB e Redis
4) Logs estruturados
5) Criptografar tokens Gmail no Redis
6) Consistencia em settings (sem os.getenv)

### Fase 6 - Evolucao (Semana 9+)
- AI categorizer com LLM.
- Importacao OFX/CSV.
- Multi-currency.
- Metas de economia.
- Contas compartilhadas.
- PWA instalavel.
- MFA com TOTP.
