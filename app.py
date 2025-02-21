# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

from rag.pipeline import process_user_question
from rag.db_queries import get_contratos, get_facturas, top_conceptos_global

st.set_page_config(page_title="POC Residencias", layout="wide")

def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase_client = init_connection()

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

    st.dataframe(df_contr)
    st.dataframe(df_fact)

def vista_por_residencia():
    st.subheader("Análisis por Residencia")
    df_contr = get_contratos(supabase_client)
    if df_contr.empty:
        st.warning("No hay contratos.")
        return
    centros = df_contr["centro"].dropna().unique().tolist()
    sel = st.selectbox("Residencia:", ["(Todas)"]+centros)
    df_fact = get_facturas(supabase_client)
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)

    if sel!="(Todas)":
        df_contr = df_contr[df_contr["centro"]==sel]
        cids = df_contr["id"].unique().tolist()
        df_fact = df_fact[df_fact["contrato_id"].isin(cids)]
    st.dataframe(df_contr)
    st.dataframe(df_fact)
    suma = df_fact["total"].sum()
    st.metric(f"Gasto total en {sel}", f"{suma:,.2f} €")

    fig = px.bar(df_fact, x="numero_factura", y="total", title="Facturas")
    st.plotly_chart(fig, use_container_width=True)

def vista_top_conceptos():
    st.subheader("Top Conceptos")
    df_top = top_conceptos_global(supabase_client)
    if df_top.empty:
        st.warning("No hay facturas.")
        return
    st.dataframe(df_top.head(10))
    fig = px.bar(df_top.head(10), x="concepto", y="total", title="Top conceptos")
    st.plotly_chart(fig, use_container_width=True)

def vista_chatbot():
    st.header("Chatbot GPT-4 (function calling)")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_input = st.text_input("Pregunta al chatbot:")
    if st.button("Enviar"):
        openai_api_key = st.secrets.get("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("Falta OPENAI_API_KEY en secrets.")
        else:
            resp = process_user_question(supabase_client, user_input, openai_api_key)
            st.session_state["chat_history"].append(("user", user_input))
            st.session_state["chat_history"].append(("bot", resp))

    st.subheader("Historial")
    for r, m in st.session_state["chat_history"]:
        if r=="user":
            st.markdown(f"**Usuario**: {m}")
        else:
            st.markdown(f"**Bot**: {m}")

def main():
    st.sidebar.title("POC Residencias")
    menu = ["Dashboard","Chatbot"]
    sel = st.sidebar.radio("Navegación", menu)
    if sel=="Dashboard":
        tabs = st.tabs(["Visión General","Por Residencia","Top Conceptos"])
        with tabs[0]:
            vista_general_dashboard()
        with tabs[1]:
            vista_por_residencia()
        with tabs[2]:
            vista_top_conceptos()
    else:
        vista_chatbot()

if __name__=="__main__":
    main()
