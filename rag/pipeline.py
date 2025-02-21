# rag/pipeline.py

import json
from .gpt import GPTFunctionCaller
from . import db_queries

def process_user_question(supabase_client, user_input: str, openai_api_key: str) -> str:
    gpt_caller = GPTFunctionCaller(api_key=openai_api_key)
    response1 = gpt_caller.call_step_1(user_input)
    choice = response1.choices[0]

    # Validar si OpenAI ha solicitado una función
    fn_call = getattr(choice.message, "function_call", None)
    if fn_call:
        fn_name = fn_call.name
        fn_args_json = fn_call.arguments or "{}"
        try:
            fn_args = json.loads(fn_args_json)
        except:
            fn_args = {}

        # Mapeo de funciones disponibles
        function_map = {
            "facturas_importe_mayor": db_queries.facturas_importe_mayor,
            "proveedor_mas_contratos": db_queries.proveedor_mas_contratos,
            "factura_mas_reciente": db_queries.factura_mas_reciente,
            "gasto_en_rango_fechas": db_queries.gasto_en_rango_fechas,
            "contratos_vencen_antes_de": db_queries.contratos_vencen_antes_de,
            "gasto_proveedor_en_year": db_queries.gasto_proveedor_en_year,
            "facturas_mas_elevadas": db_queries.facturas_mas_elevadas,
            "ranking_proveedores_por_importe": db_queries.ranking_proveedores_por_importe,
            "top_residencias_por_gasto": db_queries.top_residencias_por_gasto,
            "analisis_gastos_mensuales": db_queries.analisis_gastos_mensuales,
            "analisis_facturas_pendientes": db_queries.analisis_facturas_pendientes,
            "proveedor_con_mayor_gasto": db_queries.proveedor_con_mayor_gasto
        }

        if fn_name in function_map:
            result_str = function_map[fn_name](supabase_client, **fn_args)
        else:
            result_str = f"No hay una función implementada localmente para '{fn_name}'."

        # Segunda llamada a GPT para generar respuesta final
        final = gpt_caller.call_step_2(fn_name, result_str)
        return final
    
    # Si no hay función, simplemente devolver el texto del modelo
    return choice.message.content.strip()
