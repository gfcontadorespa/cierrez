import pandas as pd
import os
import argparse
from gsheets_api_oauth import GoogleSheetsOAuthAPI
from db_manager import PostgresManager
from setup_relations import setup_relations_and_audit

# Configuration
SHEETS_CONFIG = {
    "sucursales": {
        "id": "16R51suML_mhKUB923fHrbi_DtU8t_1IKMAqM97lF2mk",
        "table": "tblsucursales",
        "mapping": {
            "Row ID": "branch_id",
            "Display Name": "display_name",
            "Etiqueta_Suc": "etiqueta_suc",
            "Prefijo": "prefijo",
            "email_suc": "email_suc",
            "zoho_contact_id": "zoho_contact_id",
            "zoho_tag_option_id": "zoho_tag_option_id",
            "zoho_tag_id": "zoho_tag_id"
        },
        "on_conflict": "branch_id"
    },
    "depositos": {
        "id": "1LrP7nYxJeqdgZ3_JjfW9F9S7fWtIJ0WyQEsEY5Gl9QA",
        "table": "tbl_depositos",
        "mapping": {
            "IdDeposito": "iddeposito",
            "Sucursal": "sucursal",
            "Fecha Desde": "fecha_desde",
            "Fecha Hasta": "fecha_hasta",
            "Monto": "monto",
            "Fecha Consignacion": "fecha_consignacion",
            "Realizado por": "realizado_por",
            "Comentarios": "comentarios",
            "Estado": "estado",
            "Adjuntos": "adjuntos"
        },
        "on_conflict": "iddeposito"
    },
    "cierresz": {
        "id": "1ytAlhLi5asOUdGaVQc5cSgHguABMUq4aJTYlbe1GZ_E",
        "table": "tblcierresz",
        "mapping": {
            "Row ID": "row_id",
            "Customer Name": "customer_name",
            "num_cierre": "num_cierre",
            "Invoice Date": "invoice_date",
            "Ventas Gravables": "ventas_gravables",
            "Ventas Exentas": "ventas_exentas",
            "Impuesto": "impuesto",
            "total_ingresos": "total_ingresos",
            "ventas_netas": "ventas_netas",
            "Efectivo": "efectivo",
            "Yappy": "yappy",
            "[POS] Clave": "pos_clave",
            "[POS] Visa/MC": "pos_visa_mc",
            "Cupones": "cupones",
            "Otros": "otros",
            "Reembolso Caja": "reembolso_caja",
            "Total_Pagos": "total_pagos",
            "Dif.": "dif",
            "Invoice Number": "invoice_number",
            "Comentarios": "comentarios",
            "Estado": "estado",
            "Etiqueta_Sucursal": "etiqueta_sucursal",
            "Datáfono": "datafono",
            "Imagen": "imagen",
            "fecha_adicion": "fecha_adicion",
            "fecha_modifica": "fecha_modifica",
            "Depositado": "depositado",
            "fecha_deposito": "fecha_deposito"
        },
        "on_conflict": "row_id"
    }
}

