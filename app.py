# app.py

import os
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# Importar pipeline RAG
from rag.pipeline import process_user_question

########################################
# CONFIG
########################################
st.set_page_config(
    page_title="POC Residencias",
    layout="wide",
    initial_sidebar_state="expanded",
)

def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

########################################
# DASHBOARD
########################################
def mostrar_dashboard(supabase_client: Client):
    st.title("Dashboard - Residencias")

    # Contratos
    contratos_resp = supabase_client.table("contratos").select("*").execute()
    df_contratos = pd.DataFrame(contratos_resp.data or [])

    # Facturas
    facturas_resp = supabase_client.table("facturas").select("*").execute()
    df_facturas = pd.DataFrame(facturas_resp.data or [])

    # Mostrar Contratos
    if df_contratos.empty:
        st.warning("No hay contratos registrados.")
    else:
        st.subheader("Contratos")
        st.dataframe(df_contratos)

    # Mostrar Facturas
    if df_facturas.empty:
        st.warning("No hay facturas registradas.")
        return

    st.subheader("Facturas")
    st.dataframe(df_facturas)

    # Intento de parsear fecha_factura
    df_facturas["fecha_factura"] = pd.to_datetime(df_facturas["fecha_factura"], errors="coerce")
    df_facturas["total"] = pd.to_numeric(df_facturas["total"], errors="coerce").fillna(0)

    # Gráfico de barras: total por contrato
    fig = px.bar(
        df_facturas,
        x="contrato_id",
        y="total",
        title="Facturación por Contrato"
    )
    st.plotly_chart(fig, use_container_width=True)

########################################
# CHATBOT
########################################
def chatbot_rag(supabase_client: Client):
    st.title("Chatbot RAG")

    # OpenAI API Key
    openai_api_key = st.secrets.get("OPENAI_API_KEY")
    if not openai_api_key:
        st.error("Falta la clave OPENAI_API_KEY en secrets.")
        return

    user_input = st.text_input("Pregunta (ej: ¿Cuánto gastamos con American Tower en 2024?)", "")
    if st.button("Enviar"):
        respuesta = process_user_question(supabase_client, user_input, openai_api_key)
        st.success(respuesta)

########################################
# MAIN
########################################
def main():
    supabase_client = init_connection()

    menu = ["Dashboard", "Chatbot"]
    choice = st.sidebar.radio("Menú", menu)
    if choice == "Dashboard":
        mostrar_dashboard(supabase_client)
    else:
        chatbot_rag(supabase_client)

if __name__ == "__main__":
    main()
