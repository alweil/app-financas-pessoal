from app.modules.email_parser.parser import parse_email
from app.modules.email_parser.schemas import RawEmailIngest


def test_nubank_purchase():
    payload = RawEmailIngest(
        message_id="1",
        from_address="todomundo@nubank.com.br",
        subject="Compra aprovada",
        body="Compra de R$ 123,45 aprovada em PADARIA CENTRAL em 03/02/2026 no crédito 2/5 parcelas - cartão final 1234",
        bank_source=None,
    )
    result = parse_email(payload)
    assert result.success is True
    assert result.amount == 123.45
    assert result.merchant == "PADARIA CENTRAL"
    assert result.transaction_type == "purchase"
    assert result.payment_method == "credit_card"
    assert result.installments_current == 2
    assert result.installments_total == 5
    assert result.card_last4 == "1234"


def test_pix_sent():
    payload = RawEmailIngest(
        message_id="2",
        from_address="todomundo@nubank.com.br",
        subject="Pix enviado",
        body="Pix de R$ 50,00 enviado para JOAO SILVA em 03/02/2026",
        bank_source=None,
    )
    result = parse_email(payload)
    assert result.success is True
    assert result.amount == 50.0
    assert result.transaction_type == "pix_out"
    assert result.payment_method == "pix"


def test_itau_purchase():
    payload = RawEmailIngest(
        message_id="3",
        from_address="itau@itau-unibanco.com.br",
        subject="Compra com cartão",
        body="Compra aprovada: R$ 85,90 - SUPERMERCADO X no débito Cartão ***4321",
        bank_source=None,
    )
    result = parse_email(payload)
    assert result.success is True
    assert result.amount == 85.90
    assert result.merchant == "SUPERMERCADO X"
    assert result.payment_method == "debit_card"
    assert result.card_last4 == "4321"


def test_btg_purchase():
    payload = RawEmailIngest(
        message_id="4",
        from_address="cartoes@btgpactual.com",
        subject="Compra aprovada",
        body="Compra aprovada: R$ 210,00 em LOJA Y - Cartão ***9876",
        bank_source=None,
    )
    result = parse_email(payload)
    assert result.success is True
    assert result.amount == 210.0
    assert result.merchant == "LOJA Y"
    assert result.payment_method == "credit_card"
    assert result.card_last4 == "9876"
