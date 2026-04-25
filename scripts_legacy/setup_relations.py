from db_manager import PostgresManager

def setup_relations_and_audit():
    db = PostgresManager()
    
    try:
        print("1. Ajustando esquema de Tablas...")
        db.execute_query("ALTER TABLE tblcierresz ADD COLUMN IF NOT EXISTS branch_id TEXT;")
        db.execute_query("ALTER TABLE tbl_depositos ADD COLUMN IF NOT EXISTS branch_id TEXT;")
        
        # Asegurar tipos correctos (por si acaso)
        for table in ['tblcierresz', 'tbl_depositos']:
            col_type = db.fetch_one(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'branch_id';")
            if col_type and col_type[0] == 'uuid':
                print(f"Cambiando tipo de branch_id de UUID a TEXT en {table}...")
                db.execute_query(f"ALTER TABLE {table} ALTER COLUMN branch_id TYPE TEXT USING branch_id::text;")

        print("2. Vinculando registros de Cierres Z...")
        # Lógica 1: Prefijo en customer_name (Formato 'ID: PREFIX')
        updated_c_pref = db.execute_query("""
            UPDATE tblcierresz c
            SET branch_id = s.branch_id
            FROM tblsucursales s
            WHERE split_part(c.customer_name, ': ', 2) = s.prefijo
            AND c.branch_id IS NULL;
        """)
        print(f"✅ Se vincularon {updated_c_pref} cierres usando prefijo.")

        # Lógica 2: Fallback usando etiqueta_sucursal (si existe)
        cols = db.fetch_all("SELECT column_name FROM information_schema.columns WHERE table_name = 'tblcierresz';")
        if any(c[0] == 'etiqueta_sucursal' for c in cols):
             updated_c_name = db.execute_query("""
                UPDATE tblcierresz c
                SET branch_id = s.branch_id
                FROM tblsucursales s
                WHERE LOWER(TRIM(c.etiqueta_sucursal)) = LOWER(TRIM(s.display_name))
                AND c.branch_id IS NULL;
            """)
             print(f"✅ Se vincularon {updated_c_name} cierres usando nombre.")

        print("3. Vinculando registros de Depósitos...")
        # Lógica 1: Prefijo en sucursal (Formato 'ID: PREFIX')
        updated_d_pref = db.execute_query("""
            UPDATE tbl_depositos d
            SET branch_id = s.branch_id
            FROM tblsucursales s
            WHERE split_part(d.sucursal, ': ', 2) = s.prefijo
            AND d.branch_id IS NULL;
        """)
        print(f"✅ Se vincularon {updated_d_pref} depósitos usando prefijo.")

        print("4. Estableciendo restricciones de Foreign Key...")
        for table, constraint in [('tblcierresz', 'fk_cierres_sucursal'), ('tbl_depositos', 'fk_depositos_sucursal')]:
            db.execute_query(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{constraint}') THEN
                        ALTER TABLE {table} 
                        ADD CONSTRAINT {constraint} 
                        FOREIGN KEY (branch_id) REFERENCES tblsucursales(branch_id);
                    END IF;
                END;
                $$;
            """)
        
        print("5. Actualizando campos de Auditoría en Cierres...")
        audit_cols = {
            "audit_total_pagos": "efectivo + yappy + pos_clave + pos_visa_mc + cupones + otros",
            "audit_diferencia": "total_ingresos - (efectivo + yappy + pos_clave + pos_visa_mc + cupones + otros)"
        }
        for col, formula in audit_cols.items():
            db.execute_query(f"ALTER TABLE tblcierresz ADD COLUMN IF NOT EXISTS {col} NUMERIC DEFAULT 0;")
            db.execute_query(f"UPDATE tblcierresz SET {col} = {formula};")

        print("6. Optimizando search_labels para AppSheet...")
        # Label para cierres
        db.execute_query("ALTER TABLE tblcierresz ADD COLUMN IF NOT EXISTS search_label TEXT;")
        db.execute_query("""
            UPDATE tblcierresz c
            SET search_label = 'Cierre #' || COALESCE(c.num_cierre::text, '0') || ' - ' || COALESCE(c.invoice_date::text, 'Sin Fecha')
            FROM tblsucursales s
            WHERE c.branch_id = s.branch_id;
        """)

        # Label para depósitos
        db.execute_query("ALTER TABLE tbl_depositos ADD COLUMN IF NOT EXISTS search_label TEXT;")
        db.execute_query("""
            UPDATE tbl_depositos d
            SET search_label = 'Depósito $' || COALESCE(d.monto::text, '0') || ' (' || COALESCE(d.fecha_desde::text, '') || ')'
            FROM tblsucursales s
            WHERE d.branch_id = s.branch_id;
        """)
            
        print("✅ Todo configurado con éxito.")

    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    setup_relations_and_audit()
