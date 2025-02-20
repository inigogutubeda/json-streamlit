# rag/parser.py
import re

def interpret_question(user_input: str) -> dict:
    """
    Detecta la 'intención' principal y extrae parámetros (por ejemplo, año).
    En un proyecto real, se puede hacer algo más sofisticado 
    (embeddings, LLM, etc.),
    pero aquí hacemos un 'regex pipeline' de demostración.
    """
    # Como ejemplo, buscaremos 2 intenciones:
    # 1) "get_total_year" -> "Qué nos hemos gastado en 2024"
    # 2) "count_invoices_year" -> "Cuántas facturas hay en 2024"
    # Y si no matchea, fallback.

    # Regex para capturar un año
    pattern_year = r"(?:en\s+facturas\s+en\s+(\d{4}))|(?:en\s+(\d{4}))|(\d{4})"
    match = re.search(pattern_year, user_input)
    year = None
    if match:
        for g in match.groups():
            if g and g.isdigit():
                year = int(g)
                break

    # Buscamos palabras clave "cuántas facturas" -> “count_invoices_year”
    if "cuántas facturas" in user_input.lower() and year:
        return {
            "intent": "count_invoices_year",
            "year": year
        }

    # Buscamos "gasto en" / "nos hemos gastado en" / etc. -> “get_total_year”
    if ("gasto" in user_input.lower() or "hemos gastado" in user_input.lower()) and year:
        return {
            "intent": "get_total_year",
            "year": year
        }

    # Podrías añadir más patrones, e.g. “contratos vencidos”, “factura con ID X”, etc.

    return {
        "intent": "fallback"
    }
