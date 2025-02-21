import streamlit as st
import pandas as pd
import plotly.express as px
import json
import fitz  # PyMuPDF para manejar PDFs
from supabase import create_client
from rag.pipeline import process_user_question
from rag.db_queries import get_contratos, get_facturas, top_conceptos_global

st.set_page_config(page_title="POC Residencias", layout="wide")

# 📌 Inicialización de Supabase
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase_client = init_connection()

# 📌 Función para Formatear las Respuestas del Chatbot
def formatear_respuesta(respuesta):
    if isinstance(respuesta, list):  
        return "<ul style='padding-left: 20px;'>" + "".join([f"<li><b>{item}</b></li>" for item in respuesta]) + "</ul>"
    if isinstance(respuesta, pd.DataFrame) and not respuesta.empty:
        st.subheader("📊 Resultado en Tabla")
        st.dataframe(respuesta.style.format("{:.2f}"))  
        return ""
    if isinstance(respuesta, str) and len(respuesta.split()) < 10:
        return f"**{respuesta}**"  
    return respuesta.replace("-", "•").replace("\n", "<br>")

# 🏠 Dashboard General con Pestañas y Gráficos Restaurados
def vista_dashboard():
    st.subheader("📊 Dashboard Residencias")
    
    # Cargar datos
    df_contr = get_contratos(supabase_client)
    df_fact = get_facturas(supabase_client)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📑 Visión General", "🏡 Análisis por Residencia", "📈 Top Conceptos"])

    with tab1:
        st.metric("📄 Facturas Totales", len(df_fact))
        st.metric("📑 Contratos Totales", len(df_contr))
        df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
        st.metric("💰 Total Facturado", f"{df_fact['total'].sum():,.2f} €")
        st.dataframe(df_contr)
        st.dataframe(df_fact)

    with tab2:
        centros = df_contr["centro"].dropna().unique().tolist()
        sel = st.selectbox("🏠 Selecciona una Residencia:", ["(Todas)"] + centros)
        
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

    with tab3:
        df_top = top_conceptos_global(supabase_client)
        if df_top.empty:
            st.warning("⚠️ No hay datos.")
        else:
            st.dataframe(df_top.head(10))
            fig = px.bar(df_top.head(10), x="concepto", y="total", title="🏆 Top Conceptos")
            st.plotly_chart(fig, use_container_width=True)

# 📂 Chat con Archivos Optimizado (10K tokens)
def vista_chat_archivos():
    st.header("📂 Chat con Archivos")

    uploaded_file = st.file_uploader("📤 Sube un archivo PDF o JSON", type=["json", "pdf"])
    file_content = None

    if uploaded_file:
        file_extension = uploaded_file.name.split(".")[-1].lower()

        try:
            if file_extension == "pdf":
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                file_content = "\n".join([page.get_text("text") for page in doc])

            elif file_extension == "json":
                file_content = json.load(uploaded_file)

            if file_content:
                st.subheader("🔍 Vista previa del contenido")
                st.text(file_content[:1000] if isinstance(file_content, str) else json.dumps(file_content, indent=2)[:1000])
            else:
                st.warning("⚠️ El archivo no contiene texto válido.")

        except Exception as e:
            st.error(f"⚠️ Error al procesar el archivo: {str(e)}")
            return

    # 📌 Chatbot con el contenido cargado
    st.subheader("🤖 Chat con el Archivo")
    if "chat_history_files" not in st.session_state:
        st.session_state["chat_history_files"] = []

    user_input = st.text_input("✍️ Escribe tu pregunta:")

    if st.button("Enviar") and file_content:
        openai_api_key = st.secrets.get("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("⚠️ Falta `OPENAI_API_KEY` en `secrets.toml`.")
        else:
            query = f"Con base en el siguiente contenido, responde: {user_input}\n\n{file_content[:10000]}"  
            st.write("🛠 Enviando consulta al chatbot:", query[:1000])

            try:
                resp = process_user_question(None, query, openai_api_key)
                resp_formatted = formatear_respuesta(resp)
                st.session_state["chat_history_files"].insert(0, ("Usuario", user_input))
                st.session_state["chat_history_files"].insert(0, ("Chatbot 🤖", resp_formatted))
            except Exception as e:
                st.error(f"⚠️ Error al procesar la respuesta del chatbot: {str(e)}")

# 🤖 Chatbot con RAG
def vista_chatbot():
    st.header("💬 Chatbot Residencias")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_input = st.text_input("✍️ Escribe tu pregunta:")

    if st.button("Enviar"):
        openai_api_key = st.secrets.get("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("⚠️ Falta `OPENAI_API_KEY` en secrets.")
        else:
            resp = process_user_question(supabase_client, user_input, openai_api_key)
            resp_formatted = formatear_respuesta(resp)  
            st.session_state["chat_history"].insert(0, ("Usuario", user_input))
            st.session_state["chat_history"].insert(0, ("Chatbot 🤖", resp_formatted))

    st.subheader("📝 Historial de Conversación")
    with st.container():
        for r, m in st.session_state["chat_history"]:
            st.markdown(f"<div style='background-color: #f8f9fa; border-left: 5px solid #dc3545; padding: 10px; border-radius: 10px; margin: 5px 0; font-size: 14px;'><b>{r}</b>: {m}</div>", unsafe_allow_html=True)

# 🎛 Navegación Principal
def main():
    st.sidebar.title("📌 POC Residencias")
    menu = ["Dashboard", "Chatbot", "Chat con Archivos"]
    sel = st.sidebar.radio("📍 Navegación", menu)

    if sel == "Dashboard":
        vista_dashboard()
    elif sel == "Chatbot":
        vista_chatbot()
    elif sel == "Chat con Archivos":
        vista_chat_archivos()

if __name__ == "__main__":
    main()
