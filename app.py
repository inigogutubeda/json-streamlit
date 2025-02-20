##############################################
# app.py
##############################################
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# Si tienes tu RAG pipeline, importarlo:
# from rag.pipeline import process_user_question
# from rag.db_queries import get_facturas, get_contratos, get_proveedores, etc.

########################
# CONFIGURACIÓN BÁSICA
########################
st.set_page_config(
    page_title="POC Residencias",
    page_icon="✅",
    layout="wide",
)

# CSS adicional para estilizar elementos
CUSTOM_CSS = """
<style>
/* Ajustar los contenedores principales */
.main > div {
    padding-left: 3rem;
    padding-right: 3rem;
    background-color: #FFFFFF; 
}

/* Contenido de cada tab: ligero margen */
[data-testid="stVerticalBlock"] {
    margin: 1rem;
}

/* Tarjetas para las métricas */
.metric-container {
    background-color: #F7FFFA;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    margin-bottom: 10px;
}

/* Títulos centrados */
h1, h2, h3 {
    text-align: center;
    color: #4CAF50;
}

/* Estilos para el chat */
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

########################
# CONEXIÓN A SUPABASE
########################
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase_client = init_connection()

########################
# FUNCIÓN: DASHBOARD
########################
def show_dashboard():
    st.header("Dashboard Principal")

    # Ejemplo: cargar contratos y facturas
    contratos_resp = supabase_client.table("contratos").select("*").execute()
    df_contratos = pd.DataFrame(contratos_resp.data or [])

    facturas_resp = supabase_client.table("facturas").select("*").execute()
    df_facturas = pd.DataFrame(facturas_resp.data or [])

    if df_contratos.empty and df_facturas.empty:
        st.warning("No se han encontrado datos en la BD.")
        return

    # Calcular métricas
    num_contratos = len(df_contratos)
    num_facturas = len(df_facturas)
    df_facturas["total"] = pd.to_numeric(df_facturas["total"], errors="coerce").fillna(0)
    total_facturado = df_facturas["total"].sum()

    # Sección de métricas en columnas
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Contratos Totales", num_contratos)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Facturas Totales", num_facturas)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Facturado (€)", f"{total_facturado:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Mostrar tabla de contratos
    st.subheader("Lista de Contratos")
    if df_contratos.empty:
        st.info("No hay contratos para mostrar.")
    else:
        st.dataframe(df_contratos)

    # Mostrar tabla de facturas y gráfica
    st.subheader("Lista de Facturas")
    if df_facturas.empty:
        st.info("No hay facturas para mostrar.")
        return
    st.dataframe(df_facturas)

    # Gráfica: Facturado por Contrato
    fig = px.bar(
        df_facturas,
        x="contrato_id",
        y="total",
        color="contrato_id",
        title="Facturación por Contrato",
        labels={"contrato_id": "ID Contrato", "total": "Importe (€)"}
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

########################
# FUNCIÓN: DOCUMENTOS
########################
def show_documentos():
    st.header("Documentos Asociados")
    st.write("Visualiza aquí los documentos (PDF) que hayas cargado en la BD.")

    resp_docs = supabase_client.table("documentos").select("*").execute()
    df_docs = pd.DataFrame(resp_docs.data or [])
    if df_docs.empty:
        st.warning("No hay documentos registrados.")
        return

    # Podrías agregar un filtro por contrato o factura
    st.dataframe(df_docs)

    st.markdown("""
    #### Descarga de Documentos
    - Si guardaste la URL (en una columna `url`), podrías mostrar un enlace de descarga.
    - Ejemplo:
    """)

    for i, row in df_docs.iterrows():
        nombre = row.get("nombre_archivo", "doc.pdf")
        url = row.get("url", None)
        if url:
            st.markdown(f"- **{nombre}**: [Abrir/Descargar]({url})")
        else:
            st.markdown(f"- **{nombre}** (Sin URL)")

########################
# FUNCIÓN: CHATBOT
########################
def show_chatbot():
    st.header("Chatbot con RAG (Vista Estética)")

    # Pedimos la clave de OpenAI
    openai_api_key = st.secrets.get("OPENAI_API_KEY")
    if not openai_api_key:
        st.error("No se ha configurado la clave OPENAI_API_KEY en secrets.")
        return

    # Iniciamos un contenedor para el historial
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    st.write("Haz tu pregunta sobre contratos/facturas. Ejemplo:")
    st.info("“¿Cuánto hemos gastado con American Tower en 2024?”")

    user_input = st.text_input("Tu pregunta:", "")
    if st.button("Enviar"):
        if user_input.strip():
            # Llamar a tu pipeline RAG
            # respuesta = process_user_question(supabase_client, user_input, openai_api_key)
            # O simular:
            respuesta = "Esta es una respuesta simulada. Integra aquí tu pipeline RAG."
            
            # Guardar en el historial
            st.session_state["chat_history"].append(("user", user_input))
            st.session_state["chat_history"].append(("bot", respuesta))

    # Mostrar historial de chat
    st.subheader("Historial de Conversación")
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for role, msg in st.session_state["chat_history"]:
            if role == "user":
                st.markdown(f'<div class="user-message">{msg}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-message">{msg}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

########################
# MAIN
########################
def main():
    # Barra lateral con info o branding
    st.sidebar.image("https://img1.wsimg.com/isteam/ip/5fadffce-9442-4e9d-9694-b276e29b2ea9/Logo%20mayores.ai.jpg/:/rs=w:292,h:92,cg:true,m/cr=w:292,h:92/qt=q:100/ll", 
                    width=100)
    st.sidebar.title("POC Residencias")
    st.sidebar.write("Selección de página:")

    # Crearemos tabs en vez de radio
    tab_names = ["Dashboard", "Documentos", "Chatbot"]
    selected_tab = st.sidebar.radio("", tab_names)

    if selected_tab == "Dashboard":
        show_dashboard()
    elif selected_tab == "Documentos":
        show_documentos()
    else:
        show_chatbot()

if __name__ == "__main__":
    main()
