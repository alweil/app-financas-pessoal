import unittest

from app.modules.ai_agent.service import categorize_transaction
from app.modules.ai_agent.schemas import CategorizationRequest


class CategorizerTests(unittest.TestCase):
    def test_transport_uber(self):
        payload = CategorizationRequest(merchant="Uber Trip", description=None)
        result = categorize_transaction(payload)
        self.assertEqual(result.category_name, "Transporte")
        self.assertEqual(result.subcategory_name, "Uber/99")

    def test_food_market(self):
        payload = CategorizationRequest(merchant="Supermercado Assai", description=None)
        result = categorize_transaction(payload)
        self.assertEqual(result.category_name, "Alimentação")
        self.assertEqual(result.subcategory_name, "Supermercado")


if __name__ == "__main__":
    unittest.main()
