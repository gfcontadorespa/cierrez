import secrets
import string
from db_manager import PostgresManager

def generate_short_id(length=22):
    # Generar un ID estilo AppSheet (alfanumérico de unos 22 caracteres)
    alphabet = string.ascii_letters + string.digits + "_-"
    return "".join(secrets.choice(alphabet) for _ in range(length))

def add_missing_branches():
    db = PostgresManager()
    try:
        branches_to_add = [
            {
                "display_name": "Westland Movies [AK]",
                "prefijo": "AK",
                "email_suc": "movieswestland@mic.com.pa" # Asumiendo correo
            },
            {
                "display_name": "Mic David [AM]",
                "prefijo": "AM",
                "email_suc": "micdavid@mic.com.pa" # Asumiendo correo
            }
        ]
        
        print("1. Insertando sucursales faltantes...")
        for branch in branches_to_add:
            # Verificar si ya existe por casualidad
            exists = db.fetch_one("SELECT 1 FROM tblsucursales WHERE display_name = %s", (branch['display_name'],))
            if not exists:
                branch_id = generate_short_id()
                query = """
                INSERT INTO tblsucursales (branch_id, display_name, prefijo, email_suc)
                VALUES (%s, %s, %s, %s)
                """
                db.execute_query(query, (branch_id, branch['display_name'], branch['prefijo'], branch['email_suc']))
                print(f"✅ Añadida sucursal: {branch['display_name']} con ID: {branch_id}")
            else:
                print(f"ℹ️ La sucursal {branch['display_name']} ya existe.")

        print("\n2. Vinculando registros de cierres huérfanos...")
        update_links_query = """
        UPDATE tblcierresz c
        SET branch_id = s.branch_id
        FROM tblsucursales s
        WHERE LOWER(TRIM(c.etiqueta_sucursal)) = LOWER(TRIM(s.display_name))
        AND c.branch_id IS NULL;
        """
        updated_rows = db.execute_query(update_links_query)
        print(f"✅ Se vincularon {updated_rows} registros de cierres.")

        print("\n3. Actualizando search_label...")
        update_label_query = """
        UPDATE tblcierresz c
        SET search_label = COALESCE(s.display_name, 'Sin Sucursal') || ' - ' || COALESCE(c.invoice_date::text, 'Sin Fecha') || ' - Cierre #' || COALESCE(c.num_cierre::text, '0')
        FROM tblsucursales s
        WHERE c.branch_id = s.branch_id;
        """
        db.execute_query(update_label_query)
        print("✅ search_label actualizado.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    add_missing_branches()
