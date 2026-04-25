from db_manager import PostgresManager

def drop_all_tables():
    db = PostgresManager()
    try:
        # Consulta para obtener todas las tablas en el esquema public
        query_get_tables = """
        SELECT tablename 
        FROM pg_catalog.pg_tables 
        WHERE schemaname = 'public';
        """
        tables = db.fetch_all(query_get_tables)
        
        if not tables:
            print("No se encontraron tablas para eliminar.")
            return

        print(f"Encontradas {len(tables)} tablas. Iniciando eliminación...")
        
        # Eliminamos cada tabla con CASCADE para manejar las dependencias
        for table in tables:
            table_name = table[0]
            drop_query = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
            print(f"Eliminando tabla: {table_name}...")
            db.execute_query(drop_query)
        
        print("✅ Todas las tablas han sido eliminadas correctamente.")

    except Exception as e:
        print(f"❌ Error al eliminar las tablas: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    drop_all_tables()
