import os
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# Lógica RAG
from rag.pipeline import process_user_question
# Para dashboard
from rag.db_queries import (
    get_contratos,
    get_facturas,
    top_conceptos_global
)

########################################
# CONFIGURACIÓN STREAMLIT
########################################
st.set_page_config(
    page_title="POC Residencias",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
/* Ajuste del contenedor principal */
.main > div {
    padding-left: 3rem;
    padding-right: 3rem;
    background-color: #FFFFFF; 
}
/* Títulos centrados */
h1, h2, h3 {
    text-align: center;
    color: #4CAF50;
}
/* Chat */
.chat-container {
    background-color: #F0F2F6;
    border-radius: 5px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.user-message {
    background-color: #DCF8C6;
    border-radius: 5px;
    padding: 0.5rem;
    margin-bottom: 0.5rem;
    display: inline-block;
}
.bot-message {
    background-color: #FFFFFF;
    border-radius: 5px;
    border: 1px solid #DDD;
    padding: 0.5rem;
    margin-bottom: 0.5rem;
    display: inline-block;
    color: #333;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

########################################
# Conexión Supabase
########################################
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    return supabase

supabase_client = init_connection()

########################################
# Funciones Dashboard
########################################
def vista_general_dashboard():
    st.subheader("Visión General")

    df_contr = get_contratos(supabase_client)
    df_fact = get_facturas(supabase_client)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Contratos totales", len(df_contr))
    with col2:
        st.metric("Facturas totales", len(df_fact))
    with col3:
        df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
        st.metric("Total facturado", f"{df_fact['total'].sum():,.2f} €")

    st.markdown("---")

    st.write("**Contratos**")
    if df_contr.empty:
        st.warning("No hay contratos.")
    else:
        st.dataframe(df_contr)

    st.write("**Facturas**")
    if df_fact.empty:
        st.warning("No hay facturas.")
    else:
        st.dataframe(df_fact)


def vista_por_residencia():
    st.subheader("Análisis por Residencia/Centro")
    df_contr = get_contratos(supabase_client)
    if df_contr.empty:
        st.warning("No hay contratos.")
        return

    centros = df_contr["centro"].dropna().unique().tolist()
    centro_sel = st.selectbox("Elige una residencia/centro:", ["(Todos)"] + centros)

    df_fact = get_facturas(supabase_client)
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)

    
    if centro_sel != "(Todos)":
        df_contr = df_contr[df_contr["centro"] == centro_sel]
        cids = df_contr["id"].unique().tolist()
        df_fact = df_fact[df_fact["contrato_id"].isin(cids)]

    st.write(f"**Contratos en {centro_sel}**")
    st.dataframe(df_contr)

    st.write(f"**Facturas en {centro_sel}**")
    if df_fact.empty:
        st.info("No hay facturas para este centro.")
        return

    st.dataframe(df_fact)
    gasto_total = df_fact["total"].sum()
    st.metric(f"Gasto total en {centro_sel}", f"{gasto_total:,.2f} €")

    # Grafico
    fig = px.bar(
        df_fact,
        x="numero_factura",
        y="total",
        title=f"Facturación {centro_sel}",
        labels={"numero_factura": "Factura", "total": "Importe (€)"}
    )
    st.plotly_chart(fig, use_container_width=True)


def vista_top_conceptos():
    st.subheader("Top Conceptos de Gasto")
    df_top = top_conceptos_global(supabase_client)
    if df_top.empty:
        st.warning("No hay facturas.")
        return
    st.write("Ranking de conceptos (desc):")
    st.dataframe(df_top)

    fig = px.bar(
        df_top.head(10),
        x="concepto",
        y="total",
        title="Top 10 Conceptos",
        labels={"concepto": "Concepto", "total": "Total (€)"}
    )
    st.plotly_chart(fig, use_container_width=True)

########################################
# Chatbot
########################################
def vista_chatbot():
    st.header("Chatbot (RAG)")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    st.write("Preguntas de ejemplo: “¿En qué residencia gastamos más en 2024?” o “¿Cuántas facturas tenemos?”,“¿Cuál es la factura más reciente?”"
             )
    user_input = st.text_input("Escribe tu pregunta:", "")
    if st.button("Enviar"):
        if user_input.strip():
            openai_api_key = st.secrets.get("OPENAI_API_KEY")
            if not openai_api_key:
                st.error("Falta OPENAI_API_KEY en secrets.")
            else:
                respuesta = process_user_question(supabase_client, user_input, openai_api_key)
                st.session_state["chat_history"].append(("user", user_input))
                st.session_state["chat_history"].append(("bot", respuesta))

    # Mostrar historial
    st.subheader("Historial")
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for role, msg in st.session_state["chat_history"]:
            if role == "user":
                st.markdown(f'<div class="user-message">{msg}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-message">{msg}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

########################################
# MAIN
########################################
def main():
    st.sidebar.title("POC Residencias")
    op = st.sidebar.radio("Navegación", ["Dashboard", "Chatbot"])

    if op == "Dashboard":
        # Tabs en el dashboard
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
