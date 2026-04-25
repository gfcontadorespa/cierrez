import gspread
import os

class GoogleSheetsOAuthAPI:
    def __init__(self, client_secret_file='client_secret.json'):
        """
        Inicializa la conexión con Google Sheets usando OAuth2 (User Flow).
        :param client_secret_file: Ruta al archivo JSON del cliente OAuth.
        """
        if not os.path.exists(client_secret_file):
            raise FileNotFoundError(f"No se encontró el archivo: {client_secret_file}")
        
        # gspread.oauth buscará client_secret.json en ~/.config/gspread o en la ruta actual
        # y guardará el token de acceso localmente.
        self.client = gspread.oauth(
            credentials_filename=client_secret_file,
            # authorized_user_filename='authorized_user.json' # Opcional: nombre del archivo del token
        )

    def open_spreadsheet(self, sheet_name_or_url):
        """Abre una hoja de cálculo por su nombre o URL."""
        if sheet_name_or_url.startswith('https://'):
            return self.client.open_by_url(sheet_name_or_url)
        return self.client.open(sheet_name_or_url)

    def get_all_records(self, spreadsheet, worksheet_name=None):
        """Obtiene todos los registros de una pestaña."""
        worksheet = spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.get_worksheet(0)
        return worksheet.get_all_records()

    def update_cell(self, spreadsheet, row, col, value, worksheet_name=None):
        """Actualiza una celda específica."""
        worksheet = spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.get_worksheet(0)
        worksheet.update_cell(row, col, value)

    def append_row(self, spreadsheet, row_data, worksheet_name=None):
        """Añade una nueva fila al final."""
        worksheet = spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.get_worksheet(0)
        worksheet.append_row(row_data)
