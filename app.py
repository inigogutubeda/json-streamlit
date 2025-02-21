import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from rag.pipeline import process_user_question
from rag.db_queries import get_contratos, get_facturas, top_conceptos_global

st.set_page_config(page_title="POC Residencias", layout="wide")

# Inicialización de conexión a Supabase
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase_client = init_connection()

# 🏠 Dashboard General
def vista_general_dashboard():
    st.subheader("📊 Visión General")
    df_contr = get_contratos(supabase_client)
    df_fact = get_facturas(supabase_client)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("📑 Contratos Totales", len(df_contr))
    with c2:
        st.metric("📄 Facturas Totales", len(df_fact))
    with c3:
        df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
        st.metric("💰 Total Facturado", f"{df_fact['total'].sum():,.2f} €")

    st.dataframe(df_contr)
    st.dataframe(df_fact)

# 🏢 Análisis por Residencia
def vista_por_residencia():
    st.subheader("🏡 Análisis por Residencia")
    df_contr = get_contratos(supabase_client)
    if df_contr.empty:
        st.warning("⚠️ No hay contratos.")
        return

    centros = df_contr["centro"].dropna().unique().tolist()
    sel = st.selectbox("🏠 Selecciona una Residencia:", ["(Todas)"]+centros)
    df_fact = get_facturas(supabase_client)
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)

    if sel != "(Todas)":
        df_contr = df_contr[df_contr["centro"] == sel]
        cids = df_contr["id"].unique().tolist()
        df_fact = df_fact[df_fact["contrato_id"].isin(cids)]
    
    st.dataframe(df_contr)
    st.dataframe(df_fact)
    suma = df_fact["total"].sum()
    st.metric(f"💵 Gasto Total en {sel}", f"{suma:,.2f} €")

    fig = px.bar(df_fact, x="numero_factura", y="total", title="📊 Facturas")
    st.plotly_chart(fig, use_container_width=True)

# 📌 Top Conceptos Facturados
def vista_top_conceptos():
    st.subheader("🏷️ Top Conceptos Facturados")
    df_top = top_conceptos_global(supabase_client)
    if df_top.empty:
        st.warning("⚠️ No hay facturas.")
        return

    st.dataframe(df_top.head(10))
    fig = px.bar(df_top.head(10), x="concepto", y="total", title="🏆 Top Conceptos")
    st.plotly_chart(fig, use_container_width=True)

# 🤖 Chatbot con mejoras visuales
# 🤖 Chatbot con Mejor Formato de Respuestas
def vista_chatbot():
    st.header("💬 Chatbot Residencias")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Input arriba del chat
    user_input = st.text_input("✍️ Escribe tu pregunta:")

    if st.button("Enviar"):
        openai_api_key = st.secrets.get("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("⚠️ Falta OPENAI_API_KEY en secrets.")
        else:
            resp = process_user_question(supabase_client, user_input, openai_api_key)
            resp_formatted = formatear_respuesta(resp)  # Aplicamos el nuevo formato
            st.session_state["chat_history"].insert(0, ("Usuario", user_input))
            st.session_state["chat_history"].insert(0, ("Chatbot 🤖", resp_formatted))

    # Historial de Conversación con Mejor Formato
    st.subheader("📝 Historial de Conversación")
    with st.container():
        for r, m in st.session_state["chat_history"]:
            if r == "Usuario":
                st.markdown(f"""
                    <div style='background-color: #d1ecf1; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                        <b>🧑‍💼 {r}</b>: {m}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='background-color: #ffffff; border-left: 5px solid #dc3545; 
                                padding: 15px; border-radius: 10px; margin: 5px 0; font-size: 14px;'>
                        {m}
                    </div>
                    """, unsafe_allow_html=True)

# 📌 Nueva Función para Mejorar el Formato de las Respuestas
def formatear_respuesta(respuesta):
    """
    Aplica formato a la respuesta para mejorar la presentación.
    - Listas estructuradas si hay múltiples elementos.
    - Tablas estilizadas si hay datos tabulares.
    - Negritas y separaciones visuales para mejorar la lectura.
    """
    if isinstance(respuesta, list):  
        return "<ul style='padding-left: 20px;'>" + "".join([f"<li><b>{item}</b></li>" for item in respuesta]) + "</ul>"

    if isinstance(respuesta, pd.DataFrame):  
        return respuesta.to_html(index=False, escape=False, border=1, justify="center")

    # Intentamos detectar si la respuesta tiene estructura tabular sin ser un DataFrame
    lineas = respuesta.split("\n")
    if all(" " in linea for linea in lineas):  # Verifica si todas las líneas tienen espacios como separación
        tabla_html = """
        <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f8f9fa;
        }
        </style>
        <table>
        """
        for i, linea in enumerate(lineas):
            columnas = linea.split()
            tabla_html += "<tr>" + "".join([f"<th>{col}</th>" if i == 0 else f"<td>{col}</td>" for col in columnas]) + "</tr>"
        tabla_html += "</table>"
        return tabla_html

    # Si no detecta formato especial, devuelve texto con mejor visualización
    return respuesta.replace("-", "•").replace("\n", "<br>")

# 🎛 Navegación Principal
def main():
    st.sidebar.title("📌 POC Residencias")
    menu = ["Dashboard", "Chatbot"]
    sel = st.sidebar.radio("📍 Navegación", menu)

    if sel == "Chatbot":
        vista_chatbot()
# 🎛 Navegación Principal
def main():
    st.sidebar.title("📌 POC Residencias")
    menu = ["Dashboard", "Chatbot"]
    sel = st.sidebar.radio("📍 Navegación", menu)

    if sel == "Dashboard":
        tabs = st.tabs(["📊 Visión General", "🏡 Por Residencia", "🏷️ Top Conceptos"])
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
