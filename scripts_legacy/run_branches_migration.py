import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_manager import PostgresManager

def run_migration():
    db = PostgresManager()
    
    print("Iniciando migración de Sucursales...")
    
    sql_script = """
    -- 1. Crear tabla de sucursales
    CREATE TABLE IF NOT EXISTS tbl_branches (
        id SERIAL PRIMARY KEY,
        company_id INTEGER REFERENCES tbl_companies(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- 2. Insertar sucursal por defecto para la Compañía 1 si no existe
    INSERT INTO tbl_branches (id, company_id, name)
    VALUES (1, 1, 'Casa Matriz')
    ON CONFLICT DO NOTHING;

    -- 3. Actualizar cierres huérfanos
    UPDATE tbl_cierres_z_master SET branch_id = 1 WHERE branch_id IS NULL AND company_id = 1;

    -- 4. Añadir Constraint FK a tbl_cierres_z_master
    ALTER TABLE tbl_cierres_z_master 
    DROP CONSTRAINT IF EXISTS tbl_cierres_z_master_branch_id_fkey;

    ALTER TABLE tbl_cierres_z_master
    ADD CONSTRAINT tbl_cierres_z_master_branch_id_fkey
    FOREIGN KEY (branch_id) REFERENCES tbl_branches(id) ON DELETE RESTRICT;
    """
    
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_script)
        conn.commit()
        print("✅ Migración de Sucursales completada con éxito.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error ejecutando migración: {e}")
    finally:
        db.release_connection(conn)
        db.close_all_connections()

if __name__ == "__main__":
    run_migration()
