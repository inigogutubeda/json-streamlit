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
    
    # 📌 Detección de Año
    year_pattern = r"(\d{4})"
    match_year = re.search(year_pattern, text)
    year = int(match_year.group(1)) if match_year else None

    # 📌 Detección de Residencia
    centro_pattern = r"(residencia\s*\d+|fundaci[óo]n\s*x)"
    match_centro = re.search(centro_pattern, text)
    centro_str = match_centro.group(1) if match_centro else None

    # 📌 Detección de Fechas
    date_pattern = r"(\d{4}-\d{2}-\d{2})"
    fechas = re.findall(date_pattern, text)

    # 📌 Detección de Proveedor
    prov_pattern = r"con\s+([\w\s]+)\s+en\s+\d{4}"
    match_prov = re.search(prov_pattern, text)
    proveedor_str = match_prov.group(1).strip() if match_prov else None

    # 📌 Detección de Servicios
    servicio_pattern = r"gasto en\s+([\w\s]+)"
    match_servicio = re.search(servicio_pattern, text)
    servicio_str = match_servicio.group(1).strip() if match_servicio else None

    # 📌 Mapeo de Intenciones
    intent_mapping = {
        "get_contratos": ["muéstrame los contratos", "lista de contratos"],
        "get_facturas": ["muéstrame las facturas", "todas las facturas registradas"],
        "facturas_importe_mayor": ["facturas mayores a", "facturas superiores a"],
        "proveedor_mas_contratos": ["proveedor con más contratos", "proveedor con más acuerdos"],
        "factura_mas_reciente": ["factura más reciente", "última factura"],
        "gasto_en_rango_fechas": ["gasto entre", "coste entre"],
        "contratos_vencen_antes_de": ["contratos vencen antes de"],
        "gasto_proveedor_en_year": ["cuánto gastamos con", "gasto con proveedor"],
        "facturas_mas_elevadas": ["facturas más grandes", "facturas más costosas"],
        "ranking_proveedores_por_importe": ["ranking proveedores", "proveedores con mayor gasto"],
        "get_facturas_pendientes": ["facturas pendientes", "qué debo pagar"],
        "get_gastos_por_mes_categoria": ["gastos por mes", "resumen de gastos"],
        "get_gastos_por_residencia": ["gasto por residencia", "cuánto gastó"],
        "get_mantenimientos_pendientes": ["mantenimientos programados", "mantenimiento próximo"],
        "get_proveedores_con_contratos_vigentes": ["proveedores con contrato activo"],
        "get_contratos_vencen_proximos_meses": ["contratos vencen en los próximos meses"],
        "get_top_centros_mayores_gastos": ["residencias con más gasto", "ranking de gastos por centro"],
        "contrato_mas_costoso": ["contrato más caro", "acuerdo más costoso"],
        "facturas_de_proveedor": ["facturas de", "facturas emitidas por"],
        "gasto_por_tipo_servicio": ["cuánto gastamos en", "gasto total en"],
        "ranking_tipos_servicios": ["ranking de servicios", "servicios con mayor coste"],
        "top_contratos_mas_costosos": ["contratos más costosos", "top contratos caros"]
    }

    for intent, keywords in intent_mapping.items():
        if any(keyword in text for keyword in keywords):
            return {
                "intent": intent,
                "year": year,
                "centro": centro_str,
                "proveedor": proveedor_str,
                "tipo_servicio": servicio_str
            }

    # 📌 Si no se encuentra una coincidencia, usamos GPT para interpretar
    gpt_caller = GPTFunctionCaller(api_key)
    response = gpt_caller.call_step_1(user_input)
    choice = response.choices[0]
    fn_call = choice.message.function_call

    if fn_call:
        return {"intent": fn_call.name, **json.loads(fn_call.arguments or "{}")}

    return {"intent": "fallback"}
