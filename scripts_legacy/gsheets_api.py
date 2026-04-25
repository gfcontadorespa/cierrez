import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os

class GoogleSheetsAPI:
    def __init__(self, credentials_file='credentials.json'):
        """
        Inicializa la conexión con Google Sheets.
        :param credentials_file: Ruta al archivo JSON de credenciales de la Cuenta de Servicio.
        """
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials_file = credentials_file
        self.creds = self._get_credentials()
        self.client = gspread.authorize(self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)

    def _get_credentials(self):
        """Obtiene las credenciales de la Cuenta de Servicio."""
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(f"No se encontró el archivo de credenciales: {self.credentials_file}")
        return ServiceAccountCredentials.from_json_keyfile_name(self.credentials_file, self.scope)

    def _authenticate(self):
        """Manteniendo compatibilidad si se usa externamente, aunque el init ya lo hace."""
        return self.client

    def open_spreadsheet(self, sheet_name_or_url):
        """
        Abre una hoja de cálculo por su nombre o URL.
        :param sheet_name_or_url: Nombre o URL completa de la hoja.
        """
        if sheet_name_or_url.startswith('https://'):
            return self.client.open_by_url(sheet_name_or_url)
        return self.client.open(sheet_name_or_url)

    def get_all_records(self, spreadsheet, worksheet_name=None):
        """
        Obtiene todos los registros de una pestaña (worksheet).
        :param spreadsheet: Objeto spreadsheet abierto.
        :param worksheet_name: Nombre de la pestaña (opcional, usa la primera por defecto).
        """
        worksheet = spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.get_worksheet(0)
        return worksheet.get_all_records()

    def update_cell(self, spreadsheet, row, col, value, worksheet_name=None):
        """
        Actualiza una celda específica.
        :param row: Fila (1-indexed)
        :param col: Columna (1-indexed)
        :param value: Nuevo valor
        """
        worksheet = spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.get_worksheet(0)
        worksheet.update_cell(row, col, value)

    def append_row(self, spreadsheet, row_data, worksheet_name=None):
        """
        Añade una nueva fila al final de los datos.
        :param row_data: Lista de valores para la nueva fila.
        """
        worksheet = spreadsheet.worksheet(worksheet_name) if worksheet_name else spreadsheet.get_worksheet(0)
        worksheet.append_row(row_data)

    def download_file(self, file_id, output_path):
        """
        Descarga un archivo de Google Drive por su ID.
        :param file_id: ID del archivo en Google Drive.
        :param output_path: Ruta local donde guardar el archivo.
        """
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Descargando {file_id}: {int(status.progress() * 100)}%.")
        
        with open(output_path, 'wb') as f:
            f.write(fh.getvalue())
        print(f"Archivo guardado en: {output_path}")

    def find_file_by_name(self, name):
        """
        Busca un archivo por nombre en Drive y retorna su ID.
        Útil para encontrar imágenes si AppSheet solo da el nombre relativo.
        """
        query = f"name = '{name}'"
        results = self.drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        if not items:
            return None
        return items[0]['id']
