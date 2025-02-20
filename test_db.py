import os
from dotenv import load_dotenv
from supabase import create_client, Client

def test_supabase_connection():
    # Carga las variables desde el archivo .env
    load_dotenv()

    # Lee las variables de entorno
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("No se han encontrado SUPABASE_URL o SUPABASE_KEY en el entorno o .env")

    # Crea el cliente de Supabase
    supabase: Client = create_client(url, key)

    try:
        # Realizamos una operación de prueba, por ejemplo, leer datos de una tabla "prueba"
        # Asegúrate de tener creada la tabla en el proyecto Supabase
        response = supabase.table("prueba").select("*").execute()
        print("¡Conexión exitosa a Supabase!")
        print("Datos en la tabla 'prueba':", response.data)

    except Exception as e:
        print("Error realizando consulta en Supabase:", e)


if __name__ == "__main__":
    test_supabase_connection()
