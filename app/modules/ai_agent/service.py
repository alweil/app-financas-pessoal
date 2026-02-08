from app.modules.ai_agent.rules import RULES, normalize
from app.modules.ai_agent.schemas import CategorizationRequest, CategorizationResponse


def categorize_transaction(payload: CategorizationRequest) -> CategorizationResponse:
    text = normalize(f"{payload.merchant or ''} {payload.description or ''}")
    for rule in RULES:
        for keyword in rule.keywords:
            normalized_keyword = normalize(keyword)
            if normalized_keyword and normalized_keyword in text:
                return CategorizationResponse(
                    category_id=None,
                    category_name=rule.category,
                    subcategory_name=rule.subcategory,
                    reason=f"Regra por palavra-chave: {keyword}",
                )
    return CategorizationResponse(
        category_id=None,
        category_name="Outros",
        subcategory_name="Outros",
        reason="Sem correspondência",
    )
