import unittest

from app.modules.email_parser.parser import parse_email
from app.modules.email_parser.schemas import RawEmailIngest


class EmailParserTests(unittest.TestCase):
    def test_nubank_purchase(self):
        payload = RawEmailIngest(
            message_id="1",
            from_address="todomundo@nubank.com.br",
            subject="Compra aprovada",
            body="Compra de R$ 123,45 aprovada em PADARIA CENTRAL em 03/02/2026 no crédito 2/5 parcelas - cartão final 1234",
            bank_source=None,
        )
        result = parse_email(payload)
        self.assertTrue(result.success)
        self.assertEqual(result.amount, 123.45)
        self.assertEqual(result.merchant, "PADARIA CENTRAL")
        self.assertEqual(result.transaction_type, "purchase")
        self.assertEqual(result.payment_method, "credit_card")
        self.assertEqual(result.installments_current, 2)
        self.assertEqual(result.installments_total, 5)
        self.assertEqual(result.card_last4, "1234")

    def test_pix_sent(self):
        payload = RawEmailIngest(
            message_id="2",
            from_address="todomundo@nubank.com.br",
            subject="Pix enviado",
            body="Pix de R$ 50,00 enviado para JOAO SILVA em 03/02/2026",
            bank_source=None,
        )
        result = parse_email(payload)
        self.assertTrue(result.success)
        self.assertEqual(result.amount, 50.0)
        self.assertEqual(result.transaction_type, "pix_out")
        self.assertEqual(result.payment_method, "pix")

    def test_itau_purchase(self):
        payload = RawEmailIngest(
            message_id="3",
            from_address="itau@itau-unibanco.com.br",
            subject="Compra com cartão",
            body="Compra aprovada: R$ 85,90 - SUPERMERCADO X no débito Cartão ***4321",
            bank_source=None,
        )
        result = parse_email(payload)
        self.assertTrue(result.success)
        self.assertEqual(result.amount, 85.90)
        self.assertEqual(result.merchant, "SUPERMERCADO X")
        self.assertEqual(result.payment_method, "debit_card")
        self.assertEqual(result.card_last4, "4321")

    def test_btg_purchase(self):
        payload = RawEmailIngest(
            message_id="4",
            from_address="cartoes@btgpactual.com",
            subject="Compra aprovada",
            body="Compra aprovada: R$ 210,00 em LOJA Y - Cartão ***9876",
            bank_source=None,
        )
        result = parse_email(payload)
        self.assertTrue(result.success)
        self.assertEqual(result.amount, 210.0)
        self.assertEqual(result.merchant, "LOJA Y")
        self.assertEqual(result.payment_method, "credit_card")
        self.assertEqual(result.card_last4, "9876")


if __name__ == "__main__":
    unittest.main()
