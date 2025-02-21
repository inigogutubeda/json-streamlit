# rag/gpt.py

import json
from openai import OpenAI

class GPTFunctionCaller:
    """
    Maneja function calling con openai>=1.0 (clase OpenAI).
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
                        "importe": {"type": "number"}
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
                        "fecha_inicio": {"type": "string"},
                        "fecha_fin": {"type": "string"}
                    },
                    "required": ["fecha_inicio","fecha_fin"]
                }
            },
            {
                "name": "contratos_vencen_antes_de",
                "description": "Retorna los contratos que vencen antes de una fecha (dd/mm/yyyy)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fecha_limite": {"type": "string"}
                    },
                    "required":["fecha_limite"]
                }
            }
        ]

    def call_step_1(self, user_message: str):
        """
        Llamada inicial a GPT, que puede decidir llamar a una function.
        """
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role":"user","content":user_message}],
            functions=self.functions_spec,
            temperature=0
        )
        return response

    def call_step_2(self, function_name: str, function_result: str) -> str:
        """
        Segunda llamada: pasamos el output de la función local
        para que GPT devuelva la respuesta final conversacional.
        """
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role":"system",
                    "content":"Output de la función Python. Devuelve una respuesta final al usuario."
                },
                {
                    "role":"assistant",
                    "name":function_name,
                    "content":function_result
                }
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip()
