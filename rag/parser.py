# rag/parser.py
import re

def interpret_question(user_input: str) -> dict:
    """
    Detecta varias intenciones básicas:
      - get_total_year_by_proveedor: "¿Cuánto hemos gastado con [proveedor] en [2024]?"
      - get_total_year: "¿Cuánto nos hemos gastado en 2024?"
    Si no reconoce nada, fallback.
    """
    text = user_input.lower()

    # Regex para capturar un año (2024, 2023, etc.)
    year_pattern = r"(\d{4})"
    year_match = re.search(year_pattern, text)
    year = None
    if year_match:
        year = int(year_match.group(1))

    # Regex para "con <proveedor> en <año>"
    proveedor_pattern = r"con\s+([a-záéíóúñ\s\.]+)\s+en\s+\d{4}"
    prov_match = re.search(proveedor_pattern, text)
    proveedor = None
    if prov_match:
        proveedor = prov_match.group(1).strip()

    # Caso 1: get_total_year_by_proveedor
    if proveedor and year:
        return {
            "intent": "get_total_year_by_proveedor",
            "proveedor": proveedor,
            "year": year
        }

    # Caso 2: get_total_year (si mencionan gasto y un año)
    if ("gasto" in text or "gastado" in text) and year:
        return {
            "intent": "get_total_year",
            "year": year
        }

    # Fallback
    return {"intent": "fallback"}
