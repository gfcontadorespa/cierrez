import os
import sys

# Añadir directorio padre para importar db_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_manager import PostgresManager

def seed_admin():
    db = PostgresManager()
    
    # 1. Aplicar la migración SQL primero
    sql_file_path = os.path.join(os.path.dirname(__file__), 'update_users_schema.sql')
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql_script)
            conn.commit()
            print("✅ Columna is_global_admin añadida con éxito.")
        except Exception as e:
            conn.rollback()
            print(f"❌ Error ejecutando el script SQL: {e}")
            raise
        finally:
            db.release_connection(conn)
    except Exception as e:
        print(f"Error general migración: {e}")

    # 2. Insertar usuario y asignarle rol
    try:
        email = "jflores@gfcontadorespa.com"
        name = "Joslu Flores"
        
        # Verificar si existe la compañía 1
        comp = db.fetch_one("SELECT id FROM tbl_companies WHERE id = 1")
        if not comp:
            print("❌ No existe la compañía ID 1. Por favor crea una en la web primero.")
            return

        # Insertar en tbl_users
        query_user = """
            INSERT INTO tbl_users (email, name, is_global_admin, active) 
            VALUES (%s, %s, TRUE, TRUE) 
            ON CONFLICT (email) DO UPDATE SET is_global_admin = TRUE, active = TRUE
            RETURNING id;
        """
        result = db.fetch_one(query_user, (email, name))
        if result:
            user_id = result[0]
        else:
            user_id = db.fetch_one("SELECT id FROM tbl_users WHERE email = %s", (email,))[0]
        
        # Insertar en tbl_company_users como 'admin'
        query_role = """
            INSERT INTO tbl_company_users (company_id, user_id, role) 
            VALUES (1, %s, 'admin') 
            ON CONFLICT (company_id, user_id) DO UPDATE SET role = 'admin';
        """
        db.execute_query(query_role, (user_id,))
        
        print(f"✅ Usuario {email} creado/actualizado como Global Admin y Admin de Compañía 1.")
        
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    seed_admin()
