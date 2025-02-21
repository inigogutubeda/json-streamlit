import json
import pandas as pd
from supabase import Client
from datetime import datetime, timedelta
from .parser import interpret_question
from .gpt import GPTFunctionCaller
from . import db_queries

def process_user_question(supabase_client, user_input: str, openai_api_key: str) -> str:
    """
    Procesa la pregunta del usuario, detectando la intención y llamando la función correspondiente.
    """
    # Intentamos interpretar la intención del usuario con regex
    parsed_intent = interpret_question(user_input, openai_api_key)
    fn_name = parsed_intent.get("intent")

    # Si no se detectó una intención válida, intentamos con GPT
    if fn_name == "fallback":
        gpt_caller = GPTFunctionCaller(api_key=openai_api_key)
        step1 = gpt_caller.call_step_1(user_input)
        choice = step1.choices[0]
        fn_call = choice.message.function_call

        if fn_call:
            fn_name = fn_call.name
            args_json = fn_call.arguments or "{}"
            try:
                parsed_intent.update(json.loads(args_json))
            except:
                pass

    # Mapeo de funciones disponibles
    function_mapping = {
        "facturas_importe_mayor": lambda: db_queries.facturas_importe_mayor(supabase_client, parsed_intent.get("importe", 0)),
        "proveedor_mas_contratos": lambda: db_queries.proveedor_mas_contratos(supabase_client),
        "factura_mas_reciente": lambda: db_queries.factura_mas_reciente(supabase_client),
        "gasto_en_rango_fechas": lambda: db_queries.gasto_en_rango_fechas(supabase_client, parsed_intent.get("fecha_inicio", ""), parsed_intent.get("fecha_fin", "")),
        "contratos_vencen_antes_de": lambda: db_queries.contratos_vencen_antes_de(supabase_client, parsed_intent.get("fecha_limite", "")),
        "gasto_proveedor_en_year": lambda: db_queries.gasto_proveedor_en_year(supabase_client, parsed_intent.get("proveedor", ""), parsed_intent.get("year", 0)),
        "facturas_mas_elevadas": lambda: db_queries.facturas_mas_elevadas(supabase_client, parsed_intent.get("top_n", 5)),
        "ranking_proveedores_por_importe": lambda: db_queries.ranking_proveedores_por_importe(supabase_client, parsed_intent.get("limit", 5), parsed_intent.get("year", None)),
        "facturas_pendientes": lambda: db_queries.get_facturas_pendientes(supabase_client),
        "gastos_por_mes_categoria": lambda: db_queries.get_gastos_por_mes_categoria(supabase_client).to_string(),
        "gastos_por_residencia": lambda: db_queries.get_gastos_por_residencia(supabase_client, parsed_intent.get("residencia", "")),
        "mantenimientos_pendientes": lambda: db_queries.get_mantenimientos_pendientes(supabase_client),
        "proveedores_con_contratos_vigentes": lambda: db_queries.get_proveedores_con_contratos_vigentes(supabase_client).to_string(),
        "facturas_por_proveedor": lambda: db_queries.get_facturas_por_proveedor(supabase_client, parsed_intent.get("proveedor", ""), parsed_intent.get("year", 0)),
        "contratos_vencen_proximos_meses": lambda: db_queries.get_contratos_vencen_proximos_meses(supabase_client),
        "top_centros_mayores_gastos": lambda: db_queries.get_top_centros_mayores_gastos(supabase_client, parsed_intent.get("year", 0)).to_string(),
        "ranking_gastos_centros": lambda: db_queries.get_top_centros_mayores_gastos(supabase_client, parsed_intent.get("year", 0)).to_string(),
        "get_total_year": lambda: db_queries.gasto_en_rango_fechas(supabase_client, f"01/01/{parsed_intent.get('year', 0)}", f"31/12/{parsed_intent.get('year', 0)}"),
        "contrato_mas_costoso": lambda: db_queries.contrato_mas_costoso(supabase_client),
        "facturas_de_proveedor": lambda: db_queries.facturas_de_proveedor(supabase_client, parsed_intent.get("proveedor", ""), parsed_intent.get("year", 0)),
        "gasto_por_tipo_servicio": lambda: db_queries.gasto_por_tipo_servicio(supabase_client, parsed_intent.get("tipo_servicio", "")),
        "ranking_tipos_servicios": lambda: db_queries.ranking_tipos_servicios(supabase_client),
        "top_contratos_mas_costosos": lambda: db_queries.top_contratos_mas_costosos(supabase_client),
    }

    # Ejecutamos la función correspondiente si está en el mapeo
    result_str = function_mapping.get(fn_name, lambda: "Lo siento, no entendí tu pregunta. Intenta reformularla o pregunta sobre facturas, contratos o gastos.")()

    return result_str
