# rag/gpt.py

from openai import OpenAI

def create_gpt_client(api_key: str) -> OpenAI:
    """
    Crea y retorna la instancia de la clase OpenAI (nuevo SDK >=1.0).
    """
    return OpenAI(api_key=api_key)

def build_prompt(context: str, user_question: str) -> str:
    """
    Combina el contexto extraído de la BD con la pregunta del usuario
    para generar el contenido final que se pasará como 'user' message.
    """
    prompt = (
        "Eres un asistente experto en facturación y contratos. "
        "Usa el siguiente contexto para responder:\n\n"
        f"{context}\n\n"
        "Pregunta:\n"
        f"{user_question}\n\n"
        "Respuesta:"
    )
    return prompt

def chat_completion(client: OpenAI, prompt: str, model: str = "gpt-4o") -> str:
    """
    Llama a client.chat.completions.create(...),
    retorna la respuesta como string.

    - client: instancia de OpenAI
    - prompt: texto a enviar en messages[0].content
    - model: "gpt-4o", "gpt-4", "gpt-3.5-turbo", etc.
    """
    chat_completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        store=False
    )
    return chat_completion.choices[0].message.content.strip()
