# Intelligent Background Worker - Database schema adjusted for nullable fields
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

from datetime import datetime, time as dtime, timedelta, timezone
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
        
        # Historial de notificaciones para evitar spam
        self.last_summary_time = 0.0
        self.last_counts = (0, 0)
        self.last_health_check_date = None # type: ignore

    def get_panama_time(self):
        """
        Retorna la hora actual en GMT-5 (Panamá).
        """
        return datetime.now(timezone(timedelta(hours=-5)))

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

    def _is_ocr_confusion(self, manual_val, ai_val):
        """
        Calcula si la diferencia entre dos montos es excusable por un error común de OCR.
        Soporta confusión exacta de 1 carácter en pares conocidos como 5/6, 3/8, 1/7.
        """
        try:
            m_val = float(manual_val)
            a_val = float(ai_val)
        except ValueError:
            return False

        if abs(m_val - a_val) < 0.01:
            return True

        str_man = f"{m_val:.2f}"
        str_ai = f"{a_val:.2f}"

        if len(str_man) != len(str_ai):
            return False

        differences = 0
        confusions = {('5', '6'), ('6', '5'), ('3', '8'), ('8', '3'), ('1', '7'), ('7', '1'), ('0', '8'), ('8', '0')}

        for c1, c2 in zip(str_man, str_ai):
            if c1 != c2:
                differences += 1
                if (c1, c2) not in confusions:
                    return False

        return differences == 1

    def download_image(self, file_name):
        """
        Busca y descarga una imagen de Drive dentro de la carpeta configurada.
        """
        if not self.drive_service:
            return None

        try:
            folder_ids_str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
            folder_ids = [fid.strip() for fid in folder_ids_str.split(",") if fid.strip()]
            
            # Buscar el archivo en cada carpeta proporcionada
            file_id = None
            for fid in folder_ids:
                query = f"name = '{file_name}' and '{fid}' in parents"
                results = self.drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                items = results.get('files', [])
                if items:
                    file_id = items[0]['id']
                    break
            
            # Si no se encontró en las carpetas específicas, intentar búsqueda global (opcional/seguridad)
            if not file_id:
                query = f"name = '{file_name}'"
                results = self.drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
                items = results.get('files', [])
                if items:
                    file_id = items[0]['id']

            if not file_id:
                print(f"❌ Imagen no encontrada en ninguna carpeta de Drive: {file_name}")
                return None
            
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

    def process_pending_cierres(self, limit=20):
        """
        Busca registros en tblcierresz que tengan al menos una imagen pero no OCR procesado.
        Limitado a 'limit' registros por tanda para evitar consumo excesivo de créditos.
        """
        query = f"""
        SELECT 
            c.row_id, c.imagen_header, c.imagen_ventas, c.imagen_visa_mc, c.imagen_clave, 
            c.pos_visa_mc, c.pos_clave,
            c.invoice_number, c.invoice_date, s.etiqueta_suc
        FROM tblcierresz c
        LEFT JOIN tblsucursales s ON c.branch_id = s.branch_id
        WHERE (
            (c.imagen_header IS NOT NULL AND c.imagen_header != '') OR 
            (c.imagen_ventas IS NOT NULL AND c.imagen_ventas != '') OR 
            (c.imagen_visa_mc IS NOT NULL AND c.imagen_visa_mc != '') OR 
            (c.imagen_clave IS NOT NULL AND c.imagen_clave != '')
        )
        AND (c.ocr_raw_text IS NULL OR c.ocr_raw_text = '')
        AND (c.fecha_modifica >= NOW() - INTERVAL '2 days')
        LIMIT {limit};
        """
        pending = self.db.fetch_all(query)
        
        if not pending:
            return 0, False

        print(f"--- Procesando {len(pending)} cierres con múltiples imágenes ---")
        
        for record in pending:
            row_id = record[0]
            # Columnas 1 a 4 son las rutas de las imágenes
            image_paths_in_db = record[1:5]
            manual_visa = record[5] or 0.0
            manual_clave = record[6] or 0.0
            inv_number = record[7] or "N/A"
            inv_date = record[8] or "N/A"
            suc_name = record[9] or "Desconocida"
            
            local_paths = []
            print(f"Procesando cierre {row_id}")
            
            for img_path in image_paths_in_db:
                if img_path:
                    file_name = os.path.basename(img_path)
                    local_path = self.download_image(file_name)
                    if local_path:
                        local_paths.append(local_path)
            
            if not local_paths:
                print(f"⚠️ No se pudieron descargar imágenes para {row_id}")
                self.db.execute_query(
                    "UPDATE tblcierresz SET ocr_raw_text = '{\"error\": \"images_not_found_on_drive\"}', fecha_modifica = NOW() WHERE row_id = %s",
                    (row_id,)
                )
                continue
            
            # Llamamos a la AI con la lista de imágenes y el contexto manual
            extracted_data = self.ai.process_cierre(
                local_paths,
                expected_visa_mc=float(manual_visa),
                expected_clave=float(manual_clave)
            )
            
            if "error" in extracted_data:
                error_msg = str(extracted_data['error']).lower()
                print(f"❌ Error IA: {extracted_data['error']}")
                
                # MARCAR EN DB PARA NO REPETIR BUCLE INFINITO
                self.db.execute_query(
                    "UPDATE tblcierresz SET ocr_raw_text = %s, comentarios = %s, fecha_modifica = NOW() WHERE row_id = %s",
                    (json.dumps(extracted_data), f"❌ AI Error: {extracted_data['error']}", row_id)
                )
                
                if "insufficient_quota" in error_msg or "quota_exceeded" in error_msg:
                    print("⚠️ Créditos de OpenAI agotados. Solicitando pausa del trabajador.")
                    return len(pending), True # (count, should_pause)
                continue
            
            print(f"✅ Datos extraídos de {len(local_paths)} imágenes: {extracted_data}")
            
            # Lógica de comparación (Auditoría)
            ai_visa = float(extracted_data.get('pos_visa_mc') or 0.0)
            ai_clave = float(extracted_data.get('pos_clave') or 0.0)
            
            audit_msg = []
            has_diff = False
            # Comparar Visa/MC
            if self._is_ocr_confusion(manual_visa, ai_visa):
                if abs(float(manual_visa) - ai_visa) >= 0.01:
                    audit_msg.append("✅ Visa/MC OK (Tolerancia OCR aplicada)")
                else:
                    audit_msg.append("✅ Visa/MC OK")
            else:
                audit_msg.append(f"❌ Visa/MC Diff: AppSheet {manual_visa} vs Foto {ai_visa}")
                has_diff = True
            
            # Comparar Clave
            if self._is_ocr_confusion(manual_clave, ai_clave):
                if abs(float(manual_clave) - ai_clave) >= 0.01:
                    audit_msg.append("✅ Clave OK (Tolerancia OCR aplicada)")
                else:
                    audit_msg.append("✅ Clave OK")
            else:
                audit_msg.append(f"❌ Clave Diff: AppSheet {manual_clave} vs Foto {ai_clave}")
                has_diff = True

            # Combinar con posibles errores de validación de la IA
            final_comment = " | ".join(audit_msg)
            debug_val = extracted_data.get('debug_info')
            if debug_val:
                if isinstance(debug_val, dict):
                    debug_val = json.dumps(debug_val)
                final_comment += f" | IA Note: {debug_val}"

            # Si hay diferencia, enviar alerta por Telegram
            if has_diff:
                alert_text = (
                    f"🚨 *Alerta de Diferencia en Cierre Z* 🚨\n\n"
                    f"🏢 *Sucursal*: {suc_name}\n"
                    f"📅 *Fecha*: {inv_date}\n"
                    f"🧾 *Cierre #*: {inv_number}\n"
                    f"📌 *Row ID*: {row_id}\n\n"
                    f"🔍 *Auditoría*: {final_comment}"
                )
                self.send_telegram_alert(alert_text)

            # Actualizar Postgres (INCLUYENDO NUEVAS COLUMNAS DE AUDITORÍA)
            update_query = """
            UPDATE tblcierresz SET
                comentarios = %s,
                ocr_raw_text = %s,
                audit_pos_visa_mc = %s,
                audit_pos_clave = %s,
                audit_diff_visa_mc = %s,
                audit_diff_clave = %s,
                fecha_modifica = NOW()
            WHERE row_id = %s
            """
            
            params = (
                final_comment, 
                json.dumps(extracted_data),
                ai_visa,
                ai_clave,
                float(manual_visa) - ai_visa,
                float(manual_clave) - ai_clave,
                row_id
            )
            
            self.db.execute_query(update_query, params)
            print(f"✅ Registro {row_id} actualizado.")
            
            # Limpiar imágenes locales
            for lp in local_paths:
                if lp and os.path.exists(lp):
                    os.remove(lp)
        
        return len(pending), False

    def process_pending_depositos(self, limit=10):
        """
        Busca registros en tbl_depositos que tengan imagen pero no auditoría.
        """
        query = f"""
        SELECT d.deposito_id, d.adjunto, d.monto, d.branch_id, s.etiqueta_suc
        FROM tbl_depositos d
        LEFT JOIN tblsucursales s ON d.branch_id = s.branch_id
        WHERE (d.adjunto IS NOT NULL AND d.adjunto != '')
        AND (d.ocr_raw_text IS NULL OR d.ocr_raw_text = '')
        AND (d.fecha_modifica >= NOW() - INTERVAL '2 days')
        LIMIT {limit};
        """
        # Nota: sucursal fue eliminada de la tabla física, usamos branch_id para relaciones.
        pending = self.db.fetch_all(query)
        
        if not pending:
            return 0, False

        print(f"--- Procesando {len(pending)} depósitos bancarios ---")
        
        for record in pending:
            dep_id = record[0]
            adjunto_path = record[1]
            monto_manual = record[2] or 0.0
            branch_id = record[3]
            suc_name = record[4] or "Desconocida"
            
            print(f"Procesando depósito {dep_id}")
            
            file_name = os.path.basename(adjunto_path)
            local_path = self.download_image(file_name)
            
            if not local_path:
                print(f"⚠️ No se pudo descargar imagen para depósito {dep_id}")
                self.db.execute_query(
                    "UPDATE tbl_depositos SET ocr_raw_text = '{\"error\": \"image_not_found_on_drive\"}', fecha_modifica = NOW() WHERE deposito_id = %s",
                    (dep_id,)
                )
                continue
                
            extracted_data = self.ai.process_deposito(
                local_path,
                expected_monto=float(monto_manual)
            )
            
            if "error" in extracted_data:
                print(f"❌ Error IA en depósito: {extracted_data['error']}")
                # MARCAR EN DB
                self.db.execute_query(
                    "UPDATE tbl_depositos SET ocr_raw_text = %s, comentarios = %s, fecha_modifica = NOW() WHERE deposito_id = %s",
                    (json.dumps(extracted_data), f"❌ AI Error: {extracted_data['error']}", dep_id)
                )
                continue
                
            ai_monto = float(extracted_data.get('monto') or 0.0)
            ai_fecha = extracted_data.get('fecha') or "No detectada"
            
            diff = abs(float(monto_manual) - ai_monto)
            is_ok = self._is_ocr_confusion(monto_manual, ai_monto)
            
            if is_ok:
                if diff >= 0.01:
                    audit_msg = f"✅ Depósito OK - Tolerancia OCR (Foto: ${ai_monto}, Fecha: {ai_fecha})"
                else:
                    audit_msg = f"✅ Depósito OK (Foto: ${ai_monto}, Fecha: {ai_fecha})"
            else:
                audit_msg = f"❌ Diferencia Depósito: AppSheet ${monto_manual} vs Foto ${ai_monto} | Fecha Foto: {ai_fecha}"
                # Alerta Telegram
                alert_text = (
                    f"🏦 *Alerta de Diferencia en Depósito* 🏦\n\n"
                    f"🏢 *Sucursal*: {suc_name}\n"
                    f"📌 *Depósito ID*: {dep_id}\n\n"
                    f"🔍 *Auditoría*: {audit_msg}"
                )
                self.send_telegram_alert(alert_text)
                
            # Actualizar DB
            update_query = """
            UPDATE tbl_depositos SET
                comentarios = COALESCE(comentarios, '') || ' | ' || %s,
                ocr_raw_text = %s,
                audit_monto = %s,
                audit_diferencia = %s
            WHERE deposito_id = %s
            """
            params = (
                audit_msg,
                json.dumps(extracted_data),
                ai_monto,
                float(monto_manual) - ai_monto,
                dep_id
            )
            self.db.execute_query(update_query, params)
            print(f"✅ Depósito {dep_id} auditado.")
            
            # Limpiar
            if os.path.exists(local_path):
                os.remove(local_path)
            
        return len(pending), False

    def send_telegram_alert(self, message):
        """
        Envía una notificación a Telegram.
        """
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            print("⚠️ Telegram no configurado (Token o Chat ID ausente).")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            r = requests.post(url, json=payload)
            r.raise_for_status()
            print("📤 Alerta enviada a Telegram.")
        except Exception as e:
            print(f"❌ Error enviando alerta a Telegram: {e}")

    def get_pending_counts(self):
        """
        Cuenta rápidamente cuántos cierres y depósitos hay pendientes de auditar.
        """
        q_z = """
            SELECT count(*) FROM tblcierresz 
            WHERE (
                (imagen_header IS NOT NULL AND imagen_header != '') OR 
                (imagen_ventas IS NOT NULL AND imagen_ventas != '') OR 
                (imagen_visa_mc IS NOT NULL AND imagen_visa_mc != '') OR 
                (imagen_clave IS NOT NULL AND imagen_clave != '')
            )
            AND (ocr_raw_text IS NULL OR ocr_raw_text = '')
            AND (fecha_modifica >= NOW() - INTERVAL '2 days');
        """
        q_d = """
            SELECT count(*) FROM tbl_depositos 
            WHERE (adjunto IS NOT NULL AND adjunto != '')
            AND (ocr_raw_text IS NULL OR ocr_raw_text = '')
            AND (fecha_modifica >= NOW() - INTERVAL '2 days');
        """
        try:
            res_z = self.db.fetch_one(q_z)[0]
            res_d = self.db.fetch_one(q_d)[0]
            return res_z, res_d
        except Exception as e:
            print(f"❌ Error obteniendo conteos pendientes: {e}")
            return 0, 0

    def perform_daily_health_check(self, days_to_check=30):
        """
        Realiza una auditoría de integridad de los últimos N días.
        Busca días faltantes y duplicados para todas las sucursales activas.
        """
        print(f"🏥 Iniciando Auditoría de Salud de Datos (Últimos {days_to_check} días)...")
        
        # Rango de fechas (Excluyendo hoy para dar tiempo a registrar)
        end_date = self.get_panama_time().date() - timedelta(days=1)
        start_date = end_date - timedelta(days=days_to_check)
        all_dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        
        query_branches = "SELECT branch_id, etiqueta_suc FROM tblsucursales WHERE active = TRUE"
        branches = self.db.fetch_all(query_branches)
        
        # Obtener exclusiones del calendario especial para el rango
        query_excl = """
        SELECT fecha, branch_id, es_opcional 
        FROM tbl_calendario_especial 
        WHERE fecha BETWEEN %s AND %s
        """
        exclusions = self.db.fetch_all(query_excl, (start_date, end_date))
        
        # Mapeo de exclusiones: {(fecha, branch_id): es_opcional, (fecha, None): es_opcional}
        excl_map = {}
        for f, b, opt in exclusions:
            excl_map[(f, b)] = opt

        summary_lines = []
        branches_with_issues = 0
        
        for b_id, b_label in branches:
            query = """
            SELECT invoice_date 
            FROM tblcierresz 
            WHERE branch_id = %s 
            AND invoice_date BETWEEN %s AND %s
            ORDER BY invoice_date
            """
            res = self.db.fetch_all(query, (b_id, start_date, end_date))
            # Asegurar que sean objetos date (algunas configuraciones pueden devolver strings)
            dates_in_db = []
            for row in res:
                d = row[0]
                if isinstance(d, str):
                    try:
                        d = datetime.strptime(d, '%Y-%m-%d').date()
                    except:
                        continue
                dates_in_db.append(d)
            
            # Faltantes
            missing_raw = [d for d in all_dates if d not in dates_in_db]
            
            # Filtrar faltantes usando el calendario especial
            missing = []
            for d in missing_raw:
                # Si existe una exclusión global (branch_id IS NULL) o específica para esta rama
                is_excluded = excl_map.get((d, None)) or excl_map.get((d, b_id))
                if not is_excluded:
                    missing.append(d)

            # Duplicados
            from collections import Counter
            duplicates = [d for d, count in Counter(dates_in_db).items() if count > 1]
            
            if missing or duplicates:
                branches_with_issues += 1
                branch_msg = f"📍 *{b_label}*:\n"
                if missing:
                    # Agrupar fechas para no saturar el mensaje si son muchas
                    if len(missing) > 5:
                        branch_msg += f"  - ⚠️ {len(missing)} días faltantes.\n"
                    else:
                        branch_msg += f"  - ⚠️ Faltan: {', '.join(d.strftime('%d/%m') for d in missing)}\n"
                if duplicates:
                    branch_msg += f"  - 👯 Duplicados: {', '.join(d.strftime('%d/%m') for d in duplicates)}\n"
                summary_lines.append(branch_msg)

        # Construir y enviar alerta
        header = f"📋 *REPORTE DIARIO DE SALUD* ({end_date.strftime('%d/%m/%Y')})\n"
        header += f"Rango: {start_date.strftime('%d/%m')} al {end_date.strftime('%d/%m')}\n\n"
        
        if not summary_lines:
            header += "✅ ¡Todo en orden! No se encontraron faltantes ni duplicados."
        else:
            header += f"Se encontraron inconsistencias en {branches_with_issues} sucursales:\n\n"
            header += "\n".join(summary_lines)
            
        self.send_telegram_alert(header)
        print("✅ Auditoría de salud completada y enviada.")

    def run(self, interval=60):
        print(f"🚀 Intelligent Worker iniciado (GMT-5). Polling cada {interval} segundos...")
        while True:
            try:
                now_panama = self.get_panama_time()
                current_time = now_panama.time()
                current_date = now_panama.date()

                # --- 1. SUSPENSIÓN (12:00 AM - 7:00 AM) ---
                if dtime(0, 0) <= current_time <= dtime(7, 0):
                    if interval != 1800: # Si no estamos en modo ahorro, avisar
                        print(f"💤 Horario de suspensión (00:00-07:00). Durmiendo...")
                    time.sleep(1800) # Dormir 30 min
                    continue

                # --- 2. AUDITORÍA DIARIA (9:00 PM) ---
                if current_time >= dtime(21, 0) and self.last_health_check_date != current_date:
                    self.perform_daily_health_check(days_to_check=30)
                    self.last_health_check_date = current_date

                # --- 3. PROCESAMIENTO NORMAL ---
                # Prediction (Antes de procesar)
                count_z, count_d = self.get_pending_counts()
                
                current_time = time.time()
                counts_changed = (count_z, count_d) != self.last_counts
                
                if (count_z > 0 or count_d > 0) and (counts_changed or (current_time - self.last_summary_time > 3600)):
                    msg = "🤖 *Intelligent Worker Activo*\n\n"
                    if count_z > 0:
                        msg += f"📦 *Cierres Z*: {count_z} pendientes\n"
                    if count_d > 0:
                        msg += f"🏦 *Depósitos*: {count_d} pendientes\n"
                    msg += "\n⏳ Empezando auditoría..."
                    self.send_telegram_alert(msg)
                    self.last_summary_time = current_time
                    self.last_counts = (count_z, count_d)
                
                elif (count_z == 0 and count_d == 0) and self.last_counts != (0, 0):
                    # Acabamos de vaciar la cola
                    self.send_telegram_alert("✅ *Auditoría completada*\n\nTodos los registros pendientes han sido procesados. El trabajador ahora está en modo de espera. 💤")
                    self.last_counts = (0, 0)
                    self.last_summary_time = current_time

                # 2. Procesar
                if count_z > 0:
                    _, should_pause = self.process_pending_cierres()
                    if should_pause:
                        pause_time = 3600
                        print(f"⏸️ Pausado por 1 hora por créditos.")
                        time.sleep(pause_time)
                        continue

                if count_d > 0:
                    self.process_pending_depositos()
                
            except Exception as e:
                print(f"❌ Error en el loop del worker: {e}")
            
            time.sleep(interval)

if __name__ == "__main__":
    worker = IntelligentWorker()
    # Para probar una vez:
    # worker.process_pending_cierres()
    # Para correr continuo:
    worker.run(interval=30)
