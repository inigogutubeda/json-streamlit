# rag/db_queries.py

import pandas as pd
import streamlit as st
from supabase import Client
from datetime import datetime

@st.cache_data
def get_contratos(supabase_client: Client) -> pd.DataFrame:
    """ Obtiene todos los contratos de la base de datos """
    resp = supabase_client.table("contratos").select("*").execute()
    return pd.DataFrame(resp.data or [])

@st.cache_data
def get_facturas(supabase_client: Client) -> pd.DataFrame:
    """ Obtiene todas las facturas de la base de datos """
    resp = supabase_client.table("facturas").select("*").execute()
    return pd.DataFrame(resp.data or [])

def get_proveedores(supabase_client: Client) -> pd.DataFrame:
    """ Obtiene todos los proveedores de la base de datos """
    resp = supabase_client.table("proveedores").select("*").execute()
    return pd.DataFrame(resp.data or [])

########################################
# 🆕 NUEVAS FUNCIONES PARA EL RAG
########################################

def top_residencias_por_gasto(supabase_client: Client) -> str:
    """ Retorna las residencias con mayor gasto total en facturas. """
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return "No hay facturas registradas."

    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
    df_group = df_fact.groupby("centro")["total"].sum().reset_index()
    df_group = df_group.sort_values("total", ascending=False).head(5)

    lines = [f"- {row['centro']}: {row['total']:.2f} €" for _, row in df_group.iterrows()]
    return f"Las residencias con mayor gasto son:\n" + "\n".join(lines)


def analisis_gastos_mensuales(supabase_client: Client, year: int) -> str:
    """ Retorna el gasto mensual total en un año específico. """
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return "No hay facturas registradas."

    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["year"] = df_fact["fecha_factura"].dt.year
    df_fact["month"] = df_fact["fecha_factura"].dt.month
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)

    df_fact = df_fact[df_fact["year"] == year]
    df_group = df_fact.groupby("month")["total"].sum().reset_index()
    
    if df_group.empty:
        return f"No hay registros de gasto en {year}."

    lines = [f"- Mes {row['month']}: {row['total']:.2f} €" for _, row in df_group.iterrows()]
    return f"Análisis de gasto mensual en {year}:\n" + "\n".join(lines)


def facturas_pendientes(supabase_client: Client) -> str:
    """ Retorna las facturas que aún no han sido pagadas. """
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return "No hay facturas registradas."

    df_fact_pendientes = df_fact[df_fact["fecha_pago"].isnull()]
    if df_fact_pendientes.empty:
        return "No hay facturas pendientes de pago."

    lines = [f"- Factura '{row['numero_factura']}' por {row['total']} € emitida el {row['fecha_factura']}"
             for _, row in df_fact_pendientes.iterrows()]
    return f"Facturas pendientes de pago:\n" + "\n".join(lines)


def proveedor_con_mayor_gasto(supabase_client: Client) -> str:
    """ Retorna el proveedor con mayor gasto total en facturas. """
    df_fact = get_facturas(supabase_client)
    df_contr = get_contratos(supabase_client)
    df_prov = get_proveedores(supabase_client)

    if df_fact.empty or df_contr.empty or df_prov.empty:
        return "No hay registros suficientes para calcular el proveedor con mayor gasto."

    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
    
    df_merge = df_fact.merge(df_contr, left_on="contrato_id", right_on="id", suffixes=("_fact", "_contr"))
    df_merge = df_merge.merge(df_prov, left_on="proveedor_id", right_on="id", suffixes=("_contr", "_prov"))

    df_group = df_merge.groupby("nombre_proveedor")["total"].sum().reset_index()
    df_group = df_group.sort_values("total", ascending=False)

    if df_group.empty:
        return "No se encontraron proveedores con facturas registradas."

    top = df_group.iloc[0]
    return f"El proveedor con mayor gasto es {top['nombre_proveedor']} con un total de {top['total']:.2f} €."


########################################
# 🔄 FUNCIONES EXISTENTES MEJORADAS
########################################

def facturas_mas_elevadas(supabase_client: Client, top_n: int = 5) -> str:
    """ Retorna las facturas con el mayor importe. """
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return "No hay facturas registradas."

    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
    df_fact = df_fact.sort_values("total", ascending=False).head(top_n)

    lines = [f"- Factura '{row['numero_factura']}' por {row['total']} €" for _, row in df_fact.iterrows()]
    return f"Las {top_n} facturas más elevadas son:\n" + "\n".join(lines)


def ranking_proveedores_por_importe(supabase_client: Client, limit: int = 5, year: int = None) -> str:
    """ Retorna un ranking de los proveedores con mayor importe facturado. """
    df_fact = get_facturas(supabase_client)
    df_contr = get_contratos(supabase_client)
    df_prov = get_proveedores(supabase_client)

    if df_fact.empty or df_contr.empty or df_prov.empty:
        return "No hay registros suficientes."

    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)

    if year:
        df_fact["year"] = df_fact["fecha_factura"].dt.year
        df_fact = df_fact[df_fact["year"] == year]

    df_merge = df_fact.merge(df_contr, left_on="contrato_id", right_on="id", suffixes=("_fact", "_contr"))
    df_merge = df_merge.merge(df_prov, left_on="proveedor_id", right_on="id", suffixes=("_contr", "_prov"))

    df_group = df_merge.groupby("nombre_proveedor")["total"].sum().reset_index()
    df_group = df_group.sort_values("total", ascending=False).head(limit)

    if df_group.empty:
        return "No se encontraron proveedores con facturas registradas."

    lines = [f"- {row['nombre_proveedor']}: {row['total']:.2f} €" for _, row in df_group.iterrows()]
    return "Ranking de proveedores por importe:\n" + "\n".join(lines)
<<<<<<< HEAD

def top_conceptos_global(supabase_client: Client) -> pd.DataFrame:
    """
    Retorna un ranking de conceptos con sum(total).
    """
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return pd.DataFrame()

    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
    df_group = df_fact.groupby("concepto")["total"].sum().reset_index()
    df_group = df_group.sort_values("total", ascending=False)
    return df_group
=======
>>>>>>> parent of b54d77b (Revert a version antigua)
