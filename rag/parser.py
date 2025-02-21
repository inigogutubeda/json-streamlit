# rag/parser.py
import re

def interpret_question(user_input: str) -> dict:
    """
    Detecta intenciones avanzadas:
     - ranking_gastos_centros: "¿En qué residencia gastamos más en 2024?"
     - max_factura_year: "Factura más alta en 2024"
     - (ejemplo) ranking_proveedores: "Ranking de proveedores más caros en Residencia 2"
     - resumen_residencia: "Dame un resumen de Residencia 1"
     - fallback: no reconoce
    """
    text = user_input.lower()

    # 1) Buscar año (4 dígitos)
    year_pattern = r"(\d{4})"
    match_year = re.search(year_pattern, text)
    year = int(match_year.group(1)) if match_year else None

    # 2) Buscar "residencia X" o "fundación x" con un regex sencillo
    # Ej.: "residencia 2" o "fundación x"
    centro_pattern = r"(residencia\s*\d+|fundaci[óo]n\s*x)"
    match_centro = re.search(centro_pattern, text)
    centro_str = match_centro.group(1) if match_centro else None

    # 3) Detección de keywords:
    if "ranking proveedores" in text or "proveedores más caros" in text:
        return {
            "intent": "ranking_proveedores",
            "centro": centro_str,
            "year": year
        }

    if "factura más alta" in text or "factura mas alta" in text:
        return {
            "intent": "max_factura_year",
            "year": year
        }

    if "resumen" in text and centro_str:
        return {
            "intent": "resumen_residencia",
            "centro": centro_str,
            "year": year
        }

    # "¿En qué residencia estamos gastando más en 2024?"
    if (("residencia" in text or "centro" in text) 
        and ("gastar" in text or "gastamos" in text)
        and ("más" in text or "mas" in text)):
        return {
            "intent": "ranking_gastos_centros",
            "year": year
        }

    # Mantén intenciones previas, ej. get_total_year
    if ("gasto" in text or "gastado" in text) and year:
        return {
            "intent": "get_total_year",
            "year": year
        }

    return {"intent": "fallback"}
