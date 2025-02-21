# rag/parser.py

import re

def interpret_question(user_input: str) -> dict:
    """
    Detecta múltiples intenciones, incluidas las nuevas:
      - facturas_importe_mayor
      - proveedor_mas_contratos
      - factura_mas_reciente
      - gasto_en_rango
      - contratos_vencen_antes
    Además de las previas (ranking_gastos_centros, max_factura_year, etc.).
    """
    text = user_input.lower()

    # 1) Buscar año (4 dígitos) genérico
    year_pattern = r"(\d{4})"
    match_year = re.search(year_pattern, text)
    year = int(match_year.group(1)) if match_year else None

    # 2) Buscar "residencia X" o "fundación x" (as en las lógicas previas)
    centro_pattern = r"(residencia\s*\d+|fundaci[óo]n\s*x)"
    match_centro = re.search(centro_pattern, text)
    centro_str = match_centro.group(1) if match_centro else None

    # 3) Buscar intervalos de fecha dd/mm/yyyy o dd-mm-yyyy
    #    Ej.: "del 01/01/2024 al 31/01/2024"
    rango_pattern = r"(del|entre)\s+(\d{2}[\-/]\d{2}[\-/]\d{4})\s+(al|hasta)\s+(\d{2}[\-/]\d{2}[\-/]\d{4})"
    rango_match = re.search(rango_pattern, text)
    date1, date2 = None, None
    if rango_match:
        date1 = rango_match.group(2)
        date2 = rango_match.group(4)

    # 4) Buscar un importe (p.ej. “importe mayor a 1000”)
    importe_pattern = r"mayor a\s+(\d+)"
    match_importe = re.search(importe_pattern, text)
    importe_val = None
    if match_importe:
        importe_val = float(match_importe.group(1))

    # 5) Buscar fecha genérica para "vencen antes de"
    #    Ej.: "vencen antes de 31/12/2025"
    vence_pattern = r"(vencen\s+antes\s+de\s+(\d{2}[\-/]\d{2}[\-/]\d{4}))"
    match_vence = re.search(vence_pattern, text)
    vence_fecha = None
    if match_vence:
        # Extraer la parte (\d{2}/\d{2}/\d{4})
        re_f = re.search(r"(\d{2}[\-/]\d{2}[\-/]\d{4})", match_vence.group(0))
        if re_f:
            vence_fecha = re_f.group(1)

    # Detectar frase “facturas con importe mayor a …”
    if "facturas" in text and "importe" in text and "mayor" in text and importe_val:
        return {
            "intent": "facturas_importe_mayor",
            "importe": importe_val
        }

    # "qué proveedor tiene más contratos"
    if "qué proveedor" in text and ("más contratos" in text or "mas contratos" in text):
        return {
            "intent": "proveedor_mas_contratos"
        }

    # "Cuál es la factura más reciente" o "factura con fecha más reciente"
    if "factura" in text and ("más reciente" in text or "mas reciente" in text):
        return {
            "intent": "factura_mas_reciente"
        }

    # "gasto total en rango"
    if ("gasto" in text or "gastado" in text) and date1 and date2:
        return {
            "intent": "gasto_en_rango",
            "fecha_inicio": date1,
            "fecha_fin": date2
        }

    # "cuántos contratos vencen antes de dd/mm/yyyy"
    if ("contratos" in text and "vencen antes de" in text) and vence_fecha:
        return {
            "intent": "contratos_vencen_antes",
            "fecha_vencimiento": vence_fecha
        }

    # Mantener las previas (ranking_gastos_centros, max_factura_year, etc.)
    # Ranking gasto por centro
    if (("residencia" in text or "centro" in text) 
        and ("gastar" in text or "gastamos" in text)
        and ("más" in text or "mas" in text)):
        return {
            "intent": "ranking_gastos_centros",
            "year": year
        }

    # Factura más alta en un año
    if "factura más alta" in text or "factura mas alta" in text:
        return {
            "intent": "max_factura_year",
            "year": year
        }

    # Ranking proveedores
    if "ranking proveedores" in text or "proveedores más caros" in text:
        return {
            "intent": "ranking_proveedores",
            "centro": centro_str,
            "year": year
        }

    # Resumen residencia
    if "resumen" in text and centro_str:
        return {
            "intent": "resumen_residencia",
            "centro": centro_str,
            "year": year
        }

    # get_total_year
    if ("gasto" in text or "gastado" in text) and year:
        return {
            "intent": "get_total_year",
            "year": year
        }

    return {"intent": "fallback"}
