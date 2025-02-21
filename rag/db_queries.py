# rag/db_queries.py

import pandas as pd
from supabase import Client
from datetime import datetime

def get_contratos(supabase_client: Client):
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

    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)
    df_filtradas = df[df["total"] > importe]
    if df_filtradas.empty:
        return f"No hay facturas con importe mayor a {importe}."
    suma = df_filtradas["total"].sum()
    return (f"Encontré {len(df_filtradas)} facturas con importe mayor a {importe:.2f}. "
            f"Suma de esas facturas = {suma:.2f}.")


def proveedor_mas_contratos(supabase_client: Client) -> str:
    """
    Devuelve qué proveedor tiene más contratos y un ranking.
    """
    df_contr = get_contratos(supabase_client)
    if df_contr.empty:
        return "No hay contratos registrados."

    df_group = df_contr.groupby("proveedor_id").size().reset_index(name="num_contratos")

    # Traer proveedores
    resp_prov = supabase_client.table("proveedores").select("*").execute()
    df_prov = pd.DataFrame(resp_prov.data or [])

    df_merge = df_group.merge(df_prov, left_on="proveedor_id", right_on="id")
    df_merge = df_merge.sort_values("num_contratos", ascending=False)

    if df_merge.empty:
        return "No encontré ningún proveedor."
    
    lines = []
    for _, row in df_merge.iterrows():
        lines.append(f"- {row['nombre_proveedor']}: {row['num_contratos']} contratos")
    top = df_merge.iloc[0]
    return ("Ranking de proveedores por número de contratos:\n"
            + "\n".join(lines)
            + f"\n\nEl proveedor con más contratos es {top['nombre_proveedor']} con {top['num_contratos']}.")


def factura_mas_reciente(supabase_client: Client) -> str:
    """
    Retorna la factura con la fecha_factura más reciente.
    """
    df = get_facturas(supabase_client)
    if df.empty:
        return "No hay facturas registradas."

    df["fecha_factura"] = pd.to_datetime(df["fecha_factura"], errors="coerce")
    df = df.dropna(subset=["fecha_factura"])
    if df.empty:
        return "No hay facturas con fecha válida."

    row = df.loc[df["fecha_factura"].idxmax()]
    return (f"La factura más reciente es '{row['numero']}' con fecha {row['fecha_factura']} "
            f"y un total de {row['total']}. "
            f"Concepto: {row.get('concepto','(sin concepto)')}")


def gasto_en_rango_fechas(supabase_client: Client, fecha_inicio: str, fecha_fin: str) -> str:
    """
    Calcula la suma de facturas en [fecha_inicio, fecha_fin] (dd/mm/yyyy).
    """
    fmt = "%d/%m/%Y"
    try:
        fi = datetime.strptime(fecha_inicio, fmt)
        ff = datetime.strptime(fecha_fin, fmt)
    except ValueError:
        return "No pude parsear las fechas (usa dd/mm/yyyy)."

    df = get_facturas(supabase_client)
    if df.empty:
        return "No hay facturas registradas."
    df["fecha_factura"] = pd.to_datetime(df["fecha_factura"], errors="coerce")
    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)

    df = df.dropna(subset=["fecha_factura"])
    df_fil = df[(df["fecha_factura"] >= fi) & (df["fecha_factura"] <= ff)]

    suma = df_fil["total"].sum()
    return (f"El gasto total entre {fecha_inicio} y {fecha_fin} es de {suma:.2f}.")


def contratos_vencen_antes_de(supabase_client: Client, fecha_limite: str) -> str:
    """
    Devuelve cuántos contratos vencen antes de fecha_limite (dd/mm/yyyy) y una breve lista.
    """
    try:
        fmt = "%d/%m/%Y"
        f_lim = datetime.strptime(fecha_limite, fmt)
    except ValueError:
        return "No pude parsear la fecha (usa dd/mm/yyyy)."

    df = get_contratos(supabase_client)
    if df.empty:
        return "No hay contratos."

    df["fecha_vencimiento"] = pd.to_datetime(df["fecha_vencimiento"], errors="coerce")
    df = df.dropna(subset=["fecha_vencimiento"])
    df_fil = df[df["fecha_vencimiento"] < f_lim]

    if df_fil.empty:
        return f"No hay contratos que venzan antes de {fecha_limite}."
    
    lines = []
    for _, row in df_fil.iterrows():
        lines.append(f"- Contrato ID {row['id']} (Centro: {row['centro']}), vence: {row['fecha_vencimiento']}")
    return (f"Hay {len(df_fil)} contratos que vencen antes de {fecha_limite}:\n"
            + "\n".join(lines))
