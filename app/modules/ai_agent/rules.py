from __future__ import annotations

import unicodedata
from dataclasses import dataclass


@dataclass
class CategoryRule:
    category: str
    subcategory: str
    keywords: list[str]


RULES: list[CategoryRule] = [
    CategoryRule(
        "Transporte", "Uber/99", ["uber", "99", "cabify", "in drive", "indrive"]
    ),
    CategoryRule(
        "Transporte",
        "Combustível",
        [
            "posto",
            "combustivel",
            "gasolina",
            "etanol",
            "shell",
            "petrobras",
            "ipiranga",
        ],
    ),
    CategoryRule(
        "Transporte",
        "Transporte Público",
        ["metro", "metrô", "trem", "onibus", "ônibus", "cptm", "bilhete"],
    ),
    CategoryRule(
        "Transporte",
        "Estacionamento",
        ["estacionamento", "valet", "parking", "zona azul"],
    ),
    CategoryRule(
        "Alimentação",
        "Restaurantes",
        ["restaurante", "bar", "lanchonete", "ifood", "i food", "rappi", "ubereats"],
    ),
    CategoryRule(
        "Alimentação",
        "Supermercado",
        [
            "mercado",
            "supermercado",
            "atacadao",
            "assai",
            "carrefour",
            "pao de acucar",
            "pão de açucar",
            "Zona Sul",
        ],
    ),
    CategoryRule(
        "Alimentação", "Padaria", ["padaria", "nema", "pao", "pão", "confeitaria"]
    ),
    CategoryRule("Moradia", "Aluguel", ["aluguel", "locacao", "locação"]),
    CategoryRule("Moradia", "Condomínio", ["condominio", "condomínio"]),
    CategoryRule("Moradia", "Água", ["agua", "água", "saneamento", "sabesp"]),
    CategoryRule("Moradia", "Luz", ["energia", "luz", "enel", "cpfl", "light"]),
    CategoryRule("Moradia", "Gás", ["gas", "gás", "ultragaz", "liquigas", "liquigás"]),
    CategoryRule(
        "Moradia",
        "Internet",
        ["internet", "banda larga", "fibra", "vivo", "claro", "tim"],
    ),
    CategoryRule(
        "Saúde", "Farmácia", ["farmacia", "farmácia", "drogaria", "droga", "drogasil"]
    ),
    CategoryRule("Saúde", "Consultas", ["consulta", "clinica", "clínica", "exame"]),
    CategoryRule(
        "Saúde",
        "Plano de Saúde",
        ["plano de saude", "plano de saúde", "amil", "bradesco saude"],
    ),
    CategoryRule("Saúde", "Academia", ["academia", "smart fit", "bluefit"]),
    CategoryRule("Educação", "Cursos", ["curso", "udemy", "alura", "rocketseat"]),
    CategoryRule(
        "Educação", "Livros", ["livraria", "livro", "amazon livros", "estante virtual"]
    ),
    CategoryRule("Educação", "Mensalidade", ["mensalidade", "escola", "faculdade"]),
    CategoryRule(
        "Lazer",
        "Streaming",
        ["netflix", "spotify", "amazon prime", "prime video", "disney", "hbo"],
    ),
    CategoryRule("Lazer", "Cinema", ["cinema", "cine", "ingresso"]),
    CategoryRule(
        "Lazer", "Viagens", ["hotel", "airbnb", "booking", "latam", "azul", "gol"]
    ),
    CategoryRule(
        "Compras", "Roupas", ["roupa", "moda", "renner", "cea", "c&a", "riachuelo"]
    ),
    CategoryRule(
        "Compras",
        "Eletrônicos",
        ["eletronico", "eletrônico", "magalu", "kabum", "mercado livre"],
    ),
    CategoryRule(
        "Compras",
        "Casa",
        ["casa", "leroy", "telha", "material de construcao", "construção"],
    ),
    CategoryRule("Compras", "Presentes", ["presente", "gift", "floricultura"]),
    CategoryRule(
        "Serviços",
        "Assinaturas",
        ["assinatura", "netflix", "spotify", "prime video", "icloud", "google one"],
    ),
    CategoryRule(
        "Serviços", "Telefone", ["telefonia", "celular", "vivo", "claro", "tim", "oi"]
    ),
    CategoryRule("Serviços", "Seguros", ["seguro", "apolice", "apólice"]),
    CategoryRule(
        "Investimentos",
        "Ações",
        ["corretora", "acoes", "ações", "home broker", "btg", "xp"],
    ),
    CategoryRule(
        "Investimentos", "Renda Fixa", ["cdb", "lci", "lca", "tesouro", "renda fixa"]
    ),
    CategoryRule(
        "Investimentos", "Crypto", ["bitcoin", "btc", "crypto", "ethereum", "binance"]
    ),
    CategoryRule("Investimentos", "Previdência", ["previdencia", "previdência"]),
    CategoryRule(
        "Outros",
        "Transferências",
        ["transferencia", "transferência", "pix", "ted", "doc"],
    ),
    CategoryRule("Outros", "Saques", ["saque", "caixa 24h"]),
    CategoryRule("Outros", "Taxas Bancárias", ["tarifa", "anuidade", "taxa", "juros"]),
]


def normalize(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()
