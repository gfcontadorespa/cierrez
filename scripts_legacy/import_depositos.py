import pandas as pd
import os
from db_manager import PostgresManager

def import_depositos(db, excel_path):
    if not os.path.exists(excel_path):
        print(f"Error: No se encontró el archivo Excel en {excel_path}")
        return

    print(f"Importando depósitos desde {excel_path}...")
    
    # Leer el Excel
    df = pd.read_excel(excel_path)
    
    # Renombrar columnas para que coincidan con la base de datos (o mapearlas)
    # Columnas Excel: Sucursal, Fecha Desde, Fecha Hasta, Monto, Fecha Consignacion, Realizado por, Comentarios, Estado
    # Columnas DB: sucursal, fecha_desde, fecha_hasta, monto, fecha_consignacion, realizado_por, comentarios, estado
    
    mapping = {
        'Sucursal': 'sucursal',
        'Fecha Desde': 'fecha_desde',
        'Fecha Hasta': 'fecha_hasta',
        'Monto': 'monto',
        'Fecha Consignacion': 'fecha_consignacion',
        'Realizado por': 'realizado_por',
        'Comentarios': 'comentarios',
        'Estado': 'estado'
    }
    
    df = df.rename(columns=mapping)
    
    # Limpiar datos: Reemplazar NaN por None para PostgreSQL
    df = df.where(pd.notnull(df), None)
    
    insert_query = """
    INSERT INTO tbl_depositos (
        sucursal, fecha_desde, fecha_hasta, monto, fecha_consignacion,
        realizado_por, comentarios, estado
    ) VALUES (
        %(sucursal)s, %(fecha_desde)s, %(fecha_hasta)s, %(monto)s, %(fecha_consignacion)s,
        %(realizado_por)s, %(comentarios)s, %(estado)s
    )
    """
    
    count = 0
    for _, row in df.iterrows():
        # Asegurarse de que las fechas sean objetos datetime o None
        # pandas ya debería haberlas convertido si son columnas de fecha
        db.execute_query(insert_query, row.to_dict())
        count += 1
        
    print(f"✅ Se importaron {count} depósitos.")

if __name__ == "__main__":
    db = PostgresManager()
    try:
        excel_file = "/Users/joslu/Downloads/Bitácora de Depósitos-2.xlsx"
        import_depositos(db, excel_file)
    finally:
        db.close_all_connections()
