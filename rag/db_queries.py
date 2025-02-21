import pandas as pd
from supabase import Client
from datetime import datetime
from datetime import timedelta

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

def get_facturas_pendientes(supabase_client: Client) -> str:
    """
    Devuelve las facturas pendientes de pago.
    """
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return "No hay facturas registradas."
    
    df_fact = df_fact[df_fact['estado'] == 'pendiente']
    if df_fact.empty:
        return "No hay facturas pendientes de pago."
    
    total_pendiente = df_fact["total"].sum()
    return f"Hay {len(df_fact)} facturas pendientes con un total de {total_pendiente:.2f} €."

def get_gastos_por_mes_categoria(supabase_client: Client) -> pd.DataFrame:
    """
    Devuelve un resumen de gastos agrupados por mes y categoría.
    """
    df_fact = get_facturas(supabase_client)
    if df_fact.empty:
        return "No hay facturas registradas."
    
    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact.dropna(subset=["fecha_factura"], inplace=True)
    df_fact["mes"] = df_fact["fecha_factura"].dt.strftime("%Y-%m")
    
    df_resumen = df_fact.groupby(["mes", "categoria"])["total"].sum().reset_index()
    return df_resumen

def get_gastos_por_residencia(supabase_client: Client, residencia: str) -> str:
    """
    Devuelve el gasto total de una residencia específica.
    """
    df_fact = get_facturas(supabase_client)
    df_contr = get_contratos(supabase_client)
    
    df_merge = df_fact.merge(df_contr, left_on="contrato_id", right_on="id")
    df_merge = df_merge[df_merge["centro"] == residencia]
    
    if df_merge.empty:
        return f"No se encontraron gastos para la residencia {residencia}."
    
    total_gasto = df_merge["total"].sum()
    return f"El gasto total para la residencia {residencia} es de {total_gasto:.2f} €."

def get_mantenimientos_pendientes(supabase_client: Client) -> str:
    """
    Retorna los mantenimientos programados en los próximos 30 días.
    """
    df_mant = supabase_client.table("mantenimientos").select("*").execute()
    df_mant = pd.DataFrame(df_mant.data or [])
    
    if df_mant.empty:
        return "No hay mantenimientos programados."
    
    df_mant["fecha_programada"] = pd.to_datetime(df_mant["fecha_programada"], errors="coerce")
    df_mant.dropna(subset=["fecha_programada"], inplace=True)
    fecha_limite = datetime.today() + timedelta(days=30)
    df_mant = df_mant[df_mant["fecha_programada"] <= fecha_limite]
    
    return f"Hay {len(df_mant)} mantenimientos programados en los próximos 30 días."

def get_proveedores_con_contratos_vigentes(supabase_client: Client) -> pd.DataFrame:
    """
    Devuelve un listado de proveedores con contratos activos.
    """
    df_contr = get_contratos(supabase_client)
    df_prov = supabase_client.table("proveedores").select("*").execute()
    df_prov = pd.DataFrame(df_prov.data or [])
    
    df_merge = df_contr.merge(df_prov, left_on="proveedor_id", right_on="id")
    df_merge = df_merge[df_merge["fecha_vencimiento"] > datetime.today().strftime("%Y-%m-%d")]
    return df_merge[["nombre_proveedor", "fecha_vencimiento"]]

def get_facturas_por_proveedor(supabase_client: Client, proveedor: str, year: int) -> str:
    """
    Retorna las facturas de un proveedor específico en un año.
    """
    df_fact = get_facturas(supabase_client)
    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["year"] = df_fact["fecha_factura"].dt.year
    df_fact = df_fact[(df_fact["year"] == year) & (df_fact["proveedor"] == proveedor)]
    
    if df_fact.empty:
        return f"No hay facturas de {proveedor} en {year}."
    
    total = df_fact["total"].sum()
    return f"El total facturado por {proveedor} en {year} es de {total:.2f} €."

def get_contratos_vencen_proximos_meses(supabase_client: Client) -> str:
    df_contr = get_contratos(supabase_client)
    df_contr["fecha_vencimiento"] = pd.to_datetime(df_contr["fecha_vencimiento"], errors="coerce")
    df_contr.dropna(subset=["fecha_vencimiento"], inplace=True)
    fecha_limite = datetime.today() + timedelta(days=180)
    df_contr = df_contr[df_contr["fecha_vencimiento"] <= fecha_limite]
    
    if df_contr.empty:
        return "No hay contratos próximos a vencer."
    
    contratos_lista = "\n".join([f"- ID {row['id']}, Centro: {row['centro']}, Vence: {row['fecha_vencimiento'].strftime('%d/%m/%Y')}" 
                                  for _, row in df_contr.iterrows()])
    
    return f"Hay {len(df_contr)} contratos que vencen en los próximos 6 meses:\n{contratos_lista}"

