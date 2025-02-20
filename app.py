########################################
# app.py
########################################

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
        df_facturas["total"] = df_facturas["total"].astype(float)
        fig = px.bar(df_facturas, x="contrato_id", y="total",
                     title="Facturación por Contrato")
        st.plotly_chart(fig, use_container_width=True)

########################################
# FUNCIÓN DEL CHATBOT (RAG SIMPLE)
########################################
def chatbot_rag(supabase_client: Client):
    st.title("Agente Conversacional")
    st.write("Consulta información sobre tus contratos/facturas.")

    # Recuperamos la OpenAI API Key desde los secrets
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

        # Construimos un contexto mínimo con las facturas encontradas
        contexto = f"He encontrado {len(matching_facturas)} facturas:\n"
        for f in matching_facturas[:3]:  # máximo 3 para no saturar
            contexto += f"- Factura {f['numero_factura']}, concepto: {f['concepto']}, total: {f['total']}\n"

        # Prompt a OpenAI con ese contexto
        prompt = f"""Eres un asistente experto en facturación y contratos. 
        El usuario pregunta: {user_input}
        
        Basándote en este contexto real:
        {contexto}

        Responde de forma breve y útil:
        """

        try:
            completion = openai.Completion.create(
                engine="text-davinci-003",  # o GPT-3.5-turbo, ajustando la llamada
                prompt=prompt,
                max_tokens=200,
                temperature=0.2
            )
            respuesta = completion.choices[0].text.strip()
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
