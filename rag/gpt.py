# rag/gpt.py

from openai import OpenAI

class GPTFunctionCaller:
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
                    "type":"object",
                    "properties": {}
                }
            },
            {
                "name": "factura_mas_reciente",
                "description": "Encuentra la factura con fecha más reciente",
                "parameters": {
                    "type":"object",
                    "properties": {}
                }
            },
            {
                "name": "gasto_en_rango_fechas",
                "description": "Calcula la suma de facturas entre fecha_inicio y fecha_fin (dd/mm/yyyy)",
                "parameters": {
                    "type":"object",
                    "properties":{
                        "fecha_inicio":{"type":"string"},
                        "fecha_fin":{"type":"string"}
                    },
                    "required":["fecha_inicio","fecha_fin"]
                }
            },
            {
                "name": "contratos_vencen_antes_de",
                "description": "Retorna los contratos que vencen antes de una fecha (dd/mm/yyyy)",
                "parameters": {
                    "type":"object",
                    "properties":{
                        "fecha_limite":{"type":"string"}
                    },
                    "required":["fecha_limite"]
                }
            },
            #######################################################
            # NUEVAS
            #######################################################
            {
                "name": "gasto_proveedor_en_year",
                "description": "Suma total de facturas de un proveedor en un año",
                "parameters": {
                    "type":"object",
                    "properties":{
                        "proveedor":{"type":"string"},
                        "year":{"type":"number"}
                    },
                    "required":["proveedor","year"]
                }
            },
            {
                "name": "facturas_mas_elevadas",
                "description": "Retorna las facturas con mayor 'total' (por defecto top_n=5)",
                "parameters": {
                    "type":"object",
                    "properties":{
                        "top_n":{"type":"number"}
                    },
                    "required":[]
                }
            },
            {
                "name": "ranking_proveedores_por_importe",
                "description": "Ranking de proveedores por importe total de sus facturas. Se puede filtrar por año.",
                "parameters": {
                    "type":"object",
                    "properties":{
                        "limit":{"type":"number","description":"cuantos proveedores mostrar"},
                        "year":{"type":"number","description":"(opcional) filtrar facturas por este año"}
                    },
                    "required":[]  # none strictly required
                }
            }
        ]

    def call_step_1(self, user_message: str):
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role":"user","content":user_message}],
            functions=self.functions_spec,
            temperature=0
        )
        return response

    def call_step_2(self, function_name: str, function_result: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role":"system",
                    "content":"Este es el resultado de la función local. Devuélvelo de forma clara al usuario."
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
