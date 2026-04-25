import os
import sys

# Añadir directorio padre para importar db_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_manager import PostgresManager

def run_migration():
    db = PostgresManager()
    sql_file_path = os.path.join(os.path.dirname(__file__), 'update_banks_schema.sql')
    
    print("Iniciando actualización de esquema de bancos...")
    
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql_script)
            conn.commit()
            print("✅ Actualización completada con éxito. Tabla tbl_bank_accounts creada.")
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
