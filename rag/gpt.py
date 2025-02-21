# rag/gpt.py

import json
import openai
from openai import OpenAI

def create_gpt_client(api_key: str) -> OpenAI:
    openai.api_key = api_key
    return OpenAI(api_key=api_key)

# Definimos la "especificación" de funciones que GPT puede llamar
FUNCTIONS_SPEC = [
    {
        "name": "facturas_importe_mayor",
        "description": "Filtra facturas con importe mayor que un valor dado y retorna un resumen",
        "parameters": {
            "type": "object",
            "properties": {
                "importe": {
                    "type": "number",
                    "description": "Importe mínimo para filtrar las facturas"
                }
            },
            "required": ["importe"]
        }
    },
    {
        "name": "proveedor_mas_contratos",
        "description": "Devuelve qué proveedor tiene el mayor número de contratos y un ranking",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "factura_mas_reciente",
        "description": "Busca la factura con la fecha_factura más reciente",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "gasto_en_rango_fechas",
        "description": "Calcula el gasto total entre dos fechas (dd/mm/yyyy)",
        "parameters": {
            "type": "object",
            "properties": {
                "fecha_inicio": { "type": "string" },
                "fecha_fin": { "type": "string" }
            },
            "required": ["fecha_inicio","fecha_fin"]
        }
    },
    {
        "name": "contratos_vencen_antes_de",
        "description": "Retorna cuántos contratos vencen antes de una fecha y la lista",
        "parameters": {
            "type": "object",
            "properties": {
                "fecha_limite": { "type": "string" }
            },
            "required": ["fecha_limite"]
        }
    }
]

def call_gpt_function_call(user_message: str):
    """
    Envía 'user_message' a GPT con la opción de function calling. 
    Retorna la respuesta. 
    Si GPT llama a una de las funciones definidas, interpretamos la function_call.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",  # un modelo con soporte function calling
        messages=[{"role": "user", "content": user_message}],
        functions=FUNCTIONS_SPEC,
        # "function_call"="auto" es implícito, GPT decidirá si llama o no
        temperature=0
    )
    return response

