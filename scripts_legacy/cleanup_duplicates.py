from db_manager import PostgresManager
import json

def cleanup():
    db = PostgresManager()
    
    # 1. Obtener todos los grupos con invoice_number duplicado
    query_find = """
    SELECT invoice_number
    FROM tblcierresz 
    WHERE invoice_number IS NOT NULL AND invoice_number != '' 
    GROUP BY invoice_number 
    HAVING COUNT(*) > 1;
    """
    dupes = db.fetch_all(query_find)
    print(f"Encontrados {len(dupes)} grupos de números de factura duplicados.")

    for (inv_num,) in dupes:
        # Obtener detalles de cada grupo
        query_details = """
        SELECT row_id, branch_id, invoice_date, total_ingresos, num_cierre
        FROM tblcierresz
        WHERE invoice_number = %s
        ORDER BY invoice_date DESC, row_id;
        """
        records = db.fetch_all(query_details, (inv_num,))
        
        # El primero (más reciente) será el "Maestro"
        master = records[0]
        to_check = records[1:]
        
        for rec in to_check:
            rid, bid, idate, total, nc = rec
            # Si es idéntico en fecha y monto, es un duplicado por doble subida
            if idate == master[2] and bid == master[1] and float(total or 0) == float(master[3] or 0):
                print(f"🗑️ Eliminando duplicado exacto: {inv_num} del {idate} (ID: {rid})")
                db.execute_query("DELETE FROM tblcierresz WHERE row_id = %s", (rid,))
            else:
                # Si es el mismo número pero distinta fecha o monto, es conflicto cronológico
                new_num = f"{inv_num}-OLD-{rid[:4]}"
                print(f"🏷️ Renombrando duplicado cronológico: {inv_num} -> {new_num} (ID: {rid})")
                db.execute_query("UPDATE tblcierresz SET invoice_number = %s WHERE row_id = %s", (new_num, rid))

    # 2. Aplicar la restricción de UNIQUE en la base de datos
    print("💎 Aplicando restricción UNIQUE a invoice_number...")
    try:
        db.execute_query("ALTER TABLE tblcierresz ADD CONSTRAINT unique_invoice_number UNIQUE (invoice_number);")
        print("✅ Restricción UNIQUE aplicada con éxito.")
    except Exception as e:
        print(f"❌ Error aplicando restricción: {e}")

    db.close_all_connections()

if __name__ == "__main__":
    cleanup()
