# rag/parser.py
import re

def interpret_question(user_input: str) -> dict:
    text = user_input.lower()

    # Regex para capturar año
    year_pattern = r"(\d{4})"
    year_match = re.search(year_pattern, text)
    year = None
    if year_match:
        year = int(year_match.group(1))

    # Regex / heurística para “con (American Tower) en 2024”
    proveedor_pattern = r"con\s+([a-záéíóúñ\s\.]+)\s+en\s+\d{4}"
    prov_match = re.search(proveedor_pattern, text)
    proveedor = None
    if prov_match:
        proveedor = prov_match.group(1).strip()

    # Caso: “get_total_year_by_proveedor”
    if proveedor and year:
        return {
            "intent": "get_total_year_by_proveedor",
            "proveedor": proveedor,
            "year": year
        }

    # Caso: “get_total_year”
    if ("gasto" in text or "hemos gastado" in text) and year:
        return {
            "intent": "get_total_year",
            "year": year
        }

    return {"intent": "fallback"}
