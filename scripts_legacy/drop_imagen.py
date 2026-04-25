from db_manager import PostgresManager

def drop_imagen_column():
    db = PostgresManager()
    try:
        print("Eliminando la columna 'imagen' general de 'tblcierresz'...")
        db.execute_query("ALTER TABLE tblcierresz DROP COLUMN IF EXISTS imagen;")
        print("✅ Columna eliminada con éxito.")
    except Exception as e:
        print(f"❌ Error al eliminar la columna: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    drop_imagen_column()
