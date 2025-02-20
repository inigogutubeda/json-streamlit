# rag/pipeline.py
import pandas as pd
from rag.parser import interpret_question
from rag.db_queries import (
    ranking_gastos_por_centro,
    factura_mas_alta_year,
    ranking_proveedores_por_centro,
    resumen_residencia,
    get_facturas
    # etc
)
from rag.gpt import create_gpt_client, build_prompt, chat_completion

def process_user_question(supabase_client, user_input, openai_api_key=""):
    intent_data = interpret_question(user_input)
    intent = intent_data["intent"]
    context_str = ""

    if intent == "ranking_gastos_centros":
        year = intent_data.get("year", None)
        df_rank = ranking_gastos_por_centro(supabase_client, year)
        if df_rank.empty:
            context_str = "No encontré facturas con esa condición."
        else:
            context_str = "Ranking de gasto por centro:\n"
            for i, row in df_rank.iterrows():
                context_str += f"- {row['centro']}: {row['total']:.2f}\n"
            top = df_rank.iloc[0]
            context_str += f"\nEl mayor gasto lo tiene {top['centro']} con {top['total']:.2f}."

    elif intent == "max_factura_year":
        year = intent_data.get("year", None)
        row_max = factura_mas_alta_year(supabase_client, year)
        if row_max is None:
            context_str = f"No encontré facturas para {year}."
        else:
            context_str = (f"La factura más alta en {year} es {row_max['numero_factura']}, "
                           f"con un total de {row_max['total']:.2f} €.")

    elif intent == "ranking_proveedores":
        centro = intent_data.get("centro", None)
        year = intent_data.get("year", None)
        df_rank = ranking_proveedores_por_centro(supabase_client, centro, year)
        if df_rank.empty:
            context_str = "No se encontraron proveedores con esos criterios."
        else:
            context_str = "Ranking de proveedores:\n"
            for i, row in df_rank.iterrows():
                context_str += f"- {row['nombre_proveedor']}: {row['total']:.2f}\n"
            top = df_rank.iloc[0]
            context_str += f"\nEl proveedor con mayor gasto es {top['nombre_proveedor']} con {top['total']:.2f}."

    elif intent == "resumen_residencia":
        centro = intent_data.get("centro")
        if not centro:
            context_str = "No indicaste la residencia."
        else:
            data = resumen_residencia(supabase_client, centro)
            if data is None or data["contratos"].empty:
                context_str = f"No encontré datos para {centro}."
            else:
                total_gasto = data["total_gasto"]
                num_contr = len(data["contratos"])
                num_fact = len(data["facturas"])
                context_str = (
                    f"Resumen de {centro}:\n"
                    f"- Contratos: {num_contr}\n"
                    f"- Facturas: {num_fact}\n"
                    f"- Gasto total: {total_gasto:.2f} €"
                )
    elif intent == "get_total_year":
        year = intent_data.get("year")
        df_fact = get_facturas(supabase_client)
        if df_fact.empty:
            context_str = "No hay facturas."
        else:
            df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
            df_fact["year"] = df_fact["fecha_factura"].dt.year
            df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
            df_fact = df_fact[df_fact["year"] == year]
            if df_fact.empty:
                context_str = f"No hallé facturas en {year}."
            else:
                suma = df_fact["total"].sum()
                context_str = f"En {year} hay {len(df_fact)} facturas por un total de {suma:.2f}€."
    else:
        context_str = "No reconozco la intención con los datos disponibles."

    prompt = build_prompt(context_str, user_input)
    if not openai_api_key:
        return f"(ERROR) Falta la OpenAI API Key. CONTEXTO: {context_str}"

    client = create_gpt_client(openai_api_key)
    respuesta = chat_completion(client, prompt, model="gpt-3.5-turbo")
    return respuesta
