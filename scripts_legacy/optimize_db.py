from db_manager import PostgresManager

def optimize_db():
    db = PostgresManager()
    try:
        print("1. Creando índices para mejorar el rendimiento de búsqueda...")
        # Índices en tblsucursales
        db.execute_query("CREATE INDEX IF NOT EXISTS idx_sucursales_display_name ON tblsucursales (display_name);")
        db.execute_query("CREATE INDEX IF NOT EXISTS idx_sucursales_email ON tblsucursales (email_suc text_pattern_ops);")
        
        # Índices en tblcierresz para los joins y filtros comunes
        db.execute_query("CREATE INDEX IF NOT EXISTS idx_cierresz_branch_id ON tblcierresz (branch_id);")
        db.execute_query("CREATE INDEX IF NOT EXISTS idx_cierresz_invoice_date ON tblcierresz (invoice_date);")
        db.execute_query("CREATE INDEX IF NOT EXISTS idx_cierresz_etiqueta ON tblcierresz (etiqueta_sucursal);")
        print("✅ Índices creados.")

        print("\n2. Consolidando sucursales duplicadas...")
        # ID a mantener (el que parece ser de AppSheet)
        keep_id = 'b9Qd6QQtsn4mYst8_tFnYa'
        # ID a eliminar (el que parece ser un error)
        remove_id = '6e8304ce'
        
        # Primero actualizamos los cierres que apunten al ID malo
        print(f"Migrando cierres de {remove_id} a {keep_id}...")
        updated_cierres = db.execute_query(
            "UPDATE tblcierresz SET branch_id = %s WHERE branch_id = %s;",
            (keep_id, remove_id)
        )
        print(f"✅ {updated_cierres} cierres actualizados.")
        
        # Luego eliminamos la sucursal duplicada
        print(f"Eliminando sucursal obsoleta {remove_id}...")
        deleted_suc = db.execute_query(
            "DELETE FROM tblsucursales WHERE branch_id = %s;",
            (remove_id,)
        )
        print(f"✅ {deleted_suc} sucursal eliminada.")

        print("\n3. Refrescando search_label para todas las sucursales...")
        db.execute_query("""
            UPDATE tblcierresz c
            SET search_label = COALESCE(s.display_name, 'Sin Sucursal') || ' - ' || COALESCE(c.invoice_date::text, 'Sin Fecha') || ' - Cierre #' || COALESCE(c.num_cierre::text, '0')
            FROM tblsucursales s
            WHERE c.branch_id = s.branch_id;
        """)
        print("✅ search_label actualizado.")

    except Exception as e:
        print(f"❌ Error durante la optimización: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    optimize_db()
