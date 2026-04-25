from db_manager import PostgresManager

def test_connection():
    try:
        print("Probando conexión a la base de datos...")
        db = PostgresManager()
        version = db.fetch_one("SELECT version();")
        
        if version:
            print(f"✅ Conexión exitosa!")
            print(f"Versión de Postgres: {version[0]}")
            
            # Probar creación de una tabla de prueba
            print("\nProbando creación de tabla de prueba...")
            db.execute_query("CREATE TABLE IF NOT EXISTS test_connection (id serial PRIMARY KEY, test_val varchar(50));")
            db.execute_query("INSERT INTO test_connection (test_val) VALUES (%s);", ("Conexión Verificada",))
            
            result = db.fetch_one("SELECT test_val FROM test_connection ORDER BY id DESC LIMIT 1;")
            print(f"Resultado de inserción/consulta: {result[0]}")
            
            # Limpiar
            # db.execute_query("DROP TABLE test_connection;")
            # print("Tabla de prueba eliminada.")
        else:
            print("❌ No se pudo obtener la versión de la base de datos.")
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
    finally:
        if 'db' in locals():
            db.close_all_connections()

if __name__ == "__main__":
    test_connection()
