# Intelligent Worker for SaaS Multi-Tenant
import os
import time
import requests
import json
from dotenv import load_dotenv
from db_manager import PostgresManager
from ai_vision_agent import AIVisionAgent
from datetime import datetime, time as dtime, timedelta, timezone

load_dotenv()

class IntelligentWorker:
    def __init__(self):
        self.db = PostgresManager()
        self.ai = AIVisionAgent()
        
        self.last_summary_time = 0.0
        self.last_counts = 0
        self.last_health_check_date = None

    def get_panama_time(self):
        return datetime.now(timezone(timedelta(hours=-5)))

    def send_resend_email(self, to_email, subject, html_content):
        resend_api_key = os.getenv('RESEND_API_KEY')
        if not resend_api_key:
            print("⚠️ RESEND_API_KEY not found. Cannot send email.")
            return

        headers = {
            'Authorization': f'Bearer {resend_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "from": "Cierre Z <cierrez@gfcontadorespa.com>",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }

        try:
            response = requests.post('https://api.resend.com/emails', headers=headers, json=payload)
            response.raise_for_status()
            print(f"📧 Correo enviado a {to_email}")
        except Exception as e:
            print(f"❌ Error enviando correo: {e}")

    def _is_ocr_confusion(self, manual_val, ai_val):
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

    def get_pending_counts(self):
        query = """
            SELECT count(*) FROM tbl_cierres_z_master 
            WHERE ai_processed = FALSE 
            AND status = 'unbalanced'
            AND (image_url IS NOT NULL OR pos_receipt_url IS NOT NULL)
            AND created_at >= NOW() - INTERVAL '2 days';
        """
        try:
            res = self.db.fetch_one(query)
            return res[0] if res else 0
        except Exception as e:
            print(f"❌ Error obteniendo conteos pendientes: {e}")
            return 0

    def process_pending_cierres(self, limit=20):
        query = f"""
            SELECT 
                c.id, c.company_id, c.branch_id, c.z_number, c.date_closed,
                c.image_url, c.pos_receipt_url, c.deposit_receipt_url,
                b.name as branch_name, comp.name as company_name
            FROM tbl_cierres_z_master c
            LEFT JOIN tbl_branches b ON c.branch_id = b.id
            LEFT JOIN tbl_companies comp ON c.company_id = comp.id
            WHERE c.ai_processed = FALSE
            AND c.status = 'unbalanced'
            AND (c.image_url IS NOT NULL OR c.pos_receipt_url IS NOT NULL)
            AND c.created_at >= NOW() - INTERVAL '2 days'
            LIMIT {limit};
        """
        pending = self.db.fetch_all(query)
        if not pending:
            return 0, False

        print(f"--- Procesando {len(pending)} cierres SaaS con AI ---")

        for record in pending:
            cierre_id = record[0]
            company_id = record[1]
            branch_id = record[2]
            z_number = record[3]
            date_closed = record[4]
            image_url = record[5]
            pos_url = record[6]
            deposit_url = record[7]
            branch_name = record[8] or "Sucursal Desconocida"
            company_name = record[9] or "Empresa Desconocida"

            print(f"Procesando cierre {cierre_id} (Z: {z_number}) de {company_name}")

            # Get manual payment methods expected amounts
            pm_query = """
                SELECT p.name, p.amount 
                FROM tbl_cierres_z_payments p
                LEFT JOIN tbl_payment_methods m ON p.payment_method_id = m.id
                WHERE p.cierre_id = %s
            """
            payments = self.db.fetch_all(pm_query, (cierre_id,))
            expected_visa_mc = 0.0
            expected_clave = 0.0
            
            for pm_name, pm_amount in payments:
                name_lower = pm_name.lower() if pm_name else ""
                if "visa" in name_lower or "master" in name_lower or "credito" in name_lower:
                    expected_visa_mc += float(pm_amount or 0)
                elif "clave" in name_lower or "debito" in name_lower:
                    expected_clave += float(pm_amount or 0)

            image_urls = []
            if image_url: image_urls.append(image_url)
            if pos_url: image_urls.append(pos_url)
            if deposit_url: image_urls.append(deposit_url)

            if not image_urls:
                self.db.execute_query(
                    "UPDATE tbl_cierres_z_master SET ai_processed = TRUE, ai_comments = '❌ No images provided' WHERE id = %s",
                    (cierre_id,)
                )
                continue

            extracted_data = self.ai.process_cierre(
                image_urls,
                expected_visa_mc=expected_visa_mc,
                expected_clave=expected_clave
            )

            if "error" in extracted_data:
                error_msg = str(extracted_data['error']).lower()
                print(f"❌ Error IA: {error_msg}")
                self.db.execute_query(
                    "UPDATE tbl_cierres_z_master SET ai_processed = TRUE, ai_comments = %s WHERE id = %s",
                    (f"❌ AI Error: {extracted_data['error']}", cierre_id)
                )
                if "insufficient_quota" in error_msg or "quota_exceeded" in error_msg:
                    return len(pending), True
                continue

            ai_visa = float(extracted_data.get('pos_visa_mc') or 0.0)
            ai_clave = float(extracted_data.get('pos_clave') or 0.0)

            audit_msg = []
            has_diff = False
            
            # Compare Visa/MC
            if self._is_ocr_confusion(expected_visa_mc, ai_visa):
                audit_msg.append("✅ Visa/MC OK")
            else:
                audit_msg.append(f"❌ Visa/MC Diferencia: Reportado ${expected_visa_mc} vs AI ${ai_visa}")
                has_diff = True

            # Compare Clave
            if self._is_ocr_confusion(expected_clave, ai_clave):
                audit_msg.append("✅ Clave OK")
            else:
                audit_msg.append(f"❌ Clave Diferencia: Reportado ${expected_clave} vs AI ${ai_clave}")
                has_diff = True

            final_comment = " | ".join(audit_msg)
            debug_val = extracted_data.get('debug_info', '')
            if debug_val:
                final_comment += f" | Info: {debug_val}"

            # Ensure we mark as balanced if AI found no differences, or keep unbalanced
            new_status = 'unbalanced' if has_diff else 'balanced'

            update_query = """
                UPDATE tbl_cierres_z_master SET
                    ai_processed = TRUE,
                    ai_comments = %s,
                    status = %s
                WHERE id = %s
            """
            self.db.execute_query(update_query, (final_comment, new_status, cierre_id))

            if has_diff:
                self.send_alert_to_company_admins(company_id, company_name, branch_name, date_closed, z_number, final_comment)

        return len(pending), False

    def send_alert_to_company_admins(self, company_id, company_name, branch_name, date_closed, z_number, final_comment):
        # Fetch admins for this company
        admin_query = """
            SELECT u.email 
            FROM tbl_company_users cu
            JOIN tbl_users u ON cu.user_id = u.id
            WHERE cu.company_id = %s AND (cu.role = 'admin' OR cu.role = 'owner')
        """
        admins = self.db.fetch_all(admin_query, (company_id,))
        if not admins:
            return

        subject = f"🚨 Diferencia Detectada por IA: Cierre Z #{z_number}"
        html_content = f"""
        <h2>Alerta de Diferencia en Cierre Z</h2>
        <p>Nuestro modelo de Inteligencia Artificial ha detectado una discrepancia entre lo reportado manualmente y lo leído en los comprobantes físicos (fotos).</p>
        <ul>
            <li><b>Empresa:</b> {company_name}</li>
            <li><b>Sucursal:</b> {branch_name}</li>
            <li><b>Fecha de Cierre:</b> {date_closed}</li>
            <li><b>Cierre Z Número:</b> {z_number}</li>
        </ul>
        <p><b>🔍 Resultado de la Auditoría:</b><br/>
        {final_comment}
        </p>
        <p>Por favor revise este cierre en su panel de administración.</p>
        """

        for (email,) in admins:
            self.send_resend_email(email, subject, html_content)

    def run(self, interval=60):
        print(f"🚀 SaaS Intelligent Worker iniciado. Polling cada {interval} segundos...")
        while True:
            try:
                count = self.get_pending_counts()
                if count > 0:
                    _, should_pause = self.process_pending_cierres()
                    if should_pause:
                        print("⏸️ Pausado por límite de créditos IA.")
                        time.sleep(3600)
                        continue
            except Exception as e:
                print(f"❌ Error en el loop del worker: {e}")
            time.sleep(interval)

if __name__ == "__main__":
    worker = IntelligentWorker()
    worker.run(interval=30)
