# rag/db_queries.py
import pandas as pd
from supabase import Client

def get_proveedores(supabase_client: Client) -> pd.DataFrame:
    """
    Retorna DataFrame con todos los proveedores.
    """
    resp = supabase_client.table("proveedores").select("*").execute()
    data = resp.data or []
    return pd.DataFrame(data)

def get_contratos(supabase_client: Client) -> pd.DataFrame:
    """
    Retorna DataFrame con todos los contratos.
    """
    resp = supabase_client.table("contratos").select("*").execute()
    data = resp.data or []
    return pd.DataFrame(data)

def get_facturas(supabase_client: Client) -> pd.DataFrame:
    """
    Retorna DataFrame con todas las facturas.
    """
    resp = supabase_client.table("facturas").select("*").execute()
    data = resp.data or []
    return pd.DataFrame(data)

def get_facturas_by_proveedor_and_year(supabase_client: Client, proveedor_str: str, year: int) -> pd.DataFrame:
    """
    Filtra facturas por un proveedor (buscado por substring en su 'nombre_proveedor')
    y por año en 'fecha_factura'.

    - proveedor_str: texto a buscar en nombre_proveedor
    - year: año a filtrar
    """
    df_prov = get_proveedores(supabase_client)
    if df_prov.empty:
        return pd.DataFrame()

    # Creamos columna en minúsculas para buscar
    df_prov["nombre_lower"] = df_prov["nombre_proveedor"].str.lower()
    match = df_prov[df_prov["nombre_lower"].str.contains(proveedor_str.lower())]
    if match.empty:
        return pd.DataFrame()

    # IDs del proveedor
    prov_ids = match["id"].unique().tolist()

    # Contratos asociados
    df_contr = get_contratos(supabase_client)
    df_contr = df_contr[df_contr["proveedor_id"].isin(prov_ids)]
    if df_contr.empty:
        return pd.DataFrame()

    contrato_ids = df_contr["id"].unique().tolist()

    # Facturas asociadas
    df_fact = get_facturas(supabase_client)
    df_fact = df_fact[df_fact["contrato_id"].isin(contrato_ids)]

    # Filtrar por año
    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["year"] = df_fact["fecha_factura"].dt.year
    df_fact = df_fact[df_fact["year"] == year]

    return df_fact.drop(columns=["year"], errors="ignore")
