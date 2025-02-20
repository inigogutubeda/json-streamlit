# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# Importamos nuestro pipeline RAG:
from rag.pipeline import process_user_question

def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    return supabase

def mostrar_dashboard(supabase_client: Client):
    st.title("Dashboard - Residencias")
    # ... igual que antes, lees contratos/facturas y muestras gráficas
    # (omito por brevedad)

def chatbot_rag(supabase_client: Client):
    st.title("Chatbot RAG")
    openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not openai_api_key:
        st.error("Falta OPENAI_API_KEY en secrets.")
        return

    user_input = st.text_input("Pregunta:", "")
    if st.button("Enviar"):
        respuesta = process_user_question(supabase_client, user_input, openai_api_key)
        st.success(respuesta)

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
