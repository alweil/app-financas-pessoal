from __future__ import annotations

import re
from datetime import datetime
from typing import Callable, Iterable

from app.modules.email_parser.schemas import ParsedTransaction, RawEmailIngest


def parse_email(payload: RawEmailIngest) -> ParsedTransaction:
    bank = payload.bank_source or detect_bank(payload.from_address, payload.subject)
    body = payload.body or ""

    parsers: list[Callable[[str], ParsedTransaction | None]] = []
    if bank == "nubank":
        parsers = [parse_nubank_purchase, parse_nubank_pix]
    elif bank == "itau":
        parsers = [parse_itau_purchase, parse_itau_pix]
    elif bank == "bradesco":
        parsers = [parse_bradesco_purchase]
    elif bank == "btg":
        parsers = [parse_btg_purchase]
    elif bank == "inter":
        parsers = [parse_inter_purchase]

    for parser in parsers:
        result = parser(body)
        if result:
            result.bank_source = bank
            result.subject = payload.subject
            return result

    fallback = parse_generic(body)
    if fallback:
        fallback.bank_source = bank
        fallback.subject = payload.subject
        return fallback

    return ParsedTransaction(
        success=False,
        bank_source=bank,
        amount=None,
        merchant=None,
        transaction_type=None,
        payment_method=None,
        card_last4=None,
        installments_total=None,
        installments_current=None,
        transaction_date=None,
        description=None,
        subject=payload.subject,
        reason="Formato de email não reconhecido",
    )


def detect_bank(from_address: str, subject: str | None) -> str | None:
    haystack = f"{from_address} {subject or ''}".lower()
    if "nubank" in haystack:
        return "nubank"
    if "itau" in haystack or "itaú" in haystack:
        return "itau"
    if "bradesco" in haystack:
        return "bradesco"
    if "btg" in haystack:
        return "btg"
    if "inter" in haystack:
        return "inter"
    return None


def parse_nubank_purchase(body: str) -> ParsedTransaction | None:
    pattern = r"Compra (?:de|no) R\$\s*([\d\.]+,\d{2}) aprovada em (.+?)(?: em \d{2}/\d{2}/\d{4}|\s+-\s+|$)"
    match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None
    amount = parse_amount(match.group(1))
    merchant = clean_merchant(match.group(2))
    date = parse_date(body)
    payment_method = detect_payment_method(body, default="credit_card")
    installments_current, installments_total = parse_installments(body)
    card_last4 = detect_card_last4(body)
    return ParsedTransaction(
        success=True,
        bank_source=None,
        amount=amount,
        merchant=merchant,
        transaction_type="purchase",
        payment_method=payment_method,
        card_last4=card_last4,
        installments_total=installments_total,
        installments_current=installments_current,
        transaction_date=date,
        description=None,
        subject=None,
        reason="Nubank compra",
    )


def parse_nubank_pix(body: str) -> ParsedTransaction | None:
    pattern = r"Pix de R\$\s*([\d\.]+,\d{2}) (enviado para|recebido de) (.+)"
    match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None
    amount = parse_amount(match.group(1))
    direction = match.group(2).lower()
    counterparty = match.group(3).strip()
    transaction_type = "pix_out" if "enviado" in direction else "pix_in"
    date = parse_date(body)
    return ParsedTransaction(
        success=True,
        bank_source=None,
        amount=amount,
        merchant=counterparty,
        transaction_type=transaction_type,
        payment_method="pix",
        card_last4=None,
        installments_total=None,
        installments_current=None,
        transaction_date=date,
        description=None,
        subject=None,
        reason="Nubank Pix",
    )


def parse_itau_purchase(body: str) -> ParsedTransaction | None:
    pattern = r"Compra aprovada:\s*R\$\s*([\d\.]+,\d{2})\s*-\s*(.+?)(?:\s+no\s+|\s+na\s+|\s+Cart[aã]o|$)"
    match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        pattern = r"Compra com cartão\s*R\$\s*([\d\.]+,\d{2})\s*-\s*(.+?)(?:\s+no\s+|\s+na\s+|\s+Cart[aã]o|$)"
        match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None
    amount = parse_amount(match.group(1))
    merchant = clean_merchant(match.group(2))
    date = parse_date(body)
    payment_method = detect_payment_method(body, default="credit_card")
    installments_current, installments_total = parse_installments(body)
    card_last4 = detect_card_last4(body)
    return ParsedTransaction(
        success=True,
        bank_source=None,
        amount=amount,
        merchant=merchant,
        transaction_type="purchase",
        payment_method=payment_method,
        card_last4=card_last4,
        installments_total=installments_total,
        installments_current=installments_current,
        transaction_date=date,
        description=None,
        subject=None,
        reason="Itaú compra",
    )


def parse_itau_pix(body: str) -> ParsedTransaction | None:
    pattern = r"Transferência PIX realizada:\s*R\$\s*([\d\.]+,\d{2})"
    match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None
    amount = parse_amount(match.group(1))
    date = parse_date(body)
    return ParsedTransaction(
        success=True,
        bank_source=None,
        amount=amount,
        merchant=None,
        transaction_type="pix_out",
        payment_method="pix",
        card_last4=None,
        installments_total=None,
        installments_current=None,
        transaction_date=date,
        description=None,
        subject=None,
        reason="Itaú Pix",
    )


