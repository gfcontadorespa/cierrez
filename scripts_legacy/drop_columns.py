from db_manager import PostgresManager

def drop_columns():
    db = PostgresManager()
    try:
        print("Eliminando columnas 'depositado' y 'fecha_deposito' de 'tblcierresz'...")
        db.execute_query("ALTER TABLE tblcierresz DROP COLUMN IF EXISTS depositado;")
        db.execute_query("ALTER TABLE tblcierresz DROP COLUMN IF EXISTS fecha_deposito;")
        print("✅ Columnas eliminadas con éxito.")
    except Exception as e:
        print(f"❌ Error al eliminar las columnas: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    drop_columns()
