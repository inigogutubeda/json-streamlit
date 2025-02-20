import os
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import openai

########################################
# CONFIGURACIÓN INICIAL DE LA APP
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

    # Convertir a DataFrames
    df_contratos = pd.DataFrame(contratos_data)
    df_facturas = pd.DataFrame(facturas_data)

    # Si no hay contratos, mostramos aviso
    if df_contratos.empty:
        st.warning("No hay contratos registrados.")
        return

    st.subheader("Lista de Contratos")
    st.dataframe(df_contratos)

    st.subheader("Lista de Facturas")
    if df_facturas.empty:
        st.warning("No hay facturas registradas.")
    else:
        st.dataframe(df_facturas)
        # Ejemplo de gráfico de barras: total facturado por contrato
        df_facturas["total"] = pd.to_numeric(df_facturas["total"], errors="coerce").fillna(0)
        fig = px.bar(
            df_facturas, 
            x="contrato_id", 
            y="total", 
            title="Facturación por Contrato"
        )
        st.plotly_chart(fig, use_container_width=True)

########################################
# FUNCIÓN DEL CHATBOT (con la nueva API ChatCompletion)
########################################
def chatbot_rag(supabase_client: Client):
    st.title("Agente Conversacional")
    st.write("Consulta información sobre tus contratos/facturas usando GPT-3.5/GPT-4.")

    # Clave de OpenAI desde los secrets
    openai_api_key = st.secrets.get("OPENAI_API_KEY", None)
    if not openai_api_key:
        st.error("No se encuentra la clave OPENAI_API_KEY en secrets. Por favor configúrala.")
        return

    openai.api_key = openai_api_key

    user_input = st.text_input("Pregunta sobre tus datos (contratos, facturas, etc.):")
    
    if st.button("Enviar") and user_input:
        # Búsqueda muy básica en la tabla "facturas"
        query = supabase_client.table("facturas").select("*").execute()
        facturas_data = query.data if query.data else []

        # Filtro casero: busca si user_input está en 'numero_factura' o 'concepto'
        def contains_query(item):
            texto = f"{item.get('numero_factura','')} {item.get('concepto','')}"
            return user_input.lower() in texto.lower()

        matching_facturas = [f for f in facturas_data if contains_query(f)]

        # Construir un contexto mínimo con las facturas encontradas
        contexto = f"He encontrado {len(matching_facturas)} facturas:\n"
        for f in matching_facturas[:3]:  # máx 3 facturas para no saturar
            contexto += (
                f"- Factura {f.get('numero_factura','')}, "
                f"concepto: {f.get('concepto','')}, "
                f"total: {f.get('total','')}\n"
            )

        # Montamos los mensajes para ChatCompletion
        messages = [
            {"role": "system", "content": (
                "Eres un asistente experto en facturación y contratos. "
                "Usa el contexto proporcionado para responder de forma breve y útil."
            )},
            {"role": "user", "content": f"Contexto:\n{contexto}\n\nMi pregunta: {user_input}"}
        ]

        try:
            # Llamamos a ChatCompletion
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # o "gpt-4" si lo tienes disponible
                messages=messages,
                max_tokens=300,
                temperature=0.2
            )
            respuesta = response.choices[0].message.content.strip()
            st.write(respuesta)
        except Exception as e:
            st.error(f"Error al llamar a OpenAI: {e}")

########################################
# MAIN STREAMLIT
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
