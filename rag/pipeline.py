import json
import pandas as pd
from supabase import Client
from datetime import datetime, timedelta
from .parser import interpret_question
from .gpt import GPTFunctionCaller
from . import db_queries

def process_user_question(supabase_client, user_input: str, openai_api_key: str) -> str:
    # Intentamos interpretar la intención del usuario con regex
    parsed_intent = interpret_question(user_input, openai_api_key)
    fn_name = parsed_intent.get("intent")

    if fn_name == "fallback":
        # Si no hay coincidencia en regex, llamamos a GPT
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

    # Ejecutamos la función correspondiente según la intención detectada
    if fn_name == "facturas_importe_mayor":
        importe = parsed_intent.get("importe", 0)
        result_str = db_queries.facturas_importe_mayor(supabase_client, importe)
    elif fn_name == "proveedor_mas_contratos":
        result_str = db_queries.proveedor_mas_contratos(supabase_client)
    elif fn_name == "factura_mas_reciente":
        result_str = db_queries.factura_mas_reciente(supabase_client)
    elif fn_name == "gasto_en_rango_fechas":
        fi = parsed_intent.get("fecha_inicio", "")
        ff = parsed_intent.get("fecha_fin", "")
        result_str = db_queries.gasto_en_rango_fechas(supabase_client, fi, ff)
    elif fn_name == "contratos_vencen_antes_de":
        fecha = parsed_intent.get("fecha_limite", "")
        result_str = db_queries.contratos_vencen_antes_de(supabase_client, fecha)
    elif fn_name == "gasto_proveedor_en_year":
        proveedor = parsed_intent.get("proveedor", "")
        year = parsed_intent.get("year", 0)
        result_str = db_queries.gasto_proveedor_en_year(supabase_client, proveedor, year)
    elif fn_name == "facturas_mas_elevadas":
        top_n = parsed_intent.get("top_n", 5)
        result_str = db_queries.facturas_mas_elevadas(supabase_client, top_n)
    elif fn_name == "ranking_proveedores_por_importe":
        limit = parsed_intent.get("limit", 5)
        year = parsed_intent.get("year", None)
        result_str = db_queries.ranking_proveedores_por_importe(supabase_client, limit, year)
    elif fn_name == "facturas_pendientes":
        result_str = db_queries.get_facturas_pendientes(supabase_client)
    elif fn_name == "gastos_por_mes_categoria":
        result_str = db_queries.get_gastos_por_mes_categoria(supabase_client).to_string()
    elif fn_name == "gastos_por_residencia":
        residencia = parsed_intent.get("residencia", "")
        result_str = db_queries.get_gastos_por_residencia(supabase_client, residencia)
    elif fn_name == "mantenimientos_pendientes":
        result_str = db_queries.get_mantenimientos_pendientes(supabase_client)
    elif fn_name == "proveedores_con_contratos_vigentes":
        result_str = db_queries.get_proveedores_con_contratos_vigentes(supabase_client).to_string()
    elif fn_name == "facturas_por_proveedor":
        proveedor = parsed_intent.get("proveedor", "")
        year = parsed_intent.get("year", 0)
        result_str = db_queries.get_facturas_por_proveedor(supabase_client, proveedor, year)
    elif fn_name == "contratos_vencen_proximos_meses":
        result_str = db_queries.get_contratos_vencen_proximos_meses(supabase_client)
    elif fn_name == "top_centros_mayores_gastos":
        year = parsed_intent.get("year", 0)
        result_str = db_queries.get_top_centros_mayores_gastos(supabase_client, year).to_string()
    else:
        result_str = f"No hay implementación local para la función '{fn_name}'."

    return result_str