def parse_bradesco_purchase(body: str) -> ParsedTransaction | None:
    amount_match = re.search(r"Valor:\s*R\$\s*([\d\.]+,\d{2})", body, re.IGNORECASE)
    merchant_match = re.search(r"Estabelecimento:\s*(.+)", body, re.IGNORECASE)
    if not amount_match or not merchant_match:
        return None
    amount = parse_amount(amount_match.group(1))
    merchant = clean_merchant(merchant_match.group(1))
    date = parse_date(body)
    payment_method = detect_payment_method(body, default="credit_card")
    installments_current, installments_total = parse_installments(body)
    card_last4 = detect_card_last4(body)
    return ParsedTransaction(
        success=True,
        bank_source=None,
        amount=amount,
        merchant=merchant,
        transaction_type="purchase",
        payment_method=payment_method,
        card_last4=card_last4,
        installments_total=installments_total,
        installments_current=installments_current,
        transaction_date=date,
        description=None,
        subject=None,
        reason="Bradesco compra",
    )


def parse_inter_purchase(body: str) -> ParsedTransaction | None:
    pattern = r"Compra aprovada de R\$\s*([\d\.]+,\d{2}) em (.+)"
    match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None
    amount = parse_amount(match.group(1))
    merchant = clean_merchant(match.group(2))
    date = parse_date(body)
    payment_method = detect_payment_method(body, default="credit_card")
    installments_current, installments_total = parse_installments(body)
    card_last4 = detect_card_last4(body)
    return ParsedTransaction(
        success=True,
        bank_source=None,
        amount=amount,
        merchant=merchant,
        transaction_type="purchase",
        payment_method=payment_method,
        card_last4=card_last4,
        installments_total=installments_total,
        installments_current=installments_current,
        transaction_date=date,
        description=None,
        subject=None,
        reason="Inter compra",
    )


def parse_btg_purchase(body: str) -> ParsedTransaction | None:
    pattern = r"Compra (?:aprovada|realizada):?\s*R\$\s*([\d\.]+,\d{2})\s*(?:em|no)\s*(.+?)(?:\s+-\s+Cart[aã]o|\s+-\s+|$)"
    match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None
    amount = parse_amount(match.group(1))
    merchant = clean_merchant(match.group(2))
    date = parse_date(body)
    payment_method = detect_payment_method(body, default="credit_card")
    installments_current, installments_total = parse_installments(body)
    card_last4 = detect_card_last4(body)
    return ParsedTransaction(
        success=True,
        bank_source=None,
        amount=amount,
        merchant=merchant,
        transaction_type="purchase",
        payment_method=payment_method,
        card_last4=card_last4,
        installments_total=installments_total,
        installments_current=installments_current,
        transaction_date=date,
        description=None,
        subject=None,
        reason="BTG compra",
    )


def parse_generic(body: str) -> ParsedTransaction | None:
    amount_match = re.search(r"R\$\s*([\d\.]+,\d{2})", body)
    if not amount_match:
        return None
    amount = parse_amount(amount_match.group(1))
    date = parse_date(body)
    payment_method = detect_payment_method(body, default=None)
    installments_current, installments_total = parse_installments(body)
    card_last4 = detect_card_last4(body)
    return ParsedTransaction(
        success=True,
        bank_source=None,
        amount=amount,
        merchant=None,
        transaction_type="unknown",
        payment_method=payment_method,
        card_last4=card_last4,
        installments_total=installments_total,
        installments_current=installments_current,
        transaction_date=date,
        description=None,
        subject=None,
        reason="Genérico",
    )


def parse_amount(value: str) -> float:
    cleaned = value.replace(".", "").replace(",", ".").strip()
    return float(cleaned)


def parse_date(text: str) -> datetime | None:
    patterns: Iterable[str] = [
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{2}/\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        date_str = match.group(1)
        if len(date_str) == 10:
            return datetime.strptime(date_str, "%d/%m/%Y")
    return None


def detect_payment_method(text: str, default: str | None) -> str | None:
    haystack = text.lower()
    if "pix" in haystack:
        return "pix"
    if "boleto" in haystack:
        return "boleto"
    if "débito" in haystack or "debito" in haystack:
        return "debit_card"
    if "crédito" in haystack or "credito" in haystack or "cartão" in haystack or "cartao" in haystack:
        return "credit_card"
    return default


def parse_installments(text: str) -> tuple[int | None, int | None]:
    pattern = r"(\d{1,2})\s*(?:/|de)\s*(\d{1,2})\s*(?:parcela|parcelas)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None, None
    current = int(match.group(1))
    total = int(match.group(2))
    return current, total


def detect_card_last4(text: str) -> str | None:
    patterns = [
        r"final\s*(\d{4})",
        r"cart[aã]o\s*\*{2,4}\s*(\d{4})",
        r"\*{2,4}\s*(\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def clean_merchant(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"\s+-\s+cart[aã]o.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+cart[aã]o.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+no\s+.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+na\s+.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+em\s+\d{2}/\d{2}/\d{4}.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+-\s+.*$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()
