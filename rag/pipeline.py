# rag/pipeline.py
from .parser import interpret_question
from .db_queries import (
    get_facturas, get_facturas_by_proveedor_and_year
)
from .gpt import create_gpt_client, build_prompt, chat_completion

import pandas as pd

def process_user_question(supabase_client, user_input, openai_api_key=""):
    intent_data = interpret_question(user_input)
    intent = intent_data["intent"]
    context_str = ""

    if intent == "get_total_year_by_proveedor":
        year = intent_data["year"]
        prov_str = intent_data["proveedor"]
        df_fact = get_facturas_by_proveedor_and_year(supabase_client, prov_str, year)
        if df_fact.empty:
            context_str = (
                f"No encontré facturas para el proveedor '{prov_str}' "
                f"en el año {year}.\n"
            )
        else:
            total = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0).sum()
            context_str = (
                f"Para el proveedor '{prov_str}' en {year}, "
                f"hay {len(df_fact)} facturas, con un total de {total}.\n"
            )

    elif intent == "get_total_year":
        year = intent_data["year"]
        df_fact = get_facturas(supabase_client)
        df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
        df_fact["year"] = df_fact["fecha_factura"].dt.year
        df_fact = df_fact[df_fact["year"] == year]
        if df_fact.empty:
            context_str = f"No encontré facturas en {year}.\n"
        else:
            total = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0).sum()
            context_str = (
                f"En el año {year}, hallé {len(df_fact)} facturas, con un total de {total}.\n"
            )

    else:
        context_str = "No reconozco la intención. No se hizo ninguna consulta.\n"

    # Generamos prompt final
    prompt = build_prompt(context_str, user_input)
    if not openai_api_key:
        return f"(ERROR) Falta la OpenAI API Key. Contexto: {context_str}"

    gpt_client = create_gpt_client(openai_api_key)
    return chat_completion(gpt_client, prompt, model="gpt-4o")
