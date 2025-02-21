# rag/gpt.py

from openai import OpenAI

class GPTFunctionCaller:
    """
    Maneja la creación del 'client' de openai>=1.0, define las 'functions'
    y realiza el '2-step approach' para function calling.
    """

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        # Definimos las funciones que GPT puede invocar
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
                        "fecha_inicio": {"type":"string"},
                        "fecha_fin": {"type":"string"}
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
                        "fecha_limite": {"type":"string"}
                    },
                    "required":["fecha_limite"]
                }
            }
        ]

    def call_step_1(self, user_message: str):
        """
        Primera llamada a GPT (con function calling).
        GPT puede devolver un function_call si cree que corresponde.
        """
        response = self.client.chat.completions.create(
            model="gpt-4",  # o gpt-4o si tu cuenta lo soporta
            messages=[{"role":"user","content":user_message}],
            functions=self.functions_spec,
            temperature=0
        )
        return response

    def call_step_2(self, function_name: str, function_result: str) -> str:
        """
        Segunda llamada a GPT: 
        - le pasamos un mensaje role="assistant", name=function_name, content=function_result
        - GPT genera la respuesta final
        """
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role":"system",
                    "content":"Esto es el resultado de la función python. Devuelve una respuesta final para el usuario."
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
