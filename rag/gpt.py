# rag/gpt.py
from openai import OpenAI

def create_gpt_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)

def build_prompt(context: str, user_question: str) -> str:
    prompt = (
        "Eres un asistente experto en facturación y contratos. "
        "Usa el siguiente contexto para responder de forma breve y útil:\n\n"
        f"{context}\n\n"
        "Pregunta del usuario:\n"
        f"{user_question}\n\n"
        "Respuesta:"
    )
    return prompt

def chat_completion(client: OpenAI, prompt: str, model: str = "gpt-3.5-turbo") -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        store=False
    )
    return resp.choices[0].message.content.strip()
