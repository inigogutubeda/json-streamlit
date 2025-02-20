# rag/pipeline.py
from .parser import interpret_question
from .db_queries import get_invoices_by_year, sum_invoices_total, count_invoices
from .gpt import create_gpt_client, build_prompt, chat_completion

def process_user_question(supabase_client, user_input, openai_api_key=""):
    """
    Orquesta el pipeline RAG:
      1) interpreta la pregunta
      2) consulta la BD
      3) genera un contexto
      4) pasa todo a GPT y retorna la respuesta final
    """
    # 1) interpretamos
    intent_data = interpret_question(user_input)

    # 2) según la intención, consultamos
    intent = intent_data["intent"]
    context_str = ""

    if intent == "get_total_year":
        year = intent_data["year"]
        invoices = get_invoices_by_year(supabase_client, year)
        total = sum_invoices_total(invoices)
        context_str = (
            f"Para el año {year}, encontré {len(invoices)} facturas, "
            f"con un total de {total}.\n"
        )

    elif intent == "count_invoices_year":
        year = intent_data["year"]
        invoices = get_invoices_by_year(supabase_client, year)
        c = count_invoices(invoices)
        context_str = (
            f"Para el año {year}, hay {c} facturas registradas.\n"
        )

    else:
        # fallback
        context_str = (
            "No he encontrado una intención clara. No se ha hecho ninguna consulta.\n"
        )

    # 3) Creamos el prompt
    prompt = build_prompt(context_str, user_input)

    # 4) Llamamos a GPT
    if not openai_api_key:
        # si no hay, devolvemos el contexto “pelado” o un error
        return f"(ERROR) Falta la OpenAI API Key. Contexto: {context_str}"

    gpt_client = create_gpt_client(openai_api_key)
    return chat_completion(gpt_client, prompt, model="gpt-4o")
