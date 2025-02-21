# rag/pipeline.py

import json
from .gpt import GPTFunctionCaller
from . import db_queries

def process_user_question(supabase_client, user_input: str, openai_api_key: str) -> str:
    """
    - Crea un GPTFunctionCaller con la key
    - Step 1: GPT "function calling"
    - Step 2: si GPT llama a function, la ejecutamos localmente y 
      le pasamos el resultado en un 'role=function' => GPT produce la 
      respuesta final "conversacional"
    """
    gpt_caller = GPTFunctionCaller(api_key=openai_api_key)

    step1 = gpt_caller.call_step_1(user_input)
    choice = step1.choices[0]
    finish_reason = choice["finish_reason"]

    if finish_reason == "function_call":
        # GPT invoca una de nuestras functions
        fn_call = choice["message"]["function_call"]
        fn_name = fn_call["name"]
        fn_args_json = fn_call["arguments"]

        # Parseamos los argumentos
        try:
            fn_args = json.loads(fn_args_json)
        except:
            fn_args = {}

        # Llamar la función local
        result_str = ""
        if fn_name == "facturas_importe_mayor":
            importe = fn_args.get("importe",0)
            result_str = db_queries.facturas_importe_mayor(supabase_client, importe)

        elif fn_name == "proveedor_mas_contratos":
            result_str = db_queries.proveedor_mas_contratos(supabase_client)

        elif fn_name == "factura_mas_reciente":
            result_str = db_queries.factura_mas_reciente(supabase_client)

        elif fn_name == "gasto_en_rango_fechas":
            fi = fn_args.get("fecha_inicio","")
            ff = fn_args.get("fecha_fin","")
            result_str = db_queries.gasto_en_rango_fechas(supabase_client, fi, ff)

        elif fn_name == "contratos_vencen_antes_de":
            fecha_lim = fn_args.get("fecha_limite","")
            result_str = db_queries.contratos_vencen_antes_de(supabase_client, fecha_lim)

        else:
            # Function no reconocida
            result_str = f"Function '{fn_name}' no está implementada localmente."

        # Step 2: GPT produce la respuesta final
        final_msg = gpt_caller.call_step_2(fn_name, result_str)
        return final_msg
    else:
        # GPT no llamó a function => devuelvo el texto
        return choice["message"]["content"].strip()
