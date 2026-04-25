import csv
import os
from db_manager import PostgresManager

def create_table_sucursales(db):
    # SQL para crear la tabla de sucursales "Limpia"
    create_table_query = """
    CREATE TABLE IF NOT EXISTS tblsucursales (
        branch_id TEXT PRIMARY KEY,
        display_name TEXT,
        etiqueta_suc TEXT,
        prefijo TEXT,
        email_suc TEXT,
        active BOOLEAN DEFAULT TRUE,
        zoho_contact_id TEXT,
        zoho_tag_option_id TEXT,
        zoho_tag_id TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    print("Creando tabla tblsucursales (Estructura Limpia)...")
    db.execute_query(create_table_query)

def create_table_cierresz(db):
    # SQL para crear la tabla de cierres "Limpia"
    create_table_query = """
    CREATE TABLE IF NOT EXISTS tblcierresz (
        row_id TEXT PRIMARY KEY,
        customer_name TEXT,
        branch_id TEXT REFERENCES tblsucursales(branch_id),
        num_cierre NUMERIC NOT NULL DEFAULT 0,
        invoice_date DATE,
        ventas_gravables NUMERIC NOT NULL DEFAULT 0,
        ventas_exentas NUMERIC NOT NULL DEFAULT 0,
        impuesto NUMERIC NOT NULL DEFAULT 0,
        total_ingresos NUMERIC NOT NULL DEFAULT 0,
        ventas_netas NUMERIC NOT NULL DEFAULT 0,
        efectivo NUMERIC NOT NULL DEFAULT 0,
        yappy NUMERIC NOT NULL DEFAULT 0,
        pos_clave NUMERIC NOT NULL DEFAULT 0,
        pos_visa_mc NUMERIC NOT NULL DEFAULT 0,
        cupones NUMERIC NOT NULL DEFAULT 0,
        otros NUMERIC NOT NULL DEFAULT 0,
        reembolso_caja NUMERIC NOT NULL DEFAULT 0,
        total_pagos NUMERIC NOT NULL DEFAULT 0,
        dif NUMERIC NOT NULL DEFAULT 0,
        invoice_number TEXT,
        comentarios TEXT,
        estado TEXT,
        etiqueta_sucursal TEXT,
        datafono TEXT,
        imagen TEXT,
        fecha_adicion TIMESTAMPTZ DEFAULT NOW(),
        fecha_modifica TIMESTAMPTZ DEFAULT NOW(),
        depositado NUMERIC NOT NULL DEFAULT 0,
        fecha_deposito DATE,
        audit_total_pagos NUMERIC DEFAULT 0,
        audit_diferencia NUMERIC DEFAULT 0,
        ocr_raw_text TEXT
    );
    """
    print("Creando tabla tblcierresz (Estructura Limpia)...")
    db.execute_query(create_table_query)

def create_table_depositos(db):
    # SQL para crear la tabla de depósitos con IdDeposito
    create_table_query = """
    CREATE TABLE IF NOT EXISTS tbl_depositos (
        deposito_id TEXT PRIMARY KEY,
        sucursal TEXT,
        branch_id TEXT REFERENCES tblsucursales(branch_id),
        fecha_desde DATE,
        fecha_hasta DATE,
        monto NUMERIC,
        fecha_consignacion DATE,
        realizado_por TEXT,
        comentarios TEXT,
        estado TEXT,
        adjuntos TEXT,
        search_label TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    print("Creando tabla tbl_depositos (Estructura Limpia)...")
    db.execute_query(create_table_query)

if __name__ == "__main__":
    db = PostgresManager()
    try:
        create_table_sucursales(db)
        create_table_cierresz(db)
        create_table_depositos(db)
        print("✅ Todas las tablas han sido creadas con la estructura limpia.")
    finally:
        db.close_all_connections()
