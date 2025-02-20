# rag/db_queries.py
import datetime
from supabase import Client
import pandas as pd

def get_invoices_by_year(supabase_client: Client, year: int):
    """
    Retorna todas las facturas cuyo 'fecha_factura' cae en el año indicado.
    Filtrado localmente para simplificar (pudieras usar un RPC).
    """
    resp = supabase_client.table("facturas").select("*").execute()
    all_invoices = resp.data if resp.data else []

    filtered = []
    for inv in all_invoices:
        fecha = inv.get("fecha_factura")  # asume formato "YYYY-MM-DD"
        if fecha and len(fecha) >= 4:
            # parse year
            if fecha.startswith(str(year)):
                filtered.append(inv)
    return filtered

def sum_invoices_total(invoices):
    """
    Suma el campo 'total' en la lista de facturas.
    """
    total_sum = 0
    for inv in invoices:
        val = inv.get("total", 0)
        try:
            total_sum += float(val)
        except:
            pass
    return total_sum

def count_invoices(invoices):
    """
    Retorna la cantidad de facturas en la lista.
    """
    return len(invoices)

def get_contratos(supabase_client: Client) -> pd.DataFrame:
    resp = supabase_client.table("contratos").select("*").execute()
    data = resp.data if resp.data else []
    return pd.DataFrame(data)

def get_facturas(supabase_client: Client) -> pd.DataFrame:
    resp = supabase_client.table("facturas").select("*").execute()
    data = resp.data if resp.data else []
    return pd.DataFrame(data)