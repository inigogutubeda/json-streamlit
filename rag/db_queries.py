# rag/db_queries.py

import pandas as pd
import streamlit as st
from supabase import Client
from datetime import datetime

@st.cache_data
def get_contratos(supabase_client: Client) -> pd.DataFrame:
    resp = supabase_client.table("contratos").select("*").execute()
    return pd.DataFrame(resp.data or [])

@st.cache_data
def get_facturas(supabase_client: Client) -> pd.DataFrame:
    resp = supabase_client.table("facturas").select("*").execute()
    return pd.DataFrame(resp.data or [])


########################################
# Funciones existentes
########################################

def facturas_importe_mayor(supabase_client: Client, importe: float) -> str:
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return "No hay facturas registradas."

    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
    df_fil = df_fact[df_fact["total"] > importe]
    if df_fil.empty:
        return f"No hay facturas con importe mayor a {importe:.2f}."
    suma = df_fil["total"].sum()
    return (f"Encontré {len(df_fil)} facturas con importe mayor a {importe:.2f}. "
            f"La suma de esas facturas es {suma:.2f}.")

def proveedor_mas_contratos(supabase_client: Client) -> str:
    df_contr = get_contratos(supabase_client)
    if df_contr.empty:
        return "No hay contratos registrados."

    df_group = df_contr.groupby("proveedor_id").size().reset_index(name="num_contratos")
    resp_prov = supabase_client.table("proveedores").select("*").execute()
    df_prov = pd.DataFrame(resp_prov.data or [])
    df_merge = df_group.merge(df_prov, left_on="proveedor_id", right_on="id")
    df_merge = df_merge.sort_values("num_contratos", ascending=False)
    if df_merge.empty:
        return "No encontré proveedores."

    lines = []
    for _, row in df_merge.iterrows():
        lines.append(f"- {row['nombre_proveedor']}: {row['num_contratos']} contratos")
    top = df_merge.iloc[0]
    return ("Ranking de proveedores por número de contratos:\n"
            + "\n".join(lines)
            + f"\n\nEl que más tiene es {top['nombre_proveedor']} con {top['num_contratos']}.")

def factura_mas_reciente(supabase_client: Client) -> str:
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return "No hay facturas registradas."

    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact = df_fact.dropna(subset=["fecha_factura"])
    if df_fact.empty:
        return "No hay facturas con fecha válida."

    row = df_fact.loc[df_fact["fecha_factura"].idxmax()]
    return (f"La factura más reciente es '{row['numero_factura']}' "
            f"(fecha: {row['fecha_factura']}) con total {row['total']}. "
            f"Concepto: {row.get('concepto','(sin concepto)')}")

def gasto_en_rango_fechas(supabase_client: Client, fecha_inicio: str, fecha_fin: str) -> str:
    fmt = "%d/%m/%Y"
    try:
        fi = datetime.strptime(fecha_inicio, fmt)
        ff = datetime.strptime(fecha_fin, fmt)
    except ValueError:
        return "No pude parsear las fechas. Usa dd/mm/yyyy."

    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return "No hay facturas."

    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
    df_fact = df_fact.dropna(subset=["fecha_factura"])

    df_fil = df_fact[(df_fact["fecha_factura"] >= fi) & (df_fact["fecha_factura"] <= ff)]
    suma = df_fil["total"].sum()
    return f"El gasto total entre {fecha_inicio} y {fecha_fin} es {suma:.2f}."

def contratos_vencen_antes_de(supabase_client: Client, fecha_limite: str) -> str:
    fmt = "%d/%m/%Y"
    try:
        fl = datetime.strptime(fecha_limite, fmt)
    except ValueError:
        return "No pude parsear la fecha (dd/mm/yyyy)."

    df_contr = get_contratos(supabase_client)
    if df_contr.empty:
        return "No hay contratos."

    df_contr["fecha_vencimiento"] = pd.to_datetime(df_contr["fecha_vencimiento"], errors="coerce")
    df_contr = df_contr.dropna(subset=["fecha_vencimiento"])
    df_fil = df_contr[df_contr["fecha_vencimiento"] < fl]
    if df_fil.empty:
        return f"Ningún contrato vence antes de {fecha_limite}."
    lines = []
    for _, row in df_fil.iterrows():
        lines.append(f"- Contrato ID {row['id']}, centro={row['centro']}, vence={row['fecha_vencimiento']}")
    return (f"Hay {len(df_fil)} contratos que vencen antes de {fecha_limite}:\n" + "\n".join(lines))


