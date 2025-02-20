# create_schema.py
import os
from dotenv import load_dotenv
from supabase import create_client

def create_tables():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    # Definir las sentencias SQL de creación
    # (Cada CREATE TABLE IF NOT EXISTS en SQL “clásico”)
    sql_statements = [
        """
        CREATE TABLE IF NOT EXISTS proveedores (
            id SERIAL PRIMARY KEY,
            cif_proveedor VARCHAR(50),
            nombre_proveedor VARCHAR(255),
            tipo_servicio VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS contratos (
            id SERIAL PRIMARY KEY,
            proveedor_id INT REFERENCES proveedores (id) ON DELETE CASCADE,
            centro VARCHAR(255),
            fecha_contrato DATE,
            fecha_vencimiento DATE,
            importe NUMERIC(12,2),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS facturas (
            id SERIAL PRIMARY KEY,
            contrato_id INT REFERENCES contratos (id) ON DELETE CASCADE,
            numero_factura VARCHAR(100),
            fecha_factura DATE,
            concepto VARCHAR(255),
            base_exenta NUMERIC(12,2),
            base_general NUMERIC(12,2),
            iva_general NUMERIC(12,2),
            total NUMERIC(12,2),
            inicio_periodo DATE,
            fin_periodo DATE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS documentos (
            id SERIAL PRIMARY KEY,
            contrato_id INT REFERENCES contratos (id) ON DELETE CASCADE,
            factura_id INT REFERENCES facturas (id) ON DELETE CASCADE,
            nombre_archivo VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
    ]

    for sql in sql_statements:
        response = supabase.rpc("execute_sql", {"sql": sql}).execute()
        # Nota: 'rpc("execute_sql")' es sólo un ejemplo. Si no tienes 
        # una función "execute_sql" en tu supabase, tendrías que usar 
        # la conexión "raw SQL" de otra forma o la interfaz web.

    print("Tablas creadas (o existentes) correctamente.")

if __name__ == "__main__":
    create_tables()
