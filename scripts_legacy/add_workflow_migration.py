import sys
import os

# Añadir el directorio padre al sys.path para poder importar db_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_manager import PostgresManager

def run_migration():
    db = PostgresManager()
    try:
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                # Add logo_url to tbl_companies
                print("Adding logo_url to tbl_companies...")
                cur.execute("ALTER TABLE tbl_companies ADD COLUMN IF NOT EXISTS logo_url VARCHAR(255);")
                
                # Add workflow_status to tbl_cierres_z_master
                print("Adding workflow_status to tbl_cierres_z_master...")
                cur.execute("ALTER TABLE tbl_cierres_z_master ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(50) DEFAULT 'draft';")
                
                # Update existing records to have 'draft' if null
                cur.execute("UPDATE tbl_cierres_z_master SET workflow_status = 'draft' WHERE workflow_status IS NULL;")
                
                conn.commit()
                print("Migration completed successfully.")
        finally:
            db.release_connection(conn)
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    run_migration()
