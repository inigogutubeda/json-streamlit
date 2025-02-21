import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from rag.pipeline import process_user_question
from rag.db_queries import get_contratos, get_facturas, top_conceptos_global
import fitz  # PyMuPDF
import json

st.set_page_config(page_title="POC Residencias", layout="wide")

# 📌 Inicialización de Supabase
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase_client = init_connection()

# 📂 Nueva Página: Chat con Archivos (PDF o JSON) con PyMuPDF
def vista_chat_archivos():
    st.header("📂 Chat con Archivos")

    uploaded_file = st.file_uploader("📤 Sube un archivo PDF o JSON", type=["json", "pdf"])
    file_content = None

    if uploaded_file:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        
        if file_extension == "pdf":
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            file_content = "\n".join([page.get_text("text") for page in doc])
            st.subheader("🔍 Vista previa del contenido extraído")
            st.text(file_content[:1000])  

        elif file_extension == "json":
            try:
                file_content = json.load(uploaded_file)
                st.subheader("🔍 Vista previa del JSON cargado")
                st.json(file_content)
            except json.JSONDecodeError:
                st.error("⚠️ Error al leer el JSON. Asegúrate de que el formato es correcto.")

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
            chat_context = file_content if isinstance(file_content, str) else json.dumps(file_content, indent=2)
            query = f"Con base en el siguiente contenido, responde: {user_input}\n\n{chat_context}"

            resp = process_user_question(None, query, openai_api_key)
            st.session_state["chat_history_files"].insert(0, ("Usuario", user_input))
            st.session_state["chat_history_files"].insert(0, ("Chatbot 🤖", resp))

    st.subheader("📝 Historial de Conversación")
    with st.container():
        for r, m in st.session_state["chat_history_files"]:
            st.markdown(f"<div style='background-color: #f8f9fa; border-left: 5px solid #dc3545; padding: 10px; border-radius: 10px; margin: 5px 0; font-size: 14px;'><b>{r}</b>: {m}</div>", unsafe_allow_html=True)

# 🎛 Navegación Principal
def main():
    st.sidebar.title("📌 POC Residencias")
    menu = ["Dashboard", "Chatbot", "Chat con Archivos"]
    sel = st.sidebar.radio("📍 Navegación", menu)

    if sel == "Chat con Archivos":
        vista_chat_archivos()

if __name__ == "__main__":
    main()