########################################
# NUEVAS FUNCIONES
########################################

def gasto_proveedor_en_year(supabase_client: Client, proveedor: str, year: int) -> str:
    """
    Filtra facturas de un proveedor (buscando substring en 'nombre_proveedor')
    y el año (en 'fecha_factura'), sumando 'total'.
    """
    # 1) Buscar ID del proveedor por substring
    resp_prov = supabase_client.table("proveedores").select("*").execute()
    df_prov = pd.DataFrame(resp_prov.data or [])
    if df_prov.empty:
        return "No hay proveedores."

    df_prov["nombre_lower"] = df_prov["nombre_proveedor"].str.lower()
    match = df_prov[df_prov["nombre_lower"].str.contains(proveedor.lower())]
    if match.empty:
        return f"No encontré un proveedor que coincida con '{proveedor}'."

    # Podría haber varios, cogemos todos
    prov_ids = match["id"].unique().tolist()

    # 2) Contratos con esos proveedores
    df_contr = get_contratos(supabase_client)
    df_contr = df_contr[df_contr["proveedor_id"].isin(prov_ids)]
    if df_contr.empty:
        return f"No hay contratos con proveedor '{proveedor}'."

    cids = df_contr["id"].unique().tolist()

    # 3) Facturas de esos contratos en el year
    df_fact = get_facturas(supabase_client)
    df_fact = df_fact[df_fact["contrato_id"].isin(cids)]
    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["year"] = df_fact["fecha_factura"].dt.year
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
    df_fact = df_fact[df_fact["year"] == year]

    if df_fact.empty:
        return f"No hay facturas de '{proveedor}' en el año {year}."

    suma = df_fact["total"].sum()
    return (f"En {year}, para el proveedor '{proveedor}', "
            f"hay {len(df_fact)} facturas con un total de {suma:.2f}.")


def facturas_mas_elevadas(supabase_client: Client, top_n: int=5) -> str:
    """
    Retorna las facturas con mayor 'total' (por defecto, top 5).
    """
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return "No hay facturas."
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
    df_fact = df_fact.sort_values("total", ascending=False).head(top_n)
    lines = []
    for _, row in df_fact.iterrows():
        lines.append(f"- Factura '{row['numero_factura']}' total={row['total']}")
    return (f"Las {top_n} facturas más elevadas son:\n" + "\n".join(lines))


def ranking_proveedores_por_importe(supabase_client: Client, limit: int=5, year: int=None) -> str:
    """
    Retorna un ranking de proveedores por el total de facturas.
    - limit: cuántos mostrar
    - year: si se especifica, filtra por ese año
    """
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return "No hay facturas."
    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
    if year:
        df_fact["year"] = df_fact["fecha_factura"].dt.year
        df_fact = df_fact[df_fact["year"] == year]

    # Contratos => para vincular a proveedores
    df_contr = get_contratos(supabase_client)
    df_merge = df_fact.merge(df_contr, left_on="contrato_id", right_on="id", suffixes=("_fact","_contr"))
    if df_merge.empty:
        return "No encontré facturas con contratos asociados."

    # Merge con proveedores
    resp_prov = supabase_client.table("proveedores").select("*").execute()
    df_prov = pd.DataFrame(resp_prov.data or [])
    df_merge = df_merge.merge(df_prov, left_on="proveedor_id", right_on="id", suffixes=("_ctr","_prov"))
    if df_merge.empty:
        return "No encontré proveedores asociados a estas facturas."

    # Agrupar por 'nombre_proveedor', sum de total
    df_rank = df_merge.groupby("nombre_proveedor")["total"].sum().reset_index()
    df_rank = df_rank.sort_values("total", ascending=False).head(limit)
    lines = []
    for _, row in df_rank.iterrows():
        lines.append(f"- {row['nombre_proveedor']}: {row['total']:.2f}")
    return ("Ranking de proveedores por importe:\n" + "\n".join(lines))

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
