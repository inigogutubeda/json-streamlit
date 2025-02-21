import re
import json
from datetime import datetime
from openai import OpenAI
from .gpt import GPTFunctionCaller

def interpret_question(user_input: str, api_key: str) -> dict:
    """
    Detección de intenciones combinando regex y GPT.
    """
    text = user_input.lower()
    year_pattern = r"(\d{4})"
    match_year = re.search(year_pattern, text)
    year = int(match_year.group(1)) if match_year else None

    centro_pattern = r"(residencia\s*\d+|fundaci[óo]n\s*x)"
    match_centro = re.search(centro_pattern, text)
    centro_str = match_centro.group(1) if match_centro else None

    date_pattern = r"(\d{4}-\d{2}-\d{2})"
    fechas = re.findall(date_pattern, text)

    prov_pattern = r"con\s+([\w\s]+)\s+en\s+\d{4}"
    match_prov = re.search(prov_pattern, text)
    proveedor_str = match_prov.group(1).strip() if match_prov else None

    if "ranking proveedores" in text or "proveedores mas caros" in text:
        return {"intent": "ranking_proveedores", "centro": centro_str, "year": year}
    if "factura más alta" in text or "factura mas alta" in text:
        return {"intent": "max_factura_year", "year": year}
    if "resumen" in text and centro_str:
        return {"intent": "resumen_residencia", "centro": centro_str, "year": year}
    if ("residencia" in text or "centro" in text) and ("gastar" in text or "gastamos" in text) and ("más" in text or "mas" in text):
        return {"intent": "ranking_gastos_centros", "year": year}
    if ("gasto" in text or "gastado" in text) and year:
        return {"intent": "get_total_year", "year": year}
    if ("ranking" in text and "conceptos" in text) or ("top conceptos" in text):
        return {"intent": "ranking_conceptos"}
    if "facturas" in text and ("más grandes" in text or "mas grandes" in text or "top" in text or "mayores" in text):
        return {"intent": "facturas_mas_elevadas"}
    if match_prov and year:
        return {"intent": "gasto_proveedor_en_year", "proveedor": proveedor_str, "year": year}
    if "contratos" in text and "vencen antes de" in text and len(fechas) > 0:
        return {"intent": "contratos_vencen_antes_de", "fecha_limite": fechas[0]}
    if ("gasto" in text or "gastamos" in text or "coste" in text) and len(fechas) == 2:
        return {"intent": "gasto_en_rango_fechas", "fecha_inicio": fechas[0], "fecha_fin": fechas[1]}
    if "facturas pendientes" in text or "qué debo pagar" in text:
        return {"intent": "facturas_pendientes"}
    if "mantenimiento programado" in text or "mantenimientos próximos" in text:
        return {"intent": "mantenimientos_pendientes"}
    if "contratos vencen en" in text or "próximos contratos vencen" in text:
        return {"intent": "contratos_vencen_proximos_meses"}
    if "gasto por residencia" in text or "cuánto ha gastado" in text:
        return {"intent": "gastos_por_residencia", "centro": centro_str}
    if "proveedores con contrato vigente" in text or "lista de proveedores activos" in text:
        return {"intent": "proveedores_con_contratos_vigentes"}
    if "centros con más gastos" in text or "mayores gastos en centros" in text:
        return {"intent": "top_centros_mayores_gastos", "year": year}
    
    # Si no encontramos coincidencias, usamos GPT para interpretar
    gpt_caller = GPTFunctionCaller(api_key)
    response = gpt_caller.call_step_1(user_input)
    choice = response.choices[0]
    fn_call = choice.message.function_call
    if fn_call:
        return {"intent": fn_call.name, **json.loads(fn_call.arguments or "{}")}
    return {"intent": "fallback"}
