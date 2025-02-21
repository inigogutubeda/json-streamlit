########################################
# app.py
########################################
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# Lógica Chatbot
from rag.pipeline import process_user_question

# BD queries para el Dashboard
from rag.db_queries import get_contratos, get_facturas, top_conceptos_global

st.set_page_config(
    page_title="POC Residencias (Function Calling)",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Opcional: algo de CSS
CUSTOM_CSS = """
<style>
.main > div {
    padding-left: 3rem;
    padding-right: 3rem;
}
h1, h2, h3 {
    text-align: center;
    color: #4CAF50;
}
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

def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase_client = init_connection()

########### SECCIONES DEL DASHBOARD ###########
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
    st.dataframe(df_contr) if not df_contr.empty else st.warning("No hay contratos.")
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

    fig = px.bar(
        df_fact,
        x="numero",
        y="total",
        title=f"Facturación {centro_sel}",
        labels={"numero": "Factura", "total": "Importe (€)"}
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


########### SECCIÓN DEL CHATBOT ###########
def vista_chatbot():
    st.header("Chatbot con GPT-4 function calling (sin regex)")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_input = st.text_input("Pregunta al Chatbot:", "")
    if st.button("Enviar"):
        openai_api_key = st.secrets.get("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("Falta la clave OPENAI_API_KEY en secrets.")
        else:
            respuesta = process_user_question(supabase_client, user_input, openai_api_key)
            st.session_state["chat_history"].append(("user", user_input))
            st.session_state["chat_history"].append(("bot", respuesta))

    st.subheader("Historial")
    for role, msg in st.session_state["chat_history"]:
        if role == "user":
            st.markdown(f'<div class="user-message">{msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">{msg}</div>', unsafe_allow_html=True)

########################################
# MAIN
########################################
def main():
    st.sidebar.title("POC Residencias")
    section = st.sidebar.radio("Navegación", ["Dashboard", "Chatbot"])

    if section == "Dashboard":
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
