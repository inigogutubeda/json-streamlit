# rag/db_queries.py

import pandas as pd
from supabase import Client

def get_contratos(supabase_client: Client) -> pd.DataFrame:
    resp = supabase_client.table("contratos").select("*").execute()
    return pd.DataFrame(resp.data or [])

def get_facturas(supabase_client: Client):
    resp = supabase_client.table("facturas").select("*").execute()
    return pd.DataFrame(resp.data or [])


def facturas_importe_mayor(supabase_client: Client, importe: float) -> str:
    """
    Retorna un resumen de cuántas facturas tienen total > importe y la suma total.
    """
    df = get_facturas(supabase_client)
    if df.empty:
        return "No hay facturas en la base de datos."

    df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
    if df_fact.empty:
        return None

    row_max = df_fact.loc[df_fact["total"].idxmax()]
    return row_max

def ranking_proveedores_por_centro(supabase_client: Client, centro_str=None, year=None) -> pd.DataFrame:
    """
    Ejemplo: ranking de gastos por proveedor en un centro (Residencia N, Fundación X) y (opcional) en un año.
    """
    df_contr = get_contratos(supabase_client)
    df_fact = get_facturas(supabase_client)
    if df_contr.empty or df_fact.empty:
        return pd.DataFrame()

    # Filtramos por centro si hay
    if centro_str:
        df_contr = df_contr[df_contr["centro"].str.lower() == centro_str.lower()]

    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["year"] = df_fact["fecha_factura"].dt.year

    if year:
        df_fact = df_fact[df_fact["year"] == year]

    # Merge
    df_merge = df_fact.merge(df_contr, left_on="contrato_id", right_on="id", suffixes=("_fact", "_contr"))
    df_merge["total"] = pd.to_numeric(df_merge["total"], errors="coerce").fillna(0)

    # Agrupamos por proveedor_id (que está en df_contr.proveedor_id)
    df_rank = df_merge.groupby("proveedor_id")["total"].sum().reset_index()
    df_rank = df_rank.sort_values("total", ascending=False)

    # Si quieres el nombre del proveedor, puedes load 'proveedores' y merge:
    resp_prov = supabase_client.table("proveedores").select("*").execute()
    df_prov = pd.DataFrame(resp_prov.data or [])

    df_rank = df_rank.merge(df_prov, left_on="proveedor_id", right_on="id", suffixes=(None, "_prov"))
    # df_rank tiene columns: proveedor_id, total, id, cif_proveedor, nombre_proveedor...
    df_rank = df_rank[["proveedor_id", "nombre_proveedor", "total"]].sort_values("total", ascending=False)

    return df_rank

def resumen_residencia(supabase_client: Client, centro_str: str):
    """
    Devuelve un DF con facturas y otra info para un centro en particular.
    O lo que quieras (contratos, total...). 
    """
    df_contr = get_contratos(supabase_client)
    df_fact = get_facturas(supabase_client)

    df_contr_centro = df_contr[df_contr["centro"].str.lower() == centro_str.lower()]
    if df_contr_centro.empty:
        return None

    cids = df_contr_centro["id"].unique().tolist()
    df_fact_centro = df_fact[df_fact["contrato_id"].isin(cids)]
    df_fact_centro["total"] = pd.to_numeric(df_fact_centro["total"], errors="coerce").fillna(0)
    return {
        "contratos": df_contr_centro,
        "facturas": df_fact_centro,
        "total_gasto": df_fact_centro["total"].sum()
    }

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
