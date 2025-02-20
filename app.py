import os
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
# Importa la nueva interfaz
from openai import OpenAI

########################################
# CONFIGURACIÓN INICIAL STREAMLIT
########################################
st.set_page_config(
    page_title="POC Residencias",
    layout="wide",
    initial_sidebar_state="expanded",
)

def init_connection():
    """
    Crea y retorna la conexión a Supabase usando los secrets:
      SUPABASE_URL
      SUPABASE_KEY
    """
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    return supabase

########################################
# DASHBOARD
########################################
def mostrar_dashboard(supabase_client: Client):
    st.title("Dashboard - Residencias")
    st.write("Visualiza información de contratos y facturas.")

    # 1) Obtener Contratos
    contratos_resp = supabase_client.table("contratos").select("*").execute()
    contratos_data = contratos_resp.data or []

    # 2) Obtener Facturas
    facturas_resp = supabase_client.table("facturas").select("*").execute()
    facturas_data = facturas_resp.data or []

    df_contratos = pd.DataFrame(contratos_data)
    df_facturas = pd.DataFrame(facturas_data)

    # Muestra Contratos
    if df_contratos.empty:
        st.warning("No hay contratos registrados.")
    else:
        st.subheader("Lista de Contratos")
        st.dataframe(df_contratos)

    # Muestra Facturas
    if df_facturas.empty:
        st.warning("No hay facturas registradas.")
    else:
        st.subheader("Lista de Facturas")
        st.dataframe(df_facturas)

        # Ejemplo de gráfico: total facturado por contrato
        df_facturas["total"] = pd.to_numeric(df_facturas["total"], errors="coerce").fillna(0)
        fig = px.bar(
            df_facturas,
            x="contrato_id",
            y="total",
            title="Facturación por Contrato"
        )
        st.plotly_chart(fig, use_container_width=True)

########################################
# CHATBOT (RAG SENCILLO)
########################################
def chatbot_rag(supabase_client: Client):
    st.title("Agente Conversacional")
    st.write("Pregunta sobre tus contratos y facturas. El sistema buscará coincidencias básicas en la tabla 'facturas' y le pasará esa info al modelo GPT.")

    # 1) Recuperamos la clave de OpenAI
    openai_api_key = st.secrets.get("OPENAI_API_KEY")
    if not openai_api_key:
        st.error("Falta la clave OPENAI_API_KEY en Streamlit Secrets.")
        return

    # 2) Creamos el cliente de la nueva librería openai>=1.0
    client = OpenAI(api_key=openai_api_key)

    # 3) Input del usuario
    user_input = st.text_input("¿Qué deseas consultar?", "")
    if st.button("Enviar") and user_input.strip():
        # Búsqueda trivial en la tabla "facturas"
        resp = supabase_client.table("facturas").select("*").execute()
        facturas = resp.data if resp.data else []

        def match_query(f):
            texto = (f.get("numero_factura", "") + " " + f.get("concepto", "")).lower()
            return user_input.lower() in texto

        matching = [f for f in facturas if match_query(f)]

        # Construimos un "contexto"
        contexto = f"He encontrado {len(matching)} facturas relevantes:\n"
        for f in matching[:3]:
            contexto += (
                f"- Factura {f.get('numero_factura','')} "
                f"concepto: {f.get('concepto','')} "
                f"total: {f.get('total','')}\n"
            )

        # Montamos el mensaje final
        # Ejemplo: Usamos ChatCompletions:
        #   client.chat.completions.create(
        #       model="gpt-4o",
        #       messages=[{ "role": "user", "content": "..."}]
        #   )
        prompt = f"Contexto:\n{contexto}\nEl usuario pregunta: {user_input}"

        try:
            chat_completion = client.chat.completions.create(
                model="gpt-4o",  # Cambiar a "gpt-3.5-turbo" si corresponde
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                store=True  # si quieres guardar la conversación en OpenAI
            )
            respuesta = chat_completion.choices[0].message.content.strip()
            st.success(respuesta)

        except Exception as e:
            st.error(f"Error al llamar a OpenAI con la nueva librería: {e}")

########################################
# MAIN DE STREAMLIT
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
