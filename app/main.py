from fastapi import FastAPI

from app.core.config import settings
from app.modules.accounts.router import router as accounts_router
from app.modules.budgets.router import router as budgets_router
from app.modules.categories.router import router as categories_router
from app.modules.transactions.router import router as transactions_router
from app.modules.email_parser.router import router as email_parser_router
from app.modules.ai_agent.router import router as ai_agent_router
from app.modules.notifications.router import router as notifications_router

app = FastAPI(title=settings.app_name)

app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(budgets_router)
app.include_router(email_parser_router)
app.include_router(ai_agent_router)
app.include_router(notifications_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
