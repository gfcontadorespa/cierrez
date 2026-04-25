from gsheets_api_oauth import GoogleSheetsOAuthAPI
from datetime import datetime, timedelta
import json

def analyze_december():
    try:
        api = GoogleSheetsOAuthAPI('client_secret.json')
        SHEET_URL = 'https://docs.google.com/spreadsheets/d/1ytAlhLi5asOUdGaVQc5cSgHguABMUq4aJTYlbe1GZ_E/edit?gid=231010039#gid=231010039'
        
        print(f"Obteniendo datos de la hoja...")
        sheet = api.open_spreadsheet(SHEET_URL)
        records = api.get_all_records(sheet)
        
        # Parámetros del periodo
        start_date = datetime(2025, 12, 1)
        end_date = datetime(2025, 12, 31)
        
        # Generar lista de todos los días en diciembre 2025
        all_days = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') for x in range((end_date - start_date).days + 1)]
        
        # Estructuras para el análisis
        sucursales_data = {} # {sucursal: {fecha: record}}
        
        for record in records:
            # Limpiar y validar fecha
            date_str = record.get('Invoice Date', '')
            if not date_str:
                continue
                
            try:
                # Intentar parsear la fecha para asegurar formato
                curr_date = datetime.strptime(date_str, '%Y-%m-%d')
                if start_date <= curr_date <= end_date:
                    sucursal = record.get('Etiqueta_Sucursal', 'Sin Sucursal')
                    if sucursal not in sucursales_data:
                        sucursales_data[sucursal] = {}
                    sucursales_data[sucursal][date_str] = record
            except ValueError:
                continue

        # Reporte
        print("\n" + "="*50)
        print(" REPORTE ANALÍTICO: DICIEMBRE 2025")
        print("="*50)
        
        total_general = 0
        
        # Ordenar sucursales alfabéticamente
        for sucursal in sorted(sucursales_data.keys()):
            data = sucursales_data[sucursal]
            
            # 1. Calcular ingresos
            ingresos_sucursal = sum(float(str(r.get('total_ingresos', 0)).replace(',', '')) for r in data.values())
            total_general += ingresos_sucursal
            
            # 2. Identificar fechas faltantes
            missing_dates = [day for day in all_days if day not in data]
            
            print(f"\n📍 SUCURSAL: {sucursal}")
            print(f"   💰 Total Ingresos: ${ingresos_sucursal:,.2f}")
            
            if missing_dates:
                print(f"   ⚠️ Facturas Faltantes ({len(missing_dates)}):")
                # Agrupar por rangos si son muchos, o simplemente listar
                for d in missing_dates:
                    print(f"      - {d}")
            else:
                print(f"   ✅ Todas las facturas están presentes (31/31).")
                
        print("\n" + "="*50)
        print(f"💵 TOTAL GENERAL DEL PERIODO: ${total_general:,.2f}")
        print("="*50 + "\n")

    except Exception as e:
        print(f"Ocurrió un error durante el análisis: {e}")

if __name__ == "__main__":
    analyze_december()
