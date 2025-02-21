import streamlit as st
import pandas as pd
import plotly.express as px
import json
import fitz  # PyMuPDF para manejar PDFs
import openai
from supabase import create_client
from rag.pipeline import process_user_question
from rag.db_queries import get_contratos, get_facturas, top_conceptos_global
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

st.set_page_config(page_title="POC Residencias", layout="wide")

# 📌 Inicialización de Supabase
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase_client = init_connection()

# 📌 Función para Generar Embeddings con OpenAI
def generar_embedding(texto):
    openai_api_key = st.secrets.get("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.embeddings.create(
        model="text-embedding-ada-002",  
        input=texto
    )
    return response["data"][0]["embedding"]

# 📌 Función para Hacer Chunking del Documento
def chunk_text(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# 📌 Chat con Archivos usando Chunking + Embeddings
def vista_chat_archivos():
    st.header("📂 Chat con Archivos")

    uploaded_file = st.file_uploader("📤 Sube un archivo PDF o JSON", type=["json", "pdf"])
    if "document_chunks" not in st.session_state:
        st.session_state["document_chunks"] = []
        st.session_state["chunk_embeddings"] = []

    if uploaded_file:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        text_content = ""

        try:
            if file_extension == "pdf":
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text_content = "\n".join([page.get_text("text") for page in doc])

            elif file_extension == "json":
                text_content = json.dumps(json.load(uploaded_file), indent=2)

            if text_content:
                st.subheader("🔍 Vista previa del contenido")
                st.text(text_content[:1000])
                
                # 🔹 Hacer chunking y almacenar embeddings en caché
                chunks = chunk_text(text_content, chunk_size=500)
                chunk_embeddings = [generar_embedding(chunk) for chunk in chunks]

                st.session_state["document_chunks"] = chunks
                st.session_state["chunk_embeddings"] = chunk_embeddings

                st.success("✅ Documento procesado correctamente.")

            else:
                st.warning("⚠️ El archivo no contiene texto válido.")

        except Exception as e:
            st.error(f"⚠️ Error al procesar el archivo: {str(e)}")
            return

    # 📌 Chatbot con Embeddings
    st.subheader("🤖 Chat con el Archivo")
    if "chat_history_files" not in st.session_state:
        st.session_state["chat_history_files"] = []

    user_input = st.text_input("✍️ Escribe tu pregunta:")

    if st.button("Enviar") and st.session_state["document_chunks"]:
        openai_api_key = st.secrets.get("OPENAI_API_KEY")
        if not openai_api_key:
            st.error("⚠️ Falta `OPENAI_API_KEY` en `secrets.toml`.")
        else:
            # 🔍 Generar embedding de la pregunta
            query_embedding = generar_embedding(user_input)
            
            # 🔍 Comparar con embeddings de los chunks
            similarities = cosine_similarity([query_embedding], st.session_state["chunk_embeddings"])[0]
            
            # 🔍 Seleccionar los 3 chunks más relevantes
            top_chunks = [st.session_state["document_chunks"][i] for i in np.argsort(similarities)[-3:]]

            query_context = "\n".join(top_chunks)

            query = f"Con base en el siguiente contenido relevante, responde: {user_input}\n\n{query_context}"
            
            try:
                resp = process_user_question(None, query, openai_api_key)
                st.session_state["chat_history_files"].insert(0, ("Usuario", user_input))
                st.session_state["chat_history_files"].insert(0, ("Chatbot 🤖", resp))
            except Exception as e:
                st.error(f"⚠️ Error al procesar la respuesta del chatbot: {str(e)}")

# 📌 Dashboard con Pestañas y Gráficos
def vista_dashboard():
    st.subheader("📊 Dashboard Residencias")
    
    df_contr = get_contratos(supabase_client)
    df_fact = get_facturas(supabase_client)

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

# 📌 Chatbot con RAG
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
            st.session_state["chat_history"].insert(0, ("Usuario", user_input))
            st.session_state["chat_history"].insert(0, ("Chatbot 🤖", resp))

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
