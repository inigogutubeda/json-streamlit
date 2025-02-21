# rag/pipeline.py
import pandas as pd
from .parser import interpret_question
from .db_queries import (
    ranking_gastos_por_centro,
    factura_mas_alta_year,
    ranking_proveedores_por_centro,
    resumen_residencia,
    get_facturas,
    get_facturas,
    facturas_con_importe_mayor,
    proveedor_mas_contratos,
    factura_mas_reciente,
    gasto_en_rango_fechas,
    contratos_vencen_antes_de,
    # etc
)
from .gpt import create_gpt_client, build_prompt, chat_completion

def process_user_question(supabase_client, user_input, openai_api_key=""):
    intent_data = interpret_question(user_input)
    intent = intent_data["intent"]
    context_str = ""

    if intent == "ranking_gastos_centros":
        year = intent_data.get("year", None)
        df_rank = ranking_gastos_por_centro(supabase_client, year)
        if df_rank.empty:
            context_str = "No encontré facturas con esa condición."
        else:
            context_str = "Ranking de gasto por centro:\n"
            for i, row in df_rank.iterrows():
                context_str += f"- {row['centro']}: {row['total']:.2f}\n"
            top = df_rank.iloc[0]
            context_str += f"\nEl mayor gasto lo tiene {top['centro']} con {top['total']:.2f}."

    elif intent == "max_factura_year":
        year = intent_data.get("year", None)
        row_max = factura_mas_alta_year(supabase_client, year)
        if row_max is None:
            context_str = f"No encontré facturas para {year}."
        else:
            context_str = (f"La factura más alta en {year} es {row_max['numero_factura']}, "
                           f"con un total de {row_max['total']:.2f} €.")

    elif intent == "ranking_proveedores":
        centro = intent_data.get("centro", None)
        year = intent_data.get("year", None)
        df_rank = ranking_proveedores_por_centro(supabase_client, centro, year)
        if df_rank.empty:
            context_str = "No se encontraron proveedores con esos criterios."
        else:
            context_str = "Ranking de proveedores:\n"
            for i, row in df_rank.iterrows():
                context_str += f"- {row['nombre_proveedor']}: {row['total']:.2f}\n"
            top = df_rank.iloc[0]
            context_str += f"\nEl proveedor con mayor gasto es {top['nombre_proveedor']} con {top['total']:.2f}."

    elif intent == "resumen_residencia":
        centro = intent_data.get("centro")
        if not centro:
            context_str = "No indicaste la residencia."
        else:
            data = resumen_residencia(supabase_client, centro)
            if data is None or data["contratos"].empty:
                context_str = f"No encontré datos para {centro}."
            else:
                total_gasto = data["total_gasto"]
                num_contr = len(data["contratos"])
                num_fact = len(data["facturas"])
                context_str = (
                    f"Resumen de {centro}:\n"
                    f"- Contratos: {num_contr}\n"
                    f"- Facturas: {num_fact}\n"
                    f"- Gasto total: {total_gasto:.2f} €"
                )
    elif intent == "get_total_year":
        year = intent_data.get("year")
        df_fact = get_facturas(supabase_client)
        if df_fact.empty:
            context_str = "No hay facturas."
        else:
            df_fact["fecha_factura"] = pd.to_datetime(df_fact["fecha_factura"], errors="coerce")
            df_fact["year"] = df_fact["fecha_factura"].dt.year
            df_fact["total"] = pd.to_numeric(df_fact["total"], errors="coerce").fillna(0)
            df_fact = df_fact[df_fact["year"] == year]
            if df_fact.empty:
                context_str = f"No hallé facturas en {year}."
            else:
                suma = df_fact["total"].sum()
                context_str = f"En {year} hay {len(df_fact)} facturas por un total de {suma:.2f}€."
    elif intent == "facturas_importe_mayor":
        importe = intent_data.get("importe", None)
        if importe is None:
            context_str = "No se reconoció el importe."
        else:
            df_res = facturas_con_importe_mayor(supabase_client, importe)
            if df_res.empty:
                context_str = f"No hay facturas con importe mayor a {importe}."
            else:
                context_str = f"Encontré {len(df_res)} facturas con importe mayor a {importe}.\n"
                df_res["total"] = df_res["total"].astype(float)
                sum_importe = df_res["total"].sum()
                context_str += f"Suma de esas facturas = {sum_importe:.2f}."

    # 2) proveedor_mas_contratos
    elif intent == "proveedor_mas_contratos":
        df_rank = proveedor_mas_contratos(supabase_client)
        if df_rank.empty:
            context_str = "No hay contratos ni proveedores."
        else:
            top = df_rank.iloc[0]
            context_str = "Ranking de Proveedores por número de contratos:\n"
            for i, row in df_rank.iterrows():
                context_str += f"- {row['nombre_proveedor']}: {row['num_contratos']} contratos\n"
            context_str += f"\nEl que más contratos tiene es {top['nombre_proveedor']} con {top['num_contratos']}."

    # 3) factura_mas_reciente
    elif intent == "factura_mas_reciente":
        row = factura_mas_reciente(supabase_client)
        if row is None:
            context_str = "No encontré facturas con fecha válida."
        else:
            context_str = (f"La factura más reciente es '{row['numero_factura']}' "
                           f"con fecha {row['fecha_factura']} y total {row['total']}.")

    # 4) gasto_en_rango
    elif intent == "gasto_en_rango":
        fecha_i = intent_data.get("fecha_inicio", None)
        fecha_f = intent_data.get("fecha_fin", None)
        if not fecha_i or not fecha_f:
            context_str = "No se encontraron fechas de inicio y fin."
        else:
            total_rango = gasto_en_rango_fechas(supabase_client, fecha_i, fecha_f)
            if total_rango < 0:
                context_str = "No pude parsear las fechas (dd/mm/yyyy)."
            else:
                context_str = (f"El gasto total entre {fecha_i} y {fecha_f} "
                               f"es de {total_rango:.2f}.")

    # 5) contratos_vencen_antes
    elif intent == "contratos_vencen_antes":
        vence_str = intent_data.get("fecha_vencimiento")
        df = contratos_vencen_antes_de(supabase_client, vence_str)
        if df.empty:
            context_str = f"No hay contratos que venzan antes de {vence_str}."
        else:
            context_str = f"Contratos que vencen antes de {vence_str}: {len(df)}.\n"
            # Ejemplo: enumerarlos
            for i, row in df.iterrows():
                context_str += f"- Contrato ID {row['id']} en centro {row['centro']}, vence {row['fecha_vencimiento']}\n"
    else:
        # GPT no llamó a una función. 
        # Ej: GPT dio una respuesta textual. 
        # Para una POC, podemos simplemente devolver choice.message.content
        return choice.message.content.strip()
