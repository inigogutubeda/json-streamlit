# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from rag.db_queries import get_contratos, get_facturas

# Importamos nuestro pipeline RAG:
from rag.pipeline import process_user_question

def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
    return supabase

def mostrar_dashboard(supabase_client: Client):
    st.title("Dashboard - Residencias")

    # 1) Cargamos contratos y facturas
    df_contratos = get_contratos(supabase_client)
    df_facturas = get_facturas(supabase_client)

    # Si prefieres sin modular, puedes hacerlo directo:
    contratos_resp = supabase_client.table("contratos").select("*").execute()
    df_contratos = pd.DataFrame(contratos_resp.data or [])
    facturas_resp = supabase_client.table("facturas").select("*").execute()
    df_facturas = pd.DataFrame(facturas_resp.data or [])

    # 2) Mostrar Contratos
    if df_contratos.empty:
        st.warning("No hay contratos registrados en la BD.")
    else:
        st.subheader("Lista de Contratos")
        st.dataframe(df_contratos)

    # 3) Mostrar Facturas + Filtro por año
    if df_facturas.empty:
        st.warning("No hay facturas registradas en la BD.")
        return

    st.subheader("Lista de Facturas")

    # ---- PARTE A: Filtro por año (opcional) ----
    # Asumimos 'fecha_factura' está en formato YYYY-MM-DD en la BD
    # Convertimos a datetime
    df_facturas["fecha_factura"] = pd.to_datetime(df_facturas["fecha_factura"], errors="coerce")

    # Extraemos el año y lo guardamos en una columna
    df_facturas["year"] = df_facturas["fecha_factura"].dt.year

    # Preparamos un selectbox con los años detectados
    anios_disponibles = sorted(df_facturas["year"].dropna().unique().tolist())
    anio_seleccionado = st.selectbox("Filtrar facturas por año:", [None] + anios_disponibles, index=0)

    # Aplicamos el filtro si el usuario seleccionó un año
    if anio_seleccionado:
        df_facturas = df_facturas[df_facturas["year"] == anio_seleccionado]

    # Mostramos la tabla con (posible) filtrado
    st.dataframe(df_facturas)

    # ---- PARTE B: Agregaciones y gráficas ----
    # Convertimos 'total' a numérico y sumamos nulos si hay
    df_facturas["total"] = pd.to_numeric(df_facturas["total"], errors="coerce").fillna(0)

    # 1) Gráfico de barras: total por contrato
    st.subheader("Total facturado por Contrato")
    fig_contrato = px.bar(
        df_facturas,
        x="contrato_id",
        y="total",
        title="Total facturado por Contrato",
        labels={"contrato_id": "ID Contrato", "total": "Importe Facturado"}
    )
    st.plotly_chart(fig_contrato, use_container_width=True)

    # 2) Agregación por año (después de filtrar, o antes, según tu preferencia)
    st.subheader("Suma total por año (independiente del filtro)")

    # Si prefieres la suma de TODOS los datos, haz la agrupación en df_facturas original (sin filtrar).
    # Sin embargo, para la demo, la haré sobre el df_facturas filtrado actual
    df_agg_year = df_facturas.groupby("year", dropna=False)["total"].sum().reset_index()
    df_agg_year = df_agg_year.sort_values("year", ascending=True)

    st.dataframe(df_agg_year)

    fig_year = px.bar(
        df_agg_year,
        x="year",
        y="total",
        title="Facturación agrupada por año",
        labels={"year": "Año", "total": "Importe Total"}
    )
    st.plotly_chart(fig_year, use_container_width=True)

    st.info("Puedes ampliar esta sección con más métricas (p.ej. totales por proveedor, por centro, etc.)")

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
