# rag/pipeline.py

import json
from .gpt import call_gpt_function_call
from . import db_queries

def process_user_question(supabase_client, user_input: str, openai_api_key: str) -> str:
    """
    1) Llama a GPT con function calling para ver si GPT llama a una de nuestras funciones.
    2) Si GPT llama a 'facturas_importe_mayor' con {"importe":1000}, 
       ejecutamos db_queries.facturas_importe_mayor(1000).
    3) Devolvemos la respuesta final.
    """
    # Realizamos la llamada a GPT
    response = call_gpt_function_call(user_input)
    choice = response.choices[0]
    
    if choice.finish_reason == "function_call":
        # GPT quiere llamar a una función
        function_call = choice.message.function_call
        function_name = function_call.name
        arguments_json = function_call.arguments
        try:
            args = json.loads(arguments_json)
        except:
            return "No pude parsear los argumentos."

        # Mapeamos function_name -> función Python real
        if function_name == "facturas_importe_mayor":
            importe = args.get("importe", 0)
            return db_queries.facturas_importe_mayor(supabase_client, importe)

        elif function_name == "proveedor_mas_contratos":
            return db_queries.proveedor_mas_contratos(supabase_client)

        elif function_name == "factura_mas_reciente":
            return db_queries.factura_mas_reciente(supabase_client)

        elif function_name == "gasto_en_rango_fechas":
            fi = args.get("fecha_inicio", "")
            ff = args.get("fecha_fin", "")
            return db_queries.gasto_en_rango_fechas(supabase_client, fi, ff)

        elif function_name == "contratos_vencen_antes_de":
            fecha_limite = args.get("fecha_limite","")
            return db_queries.contratos_vencen_antes_de(supabase_client, fecha_limite)

        else:
            return "Función no reconocida por la lógica local."

    else:
        # GPT no llamó a una función. 
        # Ej: GPT dio una respuesta textual. 
        # Para una POC, podemos simplemente devolver choice.message.content
        return choice.message.content.strip()
