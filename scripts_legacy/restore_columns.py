from db_manager import PostgresManager

def restore_columns():
    db = PostgresManager()
    try:
        print("Restaurando columnas eliminadas en 'tblcierresz' para revivir AppSheet...")
        db.execute_query("ALTER TABLE tblcierresz ADD COLUMN IF NOT EXISTS depositado NUMERIC NOT NULL DEFAULT 0;")
        db.execute_query("ALTER TABLE tblcierresz ADD COLUMN IF NOT EXISTS fecha_deposito DATE;")
        db.execute_query("ALTER TABLE tblcierresz ADD COLUMN IF NOT EXISTS imagen TEXT;")
        print("✅ Columnas restauradas con éxito.")
    except Exception as e:
        print(f"❌ Error al restaurar: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    restore_columns()
