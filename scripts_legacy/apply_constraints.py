from db_manager import PostgresManager

def apply_constraints():
    db = PostgresManager()
    
    numeric_columns = [
        'num_cierre', 'ventas_gravables', 'ventas_exentas', 'impuesto', 
        'total_ingresos', 'ventas_netas', 'efectivo', 'yappy', 
        'pos_clave', 'pos_visa_mc', 'cupones', 'otros', 
        'reembolso_caja', 'total_pagos', 'dif', 'depositado'
    ]
    
    try:
        print("Iniciando aplicación de restricciones en tblcierresz...")
        
        for col in numeric_columns:
            print(f"Procesando columna: {col}")
            # 1. Limpiar nulos existentes
            update_query = f"UPDATE tblcierresz SET {col} = 0 WHERE {col} IS NULL;"
            db.execute_query(update_query)
            
            # 2. Establecer valor por defecto
            default_query = f"ALTER TABLE tblcierresz ALTER COLUMN {col} SET DEFAULT 0;"
            db.execute_query(default_query)
            
            # 3. Establecer restricción NOT NULL
            not_null_query = f"ALTER TABLE tblcierresz ALTER COLUMN {col} SET NOT NULL;"
            db.execute_query(not_null_query)
            
        print("✅ Restricciones aplicadas exitosamente en todas las columnas numéricas.")

    except Exception as e:
        print(f"❌ Error al aplicar restricciones: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    apply_constraints()
