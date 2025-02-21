# rag/parser.py
import re
from datetime import datetime

def interpret_question(user_input: str) -> dict:
    """
    Detección de intenciones para mapear el texto del usuario a funciones locales.
    Nuevas keywords:
      - ranking_conceptos: "Ranking de conceptos" 
      - facturas_mas_elevadas: "Ver facturas top", "facturas más grandes"
      - gasto_proveedor_en_year: "¿Cuánto gastamos con ProveedorX en 2023?"
      - contratos_vencen_antes_de: "Contratos que vencen antes de 2024-05-01"
      - gasto_en_rango_fechas: "Gasto entre 2023-01-01 y 2023-12-31"
    """
    text = user_input.lower()

    # 1) Buscar año (4 dígitos)
    year_pattern = r"(\d{4})"
    match_year = re.search(year_pattern, text)
    year = int(match_year.group(1)) if match_year else None

    # 2) Buscar "residencia X" o "fundación x"
    centro_pattern = r"(residencia\s*\d+|fundaci[óo]n\s*x)"
    match_centro = re.search(centro_pattern, text)
    centro_str = match_centro.group(1) if match_centro else None

    # 3) Detección de posibles rangos de fecha con formato "AAAA-MM-DD"
    #    Ejemplo: "del 2023-01-01 al 2023-12-31"
    date_pattern = r"(\d{4}-\d{2}-\d{2})"
    fechas = re.findall(date_pattern, text)  # Puede devolver varias

    # 4) Palabras clave para intenciones
    if "ranking proveedores" in text or "proveedores más caros" in text:
        # Ejemplos: "Ranking proveedores en 2023" o "proveedores más caros"
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

    # Mantiene intenciones previas, ej. get_total_year
    if ("gasto" in text or "gastado" in text) and year:
        return {
            "intent": "get_total_year",
            "year": year
        }

    # NUEVAS DETECCIONES:
    # A) Ranking de conceptos totales
    if ("ranking" in text and "conceptos" in text) or ("top conceptos" in text):
        return {
            "intent": "ranking_conceptos"
        }

    # B) Top facturas
    if ("facturas" in text and ("más grandes" in text 
                                or "mas grandes" in text 
                                or "top" in text 
                                or "mayores" in text)):
        return {
            "intent": "facturas_mas_elevadas"
        }

    # C) Gasto de un proveedor en un year
    #    "¿Cuánto gastamos con 'ProveedorX' en 2023?"
    #    Buscamos un patrón "con PROVEEDOR en 2023", se asume 'proveedor' custom
    prov_pattern = r"con\s+([\w\s]+)\s+en\s+\d{4}"
    match_prov = re.search(prov_pattern, text)
    if match_prov and year:
        proveedor_str = match_prov.group(1).strip()
        return {
            "intent": "gasto_proveedor_en_year",
            "proveedor": proveedor_str,
            "year": year
        }

    # D) Contratos que vencen antes de X
    #    "contratos que vencen antes de 2024-05-01"
    if "contratos" in text and "vencen antes de" in text and len(fechas) > 0:
        # Tomamos la primera fecha encontrada
        fecha_limite = fechas[0]
        return {
            "intent": "contratos_vencen_antes_de",
            "fecha_limite": fecha_limite
        }

    # E) Gasto en rango de fechas
    #    "¿Cuánto gastamos entre 2023-01-01 y 2023-12-31?"
    if ("gasto" in text or "gastamos" in text or "coste" in text) and len(fechas) == 2:
        return {
            "intent": "gasto_en_rango_fechas",
            "fecha_inicio": fechas[0],
            "fecha_fin": fechas[1]
        }

    # F) Fallback
    return {"intent": "fallback"}
