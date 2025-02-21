# rag/pipeline.py
import json
from .gpt import GPTFunctionCaller
from . import db_queries

def process_user_question(supabase_client, user_input: str, openai_api_key: str) -> str:
    gpt_caller = GPTFunctionCaller(api_key=openai_api_key)
    step1_resp = gpt_caller.call_step_1(user_input)
    choice = step1_resp.choices[0]

    # En la nueva API, check if there's a function_call
    fn_call = choice.message.get("function_call", None)
    if fn_call:
        # GPT quiere llamar a una function
        fn_name = fn_call["name"]
        fn_args_str = fn_call.get("arguments","{}")
        try:
            fn_args = json.loads(fn_args_str)
        except:
            fn_args = {}

        # Llamamos a la función local
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
            result_str = f"Function '{fn_name}' no está implementada localmente."

        # Llamamos step 2 => GPT produce la respuesta final
        final_answer = gpt_caller.call_step_2(fn_name, result_str)
        return final_answer
    else:
        # GPT no llamó a ninguna función. Devolvemos su texto normal
        return choice.message["content"].strip()
