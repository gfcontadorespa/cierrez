import os
import time
import requests
import json
from dotenv import load_dotenv
from db_manager import PostgresManager
from ai_vision_agent import AIVisionAgent
from appsheet_api_client import AppSheetAPI
import gspread
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

from google.oauth2.credentials import Credentials

load_dotenv()

class IntelligentWorker:
    def __init__(self):
        self.db = PostgresManager()
        self.ai = AIVisionAgent()
        self.appsheet = AppSheetAPI()
        self.temp_dir = "temp_images"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        # Drive Service setup
        self.drive_service = self._init_drive_service()

    def _init_drive_service(self):
        try:
            # 1. Intentar cargar desde variable de entorno (Ideal para Easypanel/Docker)
            creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
            if creds_json:
                print("🔑 Cargando credenciales de Google desde variable de entorno...")
                creds_dict = json.loads(creds_json)
                creds = Credentials.from_authorized_user_info(creds_dict)
                return build('drive', 'v3', credentials=creds)

            # 2. Intentar cargar desde archivo local (Desarrollo)
            authorized_user_file = os.path.expanduser('~/.config/gspread/authorized_user.json')
            if os.path.exists(authorized_user_file):
                print(f"📄 Cargando credenciales de Google desde archivo: {authorized_user_file}")
                creds = Credentials.from_authorized_user_file(authorized_user_file)
                return build('drive', 'v3', credentials=creds)
            
            print("⚠️ No se encontraron credenciales de Google (GOOGLE_CREDENTIALS_JSON o authorized_user.json).")
            return None
        except Exception as e:
            print(f"❌ Error inicializando Drive Service: {e}")
            return None

    def download_image(self, file_name):
        """
        Busca y descarga una imagen de Drive dentro de la carpeta configurada.
        """
        if not self.drive_service:
            return None

        try:
            folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
            # Buscar el archivo por nombre y opcionalmente por carpeta padre
            query = f"name = '{file_name}'"
            if folder_id:
                query += f" and '{folder_id}' in parents"
                
            results = self.drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])
            
            if not items:
                print(f"❌ Imagen no encontrada en Drive: {file_name}")
                return None
            
            file_id = items[0]['id']
            request = self.drive_service.files().get_media(fileId=file_id)
            
            output_path = os.path.join(self.temp_dir, file_name)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            with open(output_path, 'wb') as f:
                f.write(fh.getvalue())
            
            return output_path
        except Exception as e:
            print(f"❌ Error descargando imagen {file_name}: {e}")
            return None

    def process_pending_cierres(self):
        """
        Busca registros en tblcierresz que tengan al menos una imagen pero no OCR procesado.
        """
        query = """
        SELECT row_id, imagen, imagen_header, imagen_ventas, imagen_visa_mc, imagen_clave, etiqueta_sucursal 
        FROM tblcierresz 
        WHERE (imagen IS NOT NULL OR imagen_header IS NOT NULL OR imagen_ventas IS NOT NULL OR imagen_visa_mc IS NOT NULL OR imagen_clave IS NOT NULL)
        AND (ocr_raw_text IS NULL OR ocr_raw_text = '');
        """
        pending = self.db.fetch_all(query)
        
        if not pending:
            return

        print(f"--- Procesando {len(pending)} cierres con múltiples imágenes ---")
        
        for record in pending:
            row_id = record[0]
            # Columnas 1 a 5 son las rutas de las imágenes
            image_paths_in_db = record[1:6]
            sucursal = record[6]
            
            local_paths = []
            print(f"Procesando cierre {row_id} ({sucursal})")
            
            for img_path in image_paths_in_db:
                if img_path:
                    file_name = os.path.basename(img_path)
                    local_path = self.download_image(file_name)
                    if local_path:
                        local_paths.append(local_path)
            
            if not local_paths:
                continue
            
            # Llamamos a la AI con la lista de imágenes
            extracted_data = self.ai.process_cierre(local_paths)
            
            if "error" in extracted_data:
                print(f"❌ Error IA: {extracted_data['error']}")
                continue
            
            print(f"✅ Datos extraídos de {len(local_paths)} imágenes: {extracted_data}")
            
            # Actualizar Postgres
            update_query = """
            UPDATE tblcierresz SET
                num_cierre = %s,
                ventas_gravables = %s,
                ventas_exentas = %s,
                impuesto = %s,
                total_ingresos = %s,
                efectivo = %s,
                yappy = %s,
                pos_clave = %s,
                pos_visa_mc = %s,
                total_pagos = %s,
                ocr_raw_text = %s,
                fecha_modifica = NOW()
            WHERE row_id = %s
            """
            
            params = (
                extracted_data.get('num_cierre'),
                extracted_data.get('ventas_gravables'),
                extracted_data.get('ventas_exentas'),
                extracted_data.get('impuesto'),
                extracted_data.get('total_ingresos'),
                extracted_data.get('efectivo'),
                extracted_data.get('yappy'),
                extracted_data.get('pos_clave'),
                extracted_data.get('pos_visa_mc'),
                extracted_data.get('total_pagos'),
                json.dumps(extracted_data),
                row_id
            )
            
            self.db.execute_query(update_query, params)
            print(f"✅ Registro {row_id} actualizado.")
            
            # Limpiar imágenes locales
            for lp in local_paths:
                if os.path.exists(lp):
                    os.remove(lp)

    def run(self, interval=60):
        print(f"🚀 Intelligent Worker iniciado. Polling cada {interval} segundos...")
        while True:
            try:
                self.process_pending_cierres()
            except Exception as e:
                print(f"❌ Error en el loop del worker: {e}")
            
            time.sleep(interval)

if __name__ == "__main__":
    worker = IntelligentWorker()
    # Para probar una vez:
    # worker.process_pending_cierres()
    # Para correr continuo:
    worker.run(interval=30)
