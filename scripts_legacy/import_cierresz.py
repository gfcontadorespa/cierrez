import pandas as pd
import os
from db_manager import PostgresManager

def import_cierresz(excel_path):
    if not os.path.exists(excel_path):
        print(f"Error: No se encontró el archivo Excel en {excel_path}")
        return

    print(f"Leyendo datos desde {excel_path}...")
    df = pd.read_excel(excel_path)
    
    # Mapeo de columnas (Excel -> DB)
    mapping = {
        'Row ID': 'row_id',
        'Customer Name': 'customer_name',
        'num_cierre': 'num_cierre',
        'Invoice Date': 'invoice_date',
        'Ventas Gravables': 'ventas_gravables',
        'Ventas Exentas': 'ventas_exentas',
        'Impuesto': 'impuesto',
        'total_ingresos': 'total_ingresos',
        'ventas_netas': 'ventas_netas',
        'Efectivo': 'efectivo',
        'Yappy': 'yappy',
        '[POS] Clave': 'pos_clave',
        '[POS] Visa/MC': 'pos_visa_mc',
        'Cupones': 'cupones',
        'Otros': 'otros',
        'Reembolso Caja': 'reembolso_caja',
        'Total_Pagos': 'total_pagos',
        'Dif.': 'dif',
        'Invoice Number': 'invoice_number',
        'Comentarios': 'comentarios',
        'Estado': 'estado',
        'Etiqueta_Sucursal': 'etiqueta_sucursal',
        'Datáfono': 'datafono',
        'Imagen': 'imagen',
        'fecha_adicion': 'fecha_adicion',
        'fecha_modifica': 'fecha_modifica',
        'Depositado': 'depositado',
        'fecha_deposito': 'fecha_deposito'
    }
    
    # Renombrar columnas para que coincidan con la DB
    df = df.rename(columns=mapping)
    
    # Filtrar solo las columnas que están en el mapeo
    df = df[list(mapping.values())]
    
    # ELIMINAR FILAS VACÍAS (donde row_id es nulo)
    df = df.dropna(subset=['row_id'])
    
    db = PostgresManager()
    try:
        print(f"Preparando {len(df)} registros para tblcierresz...")
        
        insert_query = f"""
        INSERT INTO tblcierresz ({", ".join(mapping.values())})
        VALUES ({", ".join(["%s"] * len(mapping))})
        ON CONFLICT (row_id) DO UPDATE SET
            {", ".join([f"{col} = EXCLUDED.{col}" for col in mapping.values() if col != "row_id"])}
        """
        
        # Convertir dataframe a lista de tuplas, manejando NaT/NaN
        params_list = []
        for _, row in df.iterrows():
            params_list.append(tuple(None if pd.isna(val) else val for val in row.values))
            
        print("Iniciando inserción por lotes...")
        db.execute_batch(insert_query, params_list, page_size=200)
        print(f"✅ Se importaron {len(params_list)} cierres con éxito.")

    except Exception as e:
        print(f"❌ Error durante la importación: {e}")
    finally:
        db.close_all_connections()

if __name__ == "__main__":
    excel_file = "/Users/joslu/Downloads/CierresZ.xlsx"
    import_cierresz(excel_file)
