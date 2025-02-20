import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from supabase import create_client, Client
import openai

########################################
# CONFIGURACIÓN INICIAL DE LA APP
########################################
st.set_page_config(
    page_title="POC Residencias",
    layout="wide",  # “wide” para usar todo el ancho de la pantalla
    initial_sidebar_state="expanded",
)

def init_connection():
    """
    Crea y retorna la conexión a Supabase.
    Lee las variables de entorno desde st.secrets o .env (según despliegue).
    """
    # Opción 1: usar st.secrets (si estás en Streamlit Cloud y guardaste tus credenciales)
    url = st.secrets["postgres"]["host"] if "postgres" in st.secrets else None
    user = st.secrets["postgres"]["user"] if "postgres" in st.secrets else None
    password = st.secrets["postgres"]["password"] if "postgres" in st.secrets else None
    db = st.secrets["postgres"]["database"] if "postgres" in st.secrets else None
    port = st.secrets["postgres"]["port"] if "postgres" in st.secrets else "5432"

    # Opción 2: usar .env local (si estás en local)
    if not url:
        load_dotenv()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        return create_client(url, key)
    else:
        # Si estás en Streamlit Cloud, para Supabase "oficial" se suele usar:
        # supabase = create_client(url, key)
        # Pero si st.secrets te da un host/port... eso suena más a Postgres “directo”
        # Forzamos un “raw” psycopg2 approach o ajustas a tu preferencia.
        # Aquí asumo que preferimos “supabase-py”
        # con st.secrets["postgres"]["host"] = “https://xxxxx.supabase.co”
        key = "TU_API_KEY"  # Cambia si estás guardando la clave en un secret distinto

        # Ajusta la forma en que guardaste tus secrets
        # (Si guardaste “SUPABASE_URL” y “SUPABASE_KEY” en st.secrets, cambia la lógica)
        return create_client(url, key)


########################################
# FUNCIÓN DE DASHBOARD
########################################
def mostrar_dashboard(supabase_client: Client):
    st.title("Dashboard - Residencias")
    st.write("Visualiza información de contratos y facturas.")

    # 1) Obtener datos de contratos
    contratos_resp = supabase_client.table("contratos").select("*").execute()
    contratos_data = contratos_resp.data if contratos_resp.data else []

    # 2) Obtener datos de facturas
    facturas_resp = supabase_client.table("facturas").select("*").execute()
    facturas_data = facturas_resp.data if facturas_resp.data else []

    # Convertirlos a DataFrame (para manipular en Streamlit)
    df_contratos = pd.DataFrame(contratos_data)
    df_facturas = pd.DataFrame(facturas_data)

    # Evita error si están vacíos
    if df_contratos.empty:
        st.warning("No hay contratos registrados.")
        return

    # Muestra tabla de Contratos
    st.subheader("Lista de Contratos")
    st.dataframe(df_contratos)

    # Muestra tabla de Facturas
    st.subheader("Lista de Facturas")
    if df_facturas.empty:
        st.warning("No hay facturas registradas.")
    else:
        st.dataframe(df_facturas)

        # Ejemplo simple: gráfico de barras con total facturado por contrato
        df_facturas["total"] = df_facturas["total"].astype(float)
        fig = px.bar(df_facturas, x="contrato_id", y="total", title="Facturación por Contrato")
        st.plotly_chart(fig, use_container_width=True)


########################################
# FUNCIÓN DEL CHATBOT (RAG BÁSICO)
########################################
def chatbot_rag(supabase_client: Client):
    st.title("Agente Conversacional")
    st.write("Consulta información sobre tus contratos y facturas.")

    openai_api_key = st.text_input("Introduce tu OpenAI API Key (no se guardará):", type="password")
    if not openai_api_key:
        st.warning("Por favor, introduce tu clave para usar el chatbot.")
        return

    # Configurar la clave para la sesión actual
    openai.api_key = openai_api_key

    user_input = st.text_input("Haz una pregunta sobre tus contratos/facturas:")

    if st.button("Enviar") and user_input:
        # 1) Recuperar contexto “mínimo” de la BD
        #    Por ejemplo, si la pregunta menciona una factura, buscar en DB.
        #    Para la POC, haremos algo muy simple: “buscar en las tablas” si hay algo
        #    que contenga las palabras de la pregunta, etc. En producción, usarías
        #    embeddings + vectores para un RAG real.

        # Minibúsqueda super simple:
        query = supabase_client.table("facturas").select("*").execute()
        facturas_data = query.data if query.data else []

        # Filtrar o “buscar” (casero) en concepto, número_factura... 
        # (por tiempo, haremos un substring match)
        def contains_query(item):
            texto = f"{item.get('numero_factura', '')} {item.get('concepto','')}"
            return user_input.lower() in texto.lower()

        matching_facturas = [f for f in facturas_data if contains_query(f)]

        # 2) Construimos un “contexto”
        contexto = f"Base de datos: He encontrado {len(matching_facturas)} facturas que coinciden con tu búsqueda.\n\n"
        for f in matching_facturas[:3]:  # limitamos a 3
            contexto += f"- Factura {f['numero_factura']} concepto: {f['concepto']}, total: {f['total']}\n"

        # 3) Llamada a OpenAI con el contexto
        prompt = f"""Eres un asistente experto en facturación y contratos. 
        El usuario hace esta pregunta: {user_input}
        Usa este contexto (que es real de la base de datos) para responder de forma breve:
        ---
        {contexto}
        ---
        Respuesta:
        """

        # Llamada a la API GPT-3.5 o GPT-4
        try:
            completion = openai.Completion.create(
                engine="text-davinci-003",  # o gpt-3.5-turbo con slightly different usage
                prompt=prompt,
                max_tokens=200,
                temperature=0.2
            )
            respuesta = completion.choices[0].text.strip()
            st.write(respuesta)
        except Exception as e:
            st.error(f"Error al llamar a OpenAI: {e}")


########################################
# FLUJO PRINCIPAL DE LA APP STREAMLIT
########################################
def main():
    supabase_client = init_connection()

    menu = ["Dashboard", "Chatbot"]
    choice = st.sidebar.radio("Menú", menu)

    if choice == "Dashboard":
        mostrar_dashboard(supabase_client)
    elif choice == "Chatbot":
        chatbot_rag(supabase_client)


if __name__ == "__main__":
    main()
