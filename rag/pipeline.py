import json
import pandas as pd
from supabase import Client
from datetime import datetime, timedelta
from .gpt import GPTFunctionCaller
from . import db_queries

def process_user_question(supabase_client, user_input: str, openai_api_key: str) -> str:
    gpt_caller = GPTFunctionCaller(api_key=openai_api_key)
    step1 = gpt_caller.call_step_1(user_input)
    choice = step1.choices[0]

    fn_call = choice.message.function_call  # Podría ser None
    if fn_call:
        fn_name = fn_call.name
        args_json = fn_call.arguments or "{}"
        try:
            fn_args = json.loads(args_json)
        except:
            fn_args = {}

        # Funciones existentes
        if fn_name == "facturas_importe_mayor":
            importe = fn_args.get("importe", 0)
            result_str = db_queries.facturas_importe_mayor(supabase_client, importe)
        elif fn_name == "proveedor_mas_contratos":
            result_str = db_queries.proveedor_mas_contratos(supabase_client)
        elif fn_name == "factura_mas_reciente":
            result_str = db_queries.factura_mas_reciente(supabase_client)
        elif fn_name == "gasto_en_rango_fechas":
            fi = fn_args.get("fecha_inicio", "")
            ff = fn_args.get("fecha_fin", "")
            result_str = db_queries.gasto_en_rango_fechas(supabase_client, fi, ff)
        elif fn_name == "contratos_vencen_antes_de":
            fecha = fn_args.get("fecha_limite", "")
            result_str = db_queries.contratos_vencen_antes_de(supabase_client, fecha)
        elif fn_name == "gasto_proveedor_en_year":
            proveedor = fn_args.get("proveedor", "")
            year = fn_args.get("year", 0)
            result_str = db_queries.gasto_proveedor_en_year(supabase_client, proveedor, year)
        elif fn_name == "facturas_mas_elevadas":
            top_n = fn_args.get("top_n", 5)
            result_str = db_queries.facturas_mas_elevadas(supabase_client, top_n)
        elif fn_name == "ranking_proveedores_por_importe":
            limit = fn_args.get("limit", 5)
            year = fn_args.get("year", None)
            result_str = db_queries.ranking_proveedores_por_importe(supabase_client, limit, year)        
        elif fn_name == "facturas_pendientes":
            result_str = db_queries.get_facturas_pendientes(supabase_client)
        elif fn_name == "gastos_por_mes_categoria":
            result_str = db_queries.get_gastos_por_mes_categoria(supabase_client).to_string()
        elif fn_name == "gastos_por_residencia":
            residencia = fn_args.get("residencia", "")
            result_str = db_queries.get_gastos_por_residencia(supabase_client, residencia)
        elif fn_name == "mantenimientos_pendientes":
            result_str = db_queries.get_mantenimientos_pendientes(supabase_client)
        elif fn_name == "proveedores_con_contratos_vigentes":
            result_str = db_queries.get_proveedores_con_contratos_vigentes(supabase_client).to_string()
        elif fn_name == "facturas_por_proveedor":
            proveedor = fn_args.get("proveedor", "")
            year = fn_args.get("year", 0)
            result_str = db_queries.get_facturas_por_proveedor(supabase_client, proveedor, year)
        elif fn_name == "contratos_vencen_proximos_meses":
            result_str = db_queries.get_contratos_vencen_proximos_meses(supabase_client)
        elif fn_name == "top_centros_mayores_gastos":
            year = fn_args.get("year", 0)
            result_str = db_queries.get_top_centros_mayores_gastos(supabase_client, year).to_string()
        else:
            result_str = f"No hay implementación local para la función '{fn_name}'."
        
        final = gpt_caller.call_step_2(fn_name, result_str)
        return final
    else:
        return choice.message.content.strip()