def get_top_centros_mayores_gastos(supabase_client: Client, year: int) -> pd.DataFrame:
    """
    Retorna los 5 centros con mayores gastos en un año.
    """
    df_fact = get_facturas(supabase_client)
    df_contr = get_contratos(supabase_client)
    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["year"] = df_fact["fecha_factura"].dt.year
    
    df_merge = df_fact.merge(df_contr, left_on="contrato_id", right_on="id")
    df_merge = df_merge[df_merge["year"] == year]
    df_top = df_merge.groupby("centro")["total"].sum().reset_index().sort_values("total", ascending=False).head(5)
    return df_top

def contrato_mas_costoso(supabase_client: Client) -> str:
    """
    Retorna el contrato con el importe más alto.
    """
    df_contr = get_contratos(supabase_client)
    if df_contr.empty:
        return "No hay contratos registrados."

    df_contr["importe"] = pd.to_numeric(df_contr["importe"], errors="coerce").fillna(0)
    contrato_top = df_contr.loc[df_contr["importe"].idxmax()]

    return (f"El contrato más costoso es con {contrato_top['centro']} por un importe de "
            f"{contrato_top['importe']:.2f} € y vence el {contrato_top['fecha_vencimiento']}.")

def facturas_de_proveedor(supabase_client: Client, proveedor: str, year: int) -> str:
    """
    Devuelve todas las facturas de un proveedor en un año específico.
    """
    df_fact = get_facturas(supabase_client)
    df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
    df_fact["year"] = df_fact["fecha_factura"].dt.year

    df_filtradas = df_fact[(df_fact["year"] == year) & (df_fact["proveedor"] == proveedor)]
    
    if df_filtradas.empty:
        return f"No hay facturas para {proveedor} en {year}."

    facturas_list = "\n".join(
        [f"- Factura {row['numero_factura']}: {row['total']} €" for _, row in df_filtradas.iterrows()]
    )
    
    return f"Facturas de {proveedor} en {year}:\n{facturas_list}"

def gasto_por_tipo_servicio(supabase_client: Client, tipo_servicio: str) -> str:
    """
    Calcula el total gastado en un tipo de servicio específico (ejemplo: 'electricidad', 'limpieza').
    """
    df_fact = get_facturas(supabase_client)
    df_contr = get_contratos(supabase_client)
    
    df_merge = df_fact.merge(df_contr, left_on="contrato_id", right_on="id")
    df_filtrados = df_merge[df_merge["tipo_servicio"].str.lower() == tipo_servicio.lower()]
    
    if df_filtrados.empty:
        return f"No hay gastos registrados en {tipo_servicio}."

    total_gasto = df_filtrados["total"].sum()
    return f"El total gastado en {tipo_servicio} es de {total_gasto:.2f} €."

def ranking_tipos_servicios(supabase_client: Client) -> str:
    """
    Muestra los tipos de servicio con mayor gasto total.
    """
    df_fact = get_facturas(supabase_client)
    df_contr = get_contratos(supabase_client)

    df_merge = df_fact.merge(df_contr, left_on="contrato_id", right_on="id")
    df_ranking = df_merge.groupby("tipo_servicio")["total"].sum().reset_index()
    df_ranking = df_ranking.sort_values("total", ascending=False)

    if df_ranking.empty:
        return "No hay datos suficientes para generar el ranking de servicios."

    ranking_list = "\n".join(
        [f"- {row['tipo_servicio']}: {row['total']:.2f} €" for _, row in df_ranking.iterrows()]
    )
    
    return f"Ranking de tipos de servicios más costosos:\n{ranking_list}"

def top_contratos_mas_costosos(supabase_client: Client) -> str:
    """
    Retorna los 3 contratos activos con mayor importe.
    """
    df_contr = get_contratos(supabase_client)
    if df_contr.empty:
        return "No hay contratos registrados."

    df_contr["importe"] = pd.to_numeric(df_contr["importe"], errors="coerce").fillna(0)
    df_top = df_contr.sort_values("importe", ascending=False).head(3)

    contratos_list = "\n".join(
        [f"- {row['centro']}: {row['importe']} € (Vence: {row['fecha_vencimiento']})" for _, row in df_top.iterrows()]
    )
    
    return f"Top 3 contratos más costosos:\n{contratos_list}"
