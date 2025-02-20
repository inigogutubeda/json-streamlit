# rag/db_queries.py
import pandas as pd
from supabase import Client

def get_facturas(supabase_client: Client) -> pd.DataFrame:
    resp = supabase_client.table("facturas").select("*").execute()
    data = resp.data or []
    df = pd.DataFrame(data)
    return df

def get_contratos(supabase_client: Client) -> pd.DataFrame:
    resp = supabase_client.table("contratos").select("*").execute()
    data = resp.data or []
    df = pd.DataFrame(data)
    return df

def get_proveedores(supabase_client: Client) -> pd.DataFrame:
    resp = supabase_client.table("proveedores").select("*").execute()
    data = resp.data or []
    df = pd.DataFrame(data)
    return df

def get_facturas_by_proveedor_and_year(supabase_client: Client, proveedor_str: str, year: int) -> pd.DataFrame:
    df_prov = get_proveedores(supabase_client)
    df_prov["nombre_lower"] = df_prov["nombre_proveedor"].str.lower()

    # Filtramos por substring
    match = df_prov[df_prov["nombre_lower"].str.contains(proveedor_str.lower())]
    if match.empty:
        return pd.DataFrame()

    prov_ids = match["id"].unique().tolist()

    df_contr = get_contratos(supabase_client)
    df_contr = df_contr[df_contr["proveedor_id"].isin(prov_ids)]
    if df_contr.empty:
        return pd.DataFrame()

    contrato_ids = df_contr["id"].unique().tolist()

    df_fact = get_facturas(supabase_client)
    df_fact = df_fact[df_fact["contrato_id"].isin(contrato_ids)]

    # Filtrar por año
    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["year"] = df_fact["fecha_factura"].dt.year
    df_fact = df_fact[df_fact["year"] == year]

    return df_fact.drop(columns=["year"], errors="ignore")
