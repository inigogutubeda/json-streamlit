from openai import OpenAI

class GPTFunctionCaller:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.functions_spec = [
            # Consultas generales
            {"name": "get_contratos", "description": "Obtiene todos los contratos registrados.", "parameters": {"type": "object", "properties": {}}},
            {"name": "get_facturas", "description": "Obtiene todas las facturas registradas.", "parameters": {"type": "object", "properties": {}}},
            {"name": "facturas_importe_mayor", "description": "Filtra facturas con importe mayor que un valor dado.", "parameters": {"type": "object", "properties": {"importe": {"type": "number"}}, "required": ["importe"]}},
            {"name": "proveedor_mas_contratos", "description": "Devuelve el proveedor con más contratos activos.", "parameters": {"type": "object", "properties": {}}},
            {"name": "factura_mas_reciente", "description": "Encuentra la factura más reciente registrada.", "parameters": {"type": "object", "properties": {}}},
            {"name": "gasto_en_rango_fechas", "description": "Suma de facturas en un rango de fechas.", "parameters": {"type": "object", "properties": {"fecha_inicio": {"type": "string"}, "fecha_fin": {"type": "string"}}, "required": ["fecha_inicio", "fecha_fin"]}},
            {"name": "contratos_vencen_antes_de", "description": "Lista de contratos que vencen antes de una fecha.", "parameters": {"type": "object", "properties": {"fecha_limite": {"type": "string"}}, "required": ["fecha_limite"]}},
            {"name": "gasto_proveedor_en_year", "description": "Suma total de facturas de un proveedor en un año específico.", "parameters": {"type": "object", "properties": {"proveedor": {"type": "string"}, "year": {"type": "number"}}, "required": ["proveedor", "year"]}},
            {"name": "facturas_mas_elevadas", "description": "Lista de las facturas más elevadas.", "parameters": {"type": "object", "properties": {"top_n": {"type": "number"}}, "required": []}},
            {"name": "ranking_proveedores_por_importe", "description": "Ranking de proveedores según su facturación.", "parameters": {"type": "object", "properties": {"limit": {"type": "number"}, "year": {"type": "number"}}, "required": []}},

            # Facturación y gastos
            {"name": "get_facturas_pendientes", "description": "Devuelve una lista de facturas pendientes de pago.", "parameters": {"type": "object", "properties": {}}},
            {"name": "get_facturas_por_proveedor", "description": "Obtiene todas las facturas de un proveedor en un año determinado.", "parameters": {"type": "object", "properties": {"proveedor": {"type": "string"}, "year": {"type": "number"}}, "required": ["proveedor", "year"]}},
            {"name": "get_gastos_por_mes_categoria", "description": "Devuelve los gastos agrupados por mes y categoría.", "parameters": {"type": "object", "properties": {}}},
            {"name": "get_gastos_por_residencia", "description": "Devuelve los gastos totales por residencia.", "parameters": {"type": "object", "properties": {"residencia": {"type": "string"}}, "required": ["residencia"]}},

            # Contratos y mantenimientos
            {"name": "get_mantenimientos_pendientes", "description": "Lista de mantenimientos pendientes en las residencias.", "parameters": {"type": "object", "properties": {}}},
            {"name": "get_proveedores_con_contratos_vigentes", "description": "Lista de proveedores con contratos activos.", "parameters": {"type": "object", "properties": {}}},
            {"name": "get_contratos_vencen_proximos_meses", "description": "Lista de contratos que vencen en los próximos meses.", "parameters": {"type": "object", "properties": {}}},
            {"name": "get_top_centros_mayores_gastos", "description": "Ranking de centros con los mayores gastos en un año específico.", "parameters": {"type": "object", "properties": {"year": {"type": "number"}}, "required": ["year"]}},

            # Consultas avanzadas
            {"name": "contrato_mas_costoso", "description": "Devuelve el contrato con el importe más alto.", "parameters": {"type": "object", "properties": {}}},
            {"name": "facturas_de_proveedor", "description": "Lista de facturas de un proveedor en un año.", "parameters": {"type": "object", "properties": {"proveedor": {"type": "string"}, "year": {"type": "number"}}, "required": ["proveedor", "year"]}},
            {"name": "gasto_por_tipo_servicio", "description": "Gasto total en un tipo de servicio específico.", "parameters": {"type": "object", "properties": {"tipo_servicio": {"type": "string"}}, "required": ["tipo_servicio"]}},
            {"name": "ranking_tipos_servicios", "description": "Muestra el ranking de tipos de servicio con mayor gasto total.", "parameters": {"type": "object", "properties": {}}},
            {"name": "top_contratos_mas_costosos", "description": "Lista de los contratos más costosos actualmente activos.", "parameters": {"type": "object", "properties": {}}}
        ]

    def call_step_1(self, user_message: str):
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}],
            functions=self.functions_spec,
            temperature=0
        )
        return response

    def call_step_2(self, function_name: str, function_result: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Este es el resultado de la función local. Devuélvelo de forma clara al usuario."},
                {"role": "assistant", "name": function_name, "content": function_result}
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip()
