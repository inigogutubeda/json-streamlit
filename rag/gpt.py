# gpt.py
from openai import OpenAI
import os

class GPTFunctionCaller:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def call_step_1(self, question):
        """Primera llamada a OpenAI para determinar si requiere una función."""
        return self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente financiero experto en gestión de contratos y facturas."},
                {"role": "user", "content": question}
            ],
            functions=[
                {"name": "query_database", "parameters": {"question": question}}
            ]
        )

    def call_step_2(self, function_name, data):
        """Segunda llamada para generar la respuesta final basada en datos."""
        return self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente financiero que analiza datos."},
                {"role": "user", "content": f"La función {function_name} devolvió: {data}"},
            ]
        ).choices[0].message["content"]
