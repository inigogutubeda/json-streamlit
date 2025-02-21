# rag/pipeline.py

import json
from .gpt import GPTFunctionCaller
from . import db_queries

def process_user_question(supabase_client, user_input: str, openai_api_key: str) -> str:
    gpt_caller = GPTFunctionCaller(api_key=openai_api_key)
    response1 = gpt_caller.call_step_1(user_input)
    choice = response1.choices[0]

    # En la nueva API pydantic model: message.function_call
    fn_call = choice.message.function_call  # Podría ser None
    if fn_call:
        fn_name = fn_call.name
        fn_args_json = fn_call.arguments or "{}"
        try:
            fn_args = json.loads(fn_args_json)
        except:
            fn_args = {}

        # Ejecutamos la función local
        if fn_name == "facturas_importe_mayor":
            imp = fn_args.get("importe", 0)
            result_str = db_queries.facturas_importe_mayor(supabase_client, imp)

        elif fn_name == "proveedor_mas_contratos":
            result_str = db_queries.proveedor_mas_contratos(supabase_client)

        elif fn_name == "factura_mas_reciente":
            result_str = db_queries.factura_mas_reciente(supabase_client)

        elif fn_name == "gasto_en_rango_fechas":
            fi = fn_args.get("fecha_inicio","")
            ff = fn_args.get("fecha_fin","")
            result_str = db_queries.gasto_en_rango_fechas(supabase_client, fi, ff)

        elif fn_name == "contratos_vencen_antes_de":
            fl = fn_args.get("fecha_limite","")
            result_str = db_queries.contratos_vencen_antes_de(supabase_client, fl)

        else:
            result_str = f"No hay una función implementada localmente para '{fn_name}'."

        # 2ª llamada: GPT produce respuesta final
        final = gpt_caller.call_step_2(fn_name, result_str)
        return final
    else:
        # Sin function_call => GPT devolvió un texto normal
        return choice.message.content.strip()
