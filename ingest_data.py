# ingest_data.py

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

def parse_date(date_str):
    """
    Convierte cadenas en formato DD/MM/YYYY a YYYY-MM-DD.
    Retorna None si la cadena está vacía o es inválida.
    """
    if not date_str:
        return None

    try:
        # Asume que el string está en DD/MM/YYYY
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        # Devuelve en formato ISO (YYYY-MM-DD) válido para Postgres
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def get_or_create_proveedor(supabase: Client, cif_proveedor, nombre_proveedor, tipo_servicio):
    """
    Busca un proveedor según 'cif_proveedor' y 'nombre_proveedor'.
    Si no existe, lo crea. Devuelve el registro (dict) con su 'id'.
    """
    # Buscar si ya existe
    query = supabase.table("proveedores").select("*").eq("cif_proveedor", cif_proveedor).eq("nombre_proveedor", nombre_proveedor).execute()
    data = query.data
    if data:
        # Existe, retornamos el primero
        return data[0]

    # Si no existe, lo creamos
    insert_resp = supabase.table("proveedores").insert({
        "cif_proveedor": cif_proveedor,
        "nombre_proveedor": nombre_proveedor,
        "tipo_servicio": tipo_servicio if tipo_servicio else ""
    }).execute()

    return insert_resp.data[0]


def create_contrato(supabase: Client, proveedor_id, centro, fecha_contrato, fecha_vencimiento, importe):
    """
    Inserta un contrato en la tabla 'contratos', vinculado al proveedor.
    """
    parsed_fecha_contrato = parse_date(fecha_contrato)
    parsed_fecha_vencimiento = parse_date(fecha_vencimiento)

    if not importe:
        importe = 0

    insert_resp = supabase.table("contratos").insert({
        "proveedor_id": proveedor_id,
        "centro": centro if centro else "",
        "fecha_contrato": parsed_fecha_contrato,
        "fecha_vencimiento": parsed_fecha_vencimiento,
        "importe": float(importe)
    }).execute()

    return insert_resp.data[0]


def create_factura(supabase: Client, contrato_id, factura_item):
    """
    Inserta una factura en la tabla 'facturas', asociada a un contrato dado.
    """
    numero_factura = factura_item.get("numero", "")
    fecha_factura_raw = factura_item.get("fecha", None)
    parsed_fecha_factura = parse_date(fecha_factura_raw)

    concepto = factura_item.get("concepto", "")
    base_exenta = factura_item.get("base exenta", 0)
    base_general = factura_item.get("base general", 0)
    iva_general = factura_item.get("iva general", 0)
    total = factura_item.get("total", 0)

    inicio_periodo_raw = factura_item.get("inicio periodo", None)
    parsed_inicio_periodo = parse_date(inicio_periodo_raw)

    fin_periodo_raw = factura_item.get("fin periodo", None)
    parsed_fin_periodo = parse_date(fin_periodo_raw)

    insert_resp = supabase.table("facturas").insert({
        "contrato_id": contrato_id,
        "numero_factura": numero_factura,
        "fecha_factura": parsed_fecha_factura,
        "concepto": concepto,
        "base_exenta": float(base_exenta),
        "base_general": float(base_general),
        "iva_general": float(iva_general),
        "total": float(total),
        "inicio_periodo": parsed_inicio_periodo,
        "fin_periodo": parsed_fin_periodo
    }).execute()

    return insert_resp.data[0]


def create_documentos_from_list(supabase: Client, documentos_list, contrato_id=None, factura_id=None):
    """
    Inserta en la tabla 'documentos' cada fichero asociado a un contrato o factura.
    """
    if not documentos_list:
        return

    for doc in documentos_list:
        nombre_archivo = doc.get("fichero", "")
        if not nombre_archivo:
            continue

        supabase.table("documentos").insert({
            "contrato_id": contrato_id,
            "factura_id": factura_id,
            "nombre_archivo": nombre_archivo
        }).execute()


def main():
    load_dotenv()

    # 1) Conexión a Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en el entorno (.env).")

    supabase: Client = create_client(url, key)

    # 2) Abrir el JSON (ajusta el nombre si difiere)
    json_file = "residencias_data.json"
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 3) Recorrer cada objeto del array
    for item in data:
        cif_proveedor = item.get("cif_proveedor", "")
        nombre_proveedor = item.get("nombre proveedor", "")
        tipo_servicio = item.get("tipo", "")
        centro = item.get("centro", "")
        fecha_contrato = item.get("fecha contrato", None)
        fecha_vencimiento = item.get("fecha vencimiento", None)
        importe = item.get("importe", 0)

        # 3.1) Crear / Obtener Proveedor
        proveedor = get_or_create_proveedor(supabase, cif_proveedor, nombre_proveedor, tipo_servicio)
        proveedor_id = proveedor["id"]

        # 3.2) Crear Contrato
        contrato = create_contrato(supabase, proveedor_id, centro, fecha_contrato, fecha_vencimiento, importe)
        contrato_id = contrato["id"]

        # 3.3) Documentos asociados al contrato
        documentos_contrato = item.get("Documentos", [])
        create_documentos_from_list(supabase, documentos_contrato, contrato_id=contrato_id)

        # 3.4) Facturas
        facturas_list = item.get("facturas", [])
        for factura_item in facturas_list:
            factura = create_factura(supabase, contrato_id, factura_item)
            factura_id = factura["id"]

            # Documentos asociados a la factura
            documentos_factura = factura_item.get("Documentos", [])
            create_documentos_from_list(supabase, documentos_factura, factura_id=factura_id)

    print("Proceso de ingestión completado. ¡Las fechas se han convertido correctamente!")


if __name__ == "__main__":
    main()
