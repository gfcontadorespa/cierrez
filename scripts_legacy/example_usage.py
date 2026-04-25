from gsheets_api_oauth import GoogleSheetsOAuthAPI
import json

def run_example():
    try:
        # 1. Inicializar la API (OAuth2 - Abrirá el navegador la primera vez)
        print("Conectando con Google Sheets mediante su cuenta de Google...")
        api = GoogleSheetsOAuthAPI('client_secret.json')
        
        # 2. Abrir la hoja (Reemplaza con tu URL o Nombre)
        # IMPORTANTE: Debes haber compartido la hoja con el email de la service account.
        SHEET_URL = 'https://docs.google.com/spreadsheets/d/1ytAlhLi5asOUdGaVQc5cSgHguABMUq4aJTYlbe1GZ_E/edit?gid=231010039#gid=231010039'
        
        if SHEET_URL == 'ESCRIBE_AQUI_LA_URL_DE_TU_HOJA':
            print("\n[AVISO] Para probar este script:")
            print("1. Coloca tu 'credentials.json' en esta carpeta.")
            print("2. Pega la URL de tu Google Sheet en la variable SHEET_URL en 'example_usage.py'.")
            print("3. Comparte tu Google Sheet con el email de la service account.")
            return

        sheet = api.open_spreadsheet(SHEET_URL)
        
        # 3. Leer datos
        print(f"Leyendo datos de: {sheet.title}")
        records = api.get_all_records(sheet)
        
        print("\nPrimeros 5 registros:")
        for i, record in enumerate(records[:5]):
            print(f"{i+1}: {record}")

        # 4. Insertar una fila de prueba
        # api.append_row(sheet, ["Dato 1", "Dato 2", "Dato 3"])
        # print("\nFila de prueba añadida.")

    except FileNotFoundError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nHa ocurrido un error: {e}")

if __name__ == "__main__":
    run_example()
