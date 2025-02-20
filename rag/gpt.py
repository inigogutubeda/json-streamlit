# rag/gpt.py

from openai import OpenAI

def create_gpt_client(api_key: str) -> OpenAI:
    """
    Crea y retorna la instancia de la clase OpenAI, 
    de acuerdo al nuevo SDK (>=1.0).
    """
    return OpenAI(api_key=api_key)

def build_prompt(context: str, user_question: str) -> str:
    """
    Combina el 'contexto' extraído de la BD con la pregunta
    para generar el contenido final (string) que usaremos en el mensaje 'user'.
    """
    prompt = (
        "Eres un asistente experto en facturación y contratos. "
        "Usa el siguiente contexto real para responder:\n\n"
        f"{context}\n\n"
        "Pregunta:\n"
        f"{user_question}\n\n"
        "Respuesta:"
    )
    return prompt

def chat_completion(client: OpenAI, prompt: str, model: str = "gpt-4o") -> str:
    """
    Llama a la nueva interfaz:
      client.chat.completions.create(
          model=..., 
          messages=[...], 
          ...
      )
    y devuelve la respuesta en formato string.
    
    - client: Es el objeto OpenAI que creamos con create_gpt_client().
    - prompt: El texto que pasaremos como contenido del mensaje 'user'.
    - model: El modelo a usar (p. ej. 'gpt-4o', 'gpt-4', 'gpt-3.5-turbo', etc.).
    """
    chat_completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        store=False  # Set to True si quieres que la conversación se guarde en OpenAI
    )

    # Extraemos el texto de la respuesta
    return chat_completion.choices[0].message.content.strip()
