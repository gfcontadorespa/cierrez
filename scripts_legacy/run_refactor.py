import os
from db_manager import PostgresManager

def run_migration():
    db = PostgresManager()
    sql_file_path = os.path.join(os.path.dirname(__file__), 'refactor_schema.sql')
    
    print("Iniciando refactorización de la base de datos...")
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql_script)
            conn.commit()
            print("✅ Refactorización completada con éxito. Tablas SaaS y de Pagos creadas.")
        except Exception as e:
            conn.rollback()
            print(f"❌ Error ejecutando el script SQL: {e}")
            raise
        finally:
            db.release_connection(conn)
            
    except Exception as e:
        print(f"Error general: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    run_migration()
