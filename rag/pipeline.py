# rag/pipeline.py

from .parser import interpret_question
from .db_queries import (
    get_facturas,
    facturas_con_importe_mayor,
    proveedor_mas_contratos,
    factura_mas_reciente,
    gasto_en_rango_fechas,
    contratos_vencen_antes_de,
    # + las funciones que ya teníamos (ranking_gastos_por_centro, etc.)
)
from .gpt import create_gpt_client, build_prompt, chat_completion

import pandas as pd

def process_user_question(supabase_client, user_input, openai_api_key=""):
    intent_data = interpret_question(user_input)
    intent = intent_data["intent"]
    context_str = ""

    # 1) facturas_importe_mayor
    if intent == "facturas_importe_mayor":
        importe = intent_data.get("importe", None)
        if importe is None:
            context_str = "No se reconoció el importe."
        else:
            df_res = facturas_con_importe_mayor(supabase_client, importe)
            if df_res.empty:
                context_str = f"No hay facturas con importe mayor a {importe}."
            else:
                context_str = f"Encontré {len(df_res)} facturas con importe mayor a {importe}.\n"
                df_res["total"] = df_res["total"].astype(float)
                sum_importe = df_res["total"].sum()
                context_str += f"Suma de esas facturas = {sum_importe:.2f}."

    # 2) proveedor_mas_contratos
    elif intent == "proveedor_mas_contratos":
        df_rank = proveedor_mas_contratos(supabase_client)
        if df_rank.empty:
            context_str = "No hay contratos ni proveedores."
        else:
            top = df_rank.iloc[0]
            context_str = "Ranking de Proveedores por número de contratos:\n"
            for i, row in df_rank.iterrows():
                context_str += f"- {row['nombre_proveedor']}: {row['num_contratos']} contratos\n"
            context_str += f"\nEl que más contratos tiene es {top['nombre_proveedor']} con {top['num_contratos']}."

    # 3) factura_mas_reciente
    elif intent == "factura_mas_reciente":
        row = factura_mas_reciente(supabase_client)
        if row is None:
            context_str = "No encontré facturas con fecha válida."
        else:
            context_str = (f"La factura más reciente es '{row['numero_factura']}' "
                           f"con fecha {row['fecha_factura']} y total {row['total']}.")

    # 4) gasto_en_rango
    elif intent == "gasto_en_rango":
        fecha_i = intent_data.get("fecha_inicio", None)
        fecha_f = intent_data.get("fecha_fin", None)
        if not fecha_i or not fecha_f:
            context_str = "No se encontraron fechas de inicio y fin."
        else:
            total_rango = gasto_en_rango_fechas(supabase_client, fecha_i, fecha_f)
            if total_rango < 0:
                context_str = "No pude parsear las fechas (dd/mm/yyyy)."
            else:
                context_str = (f"El gasto total entre {fecha_i} y {fecha_f} "
                               f"es de {total_rango:.2f}.")

    # 5) contratos_vencen_antes
    elif intent == "contratos_vencen_antes":
        vence_str = intent_data.get("fecha_vencimiento")
        df = contratos_vencen_antes_de(supabase_client, vence_str)
        if df.empty:
            context_str = f"No hay contratos que venzan antes de {vence_str}."
        else:
            context_str = f"Contratos que vencen antes de {vence_str}: {len(df)}.\n"
            # Ejemplo: enumerarlos
            for i, row in df.iterrows():
                context_str += f"- Contrato ID {row['id']} en centro {row['centro']}, vence {row['fecha_vencimiento']}\n"

    else:
        # Mantén aquí las intenciones anteriores (ranking_gastos_centros, etc.)
        # ...
        # Si nada coincide => fallback
        context_str = "No reconozco la intención con los datos disponibles."

    # Final: build prompt & GPT
    prompt = build_prompt(context_str, user_input)
    if not openai_api_key:
        return f"(ERROR) Falta la OpenAI API Key. CONTEXTO: {context_str}"

    client = create_gpt_client(openai_api_key)
    respuesta = chat_completion(client, prompt, model="gpt-3.5-turbo")
    return respuesta
