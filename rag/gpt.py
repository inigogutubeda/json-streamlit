# rag/gpt.py

from openai import OpenAI
import json

class GPTFunctionCaller:
    """
    Un objeto que define la 'client' y las 'functions' (para function calling),
    y hace el 2-step approach:
     1) GPT 'function_call' => (finish_reason='function_call')
     2) Llamamos a la función local => Llamada 'role=function'
     3) GPT produce la respuesta final
    """

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.functions_spec = [
            {
                "name": "facturas_importe_mayor",
                "description": "Filtra facturas con importe mayor que un valor dado",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "importe": {"type":"number"}
                    },
                    "required": ["importe"]
                }
            },
            {
                "name": "proveedor_mas_contratos",
                "description": "Devuelve ranking de proveedores por número de contratos",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "factura_mas_reciente",
                "description": "Encuentra la factura con fecha más reciente",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "gasto_en_rango_fechas",
                "description": "Calcula la suma de facturas entre fecha_inicio y fecha_fin (dd/mm/yyyy)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fecha_inicio": {"type":"string"},
                        "fecha_fin": {"type":"string"}
                    },
                    "required": ["fecha_inicio","fecha_fin"]
                }
            },
            {
                "name": "contratos_vencen_antes_de",
                "description": "Retorna los contratos que vencen antes de fecha_limite (dd/mm/yyyy)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fecha_limite": {"type":"string"}
                    },
                    "required":["fecha_limite"]
                }
            }
        ]

    def call_step_1(self, user_message: str):
        """
        1) Llamada inicial a GPT. GPT puede o no llamar a una function.
        """
        response = self.client.chat.completions.create(
            model="gpt-4o",  # o "gpt-3.5-turbo" si es tu preferencia
            messages=[{"role":"user","content":user_message}],
            functions=self.functions_spec,
            temperature=0
        )
        return response

    def call_step_2(self, function_name: str, function_result: str) -> str:
        """
        2) Llamada a GPT con un nuevo mensaje role="function", que contiene 
        el resultado de la ejecución local, para que GPT genere 
        la respuesta final “conversacional”.
        """
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content":"Aquí está la salida de la función python."},
                {"role":"assistant","name":function_name, "content":function_result}
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip()