def clean_numeric(val):
    if pd.isna(val) or val == '':
        return 0
    if isinstance(val, (int, float)):
        return val
    # Remove currency symbols and commas
    cleaned = str(val).replace('$', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0

def clean_date(val):
    if pd.isna(val) or val == '':
        return None
    try:
        # Try common formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
            try:
                return pd.to_datetime(val, format=fmt).date()
            except:
                continue
        return pd.to_datetime(val).date()
    except:
        return None

def migrate_table(api, db, config_key, dry_run=False):
    config = SHEETS_CONFIG[config_key]
    print(f"\n--- Migrating {config_key} to {config['table']} ---")
    
    sheet_url = f"https://docs.google.com/spreadsheets/d/{config['id']}"
    sheet = api.open_spreadsheet(sheet_url)
    # Assume first worksheet unless it's CierresZ or complicated
    ws = sheet.get_worksheet(0)
    print(f"Reading from worksheet: {ws.title}")
    
    records = ws.get_all_records()
    if not records:
        print("No records found.")
        return

    df = pd.DataFrame(records)
    
    # Map columns
    df = df.rename(columns=config['mapping'])
    # Keep only mapped columns
    cols_to_keep = list(config['mapping'].values())
    df = df[[c for c in cols_to_keep if c in df.columns]]
    
    # Sanitize data based on table schema (simplistic approach based on column names)
    numeric_cols = [
        'num_cierre', 'ventas_gravables', 'ventas_exentas', 'impuesto', 
        'total_ingresos', 'ventas_netas', 'efectivo', 'yappy', 
        'pos_clave', 'pos_visa_mc', 'cupones', 'otros', 
        'reembolso_caja', 'total_pagos', 'dif', 'depositado', 'monto'
    ]
    date_cols = [
        'invoice_date', 'fecha_deposito', 'fecha_desde', 'fecha_hasta', 'fecha_consignacion',
        'fecha_adicion', 'fecha_modifica'
    ]
    
    # Strings: replace NaN or empty string with None
    for col in df.columns:
        if col in numeric_cols:
            df[col] = df[col].apply(clean_numeric)
        elif col in date_cols:
            df[col] = df[col].apply(clean_date)
        else:
            df[col] = df[col].apply(lambda x: None if pd.isna(x) or str(x).strip() == '' else str(x).strip())

    # DROP ROWS WITH MISSING PRIMARY KEY
    pk = config['on_conflict']
    initial_len = len(df)
    df = df.dropna(subset=[pk])
    if len(df) < initial_len:
        print(f"Dropped {initial_len - len(df)} rows with missing {pk}.")

    # HANDLE DUPLICATES IN DEPOSITOS
    if config_key == "depositos":
        # Check for duplicate PKs
        counts = df[pk].value_counts()
        duplicate_ids = counts[counts > 1].index.tolist()
        
        if duplicate_ids:
            print(f"Found {len(duplicate_ids)} duplicate IDs. Assigning unique suffixes...")
            for dup_id in duplicate_ids:
                mask = df[pk] == dup_id
                indices = df[mask].index
                # Keep the first one as is, append suffix to others
                for i, idx in enumerate(indices[1:], 1):
                    df.at[idx, pk] = f"{dup_id}_{i}"
            print(f"Unique IDs assigned. Total unique records now: {len(df[pk].unique())}")

    if dry_run:
        print(f"[DRY RUN] Would insert {len(df)} records into {config['table']}")
        print("Sample data after cleaning:")
        print(df.head(2).to_string())
        return

    print(f"Inserting/Updating {len(df)} records...")
    
    columns = df.columns.tolist()
    placeholders = ", ".join(["%s"] * len(columns))
    update_cols = ", ".join([f"{c} = EXCLUDED.{c}" for c in columns if c != config['on_conflict']])
    
    query = f"""
    INSERT INTO {config['table']} ({", ".join(columns)})
    VALUES ({placeholders})
    ON CONFLICT ({config['on_conflict']}) DO UPDATE SET
    {update_cols}
    """
    
    params_list = [tuple(x) for x in df.values]
    count = db.execute_batch(query, params_list, page_size=200)
    print(f"✅ Processed {count} records in {config['table']}.")

def run_migration(dry_run=False):
    db = PostgresManager()
    try:
        api = GoogleSheetsOAuthAPI('client_secret.json')
        
        # Order matters: Sucursales first, then Cierres/Depositos
        migrate_table(api, db, "sucursales", dry_run)
        migrate_table(api, db, "depositos", dry_run)
        migrate_table(api, db, "cierresz", dry_run)
        
        if not dry_run:
            print("\n--- Setting up relations and audit fields ---")
            setup_relations_and_audit()
            print("✅ All data migration and setup complete.")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate Google Sheets data to PostgreSQL.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying the database.")
    args = parser.parse_args()
    
    run_migration(dry_run=args.dry_run)
