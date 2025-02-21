# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# Importa la lógica del RAG y el chatbot
from rag.pipeline import process_user_question
from rag.db_queries import (
    get_contratos,
    get_facturas,
    top_residencias_por_gasto,
    analisis_gastos_mensuales,
    facturas_pendientes,
    proveedor_con_mayor_gasto,
)

st.set_page_config(page_title="POC Residencias", layout="wide")

def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase_client = init_connection()

########################################
# 📊 DASHBOARD 📊
########################################

def vista_general_dashboard():
    st.subheader("Visión General")
    df_contr = get_contratos(supabase_client)
    df_fact = get_facturas(supabase_client)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Contratos totales", len(df_contr))
    with c2:
        st.metric("Facturas totales", len(df_fact))
    with c3:
        df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
        st.metric("Total facturado", f"{df_fact['total'].sum():,.2f} €")

    st.markdown("### Contratos")
    st.dataframe(df_contr)

    st.markdown("### Facturas")
    st.dataframe(df_fact)


def vista_por_residencia():
    st.subheader("Análisis por Residencia")
    df_contr = get_contratos(supabase_client)
    if df_contr.empty:
        st.warning("No hay contratos.")
        return

    centros = df_contr["centro"].dropna().unique().tolist()
    sel = st.selectbox("Residencia:", ["(Todas)"] + centros)
    df_fact = get_facturas(supabase_client)
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)

    if sel != "(Todas)":
        df_contr = df_contr[df_contr["centro"] == sel]
        cids = df_contr["id"].unique().tolist()
        df_fact = df_fact[df_fact["contrato_id"].isin(cids)]

    st.markdown(f"### Contratos en {sel}")
    st.dataframe(df_contr)

    st.markdown(f"### Facturas en {sel}")
    if df_fact.empty:
        st.warning("No hay facturas para esta residencia.")
        return

    st.dataframe(df_fact)
    suma = df_fact["total"].sum()
    st.metric(f"Gasto total en {sel}", f"{suma:,.2f} €")

    fig = px.bar(df_fact, x="numero_factura", y="total", title="Facturas por Residencia")
    st.plotly_chart(fig, use_container_width=True)


def vista_top_conceptos():
    st.subheader("Top Residencias y Gastos")
    
    # Residencias con mayor gasto
    top_residencias = top_residencias_por_gasto(supabase_client)
    st.markdown("### Residencias con Mayor Gasto")
    st.write(top_residencias)

    # Análisis de gasto mensual
    year = st.slider("Selecciona un año", 2020, 2025, 2024)
    gasto_mensual = analisis_gastos_mensuales(supabase_client, year)
    st.markdown(f"### Análisis de Gasto Mensual en {year}")
    st.write(gasto_mensual)

    # Facturas pendientes
    st.markdown("### Facturas Pendientes")
    fact_pend = facturas_pendientes(supabase_client)
    st.write(fact_pend)

    # Proveedor con mayor gasto
    st.markdown("### Proveedor con Mayor Gasto")
    prov_gasto = proveedor_con_mayor_gasto(supabase_client)
    st.write(prov_gasto)


########################################
# 🤖 CHATBOT 🤖
########################################

def vista_chatbot():
    st.header("Chatbot GPT-4 (function calling)")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_input = st.text_input("Pregunta al chatbot:")

    if st.button("Enviar"):
        openai_api_key = st.secrets.get("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("Falta la clave OPENAI_API_KEY en secrets.")
        else:
            respuesta = process_user_question(supabase_client, user_input, openai_api_key)
            st.session_state["chat_history"].append(("Usuario", user_input))
            st.session_state["chat_history"].append(("Chatbot", respuesta))

    st.subheader("Historial de Conversación")
    for role, text in st.session_state["chat_history"]:
        st.markdown(f"**{role}:** {text}")


########################################
# 🚀 NAVEGACIÓN ENTRE SECCIONES
########################################

def main():
    st.sidebar.title("POC Residencias")
    menu = ["Dashboard", "Chatbot"]
    sel = st.sidebar.radio("Navegación", menu)

    if sel == "Dashboard":
        tabs = st.tabs(["Visión General", "Por Residencia", "Top Conceptos"])
        with tabs[0]:
            vista_general_dashboard()
        with tabs[1]:
            vista_por_residencia()
        with tabs[2]:
            vista_top_conceptos()
    else:
        vista_chatbot()


if __name__ == "__main__":
    main()
