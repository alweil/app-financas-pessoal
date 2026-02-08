from app.modules.ai_agent.service import categorize_transaction
from app.modules.ai_agent.schemas import CategorizationRequest


def test_transport_uber():
    payload = CategorizationRequest(merchant="Uber Trip", description=None)
    result = categorize_transaction(payload)
    assert result.category_name == "Transporte"
    assert result.subcategory_name == "Uber/99"


def test_food_market():
    payload = CategorizationRequest(merchant="Supermercado Assai", description=None)
    result = categorize_transaction(payload)
    assert result.category_name == "Alimentação"
    assert result.subcategory_name == "Supermercado"
