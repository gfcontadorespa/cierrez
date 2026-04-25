from db_manager import PostgresManager

def update_cierresz_for_ocr():
    db = PostgresManager()
    try:
        print("Añadiendo columna ocr_raw_text a tblcierresz...")
        # Añadimos la columna para guardar el texto bruto del OCR
        db.execute_query("ALTER TABLE tblcierresz ADD COLUMN IF NOT EXISTS ocr_raw_text TEXT;")
        
        # También nos aseguramos de que 'imagen' sea TEXT (ya lo es, pero por seguridad)
        db.execute_query("ALTER TABLE tblcierresz ALTER COLUMN imagen TYPE TEXT;")
        
        print("✅ Columna ocr_raw_text añadida con éxito.")
    except Exception as e:
        print(f"❌ Error al actualizar la tabla: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    update_cierresz_for_ocr()
