# rag/db_queries.py

import pandas as pd
from supabase import Client
from datetime import datetime

def get_contratos(supabase_client: Client) -> pd.DataFrame:
    resp = supabase_client.table("contratos").select("*").execute()
    return pd.DataFrame(resp.data or [])

def get_facturas(supabase_client: Client) -> pd.DataFrame:
    resp = supabase_client.table("facturas").select("*").execute()
    return pd.DataFrame(resp.data or [])

def facturas_con_importe_mayor(supabase_client: Client, importe: float) -> pd.DataFrame:
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return pd.DataFrame()
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
    df_fact = df_fact[df_fact["total"] > importe]
    return df_fact

def proveedor_mas_contratos(supabase_client: Client) -> pd.DataFrame:
    """
    Devuelve un DF con ['proveedor_id', 'nombre_proveedor', 'num_contratos'],
    ordenado desc, para ver quien tiene más contratos.
    """
    df_contr = get_contratos(supabase_client)
    if df_contr.empty:
        return pd.DataFrame()

    # Agrupar por proveedor_id
    df_group = df_contr.groupby("proveedor_id").size().reset_index(name="num_contratos")

    # Traemos la tabla proveedores para el nombre
    resp_prov = supabase_client.table("proveedores").select("*").execute()
    df_prov = pd.DataFrame(resp_prov.data or [])

    df_merge = df_group.merge(df_prov, left_on="proveedor_id", right_on="id")
    df_merge = df_merge[["proveedor_id", "nombre_proveedor", "num_contratos"]]
    df_merge = df_merge.sort_values("num_contratos", ascending=False)
    return df_merge

def factura_mas_reciente(supabase_client: Client):
    """
    Retorna la fila con la fecha_factura más reciente.
    """
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return None

    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact = df_fact.dropna(subset=["fecha_factura"])
    if df_fact.empty:
        return None
    row = df_fact.loc[df_fact["fecha_factura"].idxmax()]
    return row

def gasto_en_rango_fechas(supabase_client: Client, fecha_inicio: str, fecha_fin: str) -> float:
    """
    Filtra facturas donde fecha_factura esté entre fecha_inicio y fecha_fin (dd/mm/yyyy).
    Suma el total.
    """
    try:
        fmt = "%d/%m/%Y"  # Ajustar si usas dd-mm-yyyy
        f_i = datetime.strptime(fecha_inicio, fmt)
        f_f = datetime.strptime(fecha_fin, fmt)
    except ValueError:
        # Si falla, devolver -1 o algo
        return -1

    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return 0

    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)

    df_fact = df_fact.dropna(subset=["fecha_factura"])
    df_filtered = df_fact[(df_fact["fecha_factura"] >= f_i) & (df_fact["fecha_factura"] <= f_f)]
    return df_filtered["total"].sum()

def contratos_vencen_antes_de(supabase_client: Client, fecha_str: str) -> pd.DataFrame:
    """
    Devuelve DF de contratos que vencen antes de fecha_str (dd/mm/yyyy).
    """
    try:
        fmt = "%d/%m/%Y"
        fecha_limite = datetime.strptime(fecha_str, fmt)
    except ValueError:
        return pd.DataFrame()

    df_contr = get_contratos(supabase_client)
    if df_contr.empty:
        return df_contr

    df_contr["fecha_vencimiento"] = pd.to_datetime(df_contr["fecha_vencimiento"], errors="coerce", format="%Y-%m-%d")
    df_contr = df_contr.dropna(subset=["fecha_vencimiento"])

    df_res = df_contr[df_contr["fecha_vencimiento"] < fecha_limite]
    return df_res

# Mantenemos las funciones previas (ranking_gastos_por_centro, factura_mas_alta_year, etc.)
# ...
