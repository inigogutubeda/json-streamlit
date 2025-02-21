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

def top_conceptos_global(supabase_client: Client) -> pd.DataFrame:
    """
    Para el dashboard (ranking de conceptos).
    """
    df_f = get_facturas(supabase_client)
    if df_f.empty:
        return pd.DataFrame()
    df_f["total"] = pd.to_numeric(df_f["total"], errors="coerce").fillna(0)
    df_group = df_f.groupby("concepto")["total"].sum().reset_index()
    df_group = df_group.sort_values("total", ascending=False)
    return df_group
