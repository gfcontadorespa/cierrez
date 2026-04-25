from fastapi import FastAPI, HTTPException, File, UploadFile, APIRouter
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from pydantic import BaseModel
import boto3
import uuid
import jwt
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import resend
import pandas as pd
from io import BytesIO
from datetime import datetime
import base64

load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

# Añadir el directorio padre al sys.path para poder importar db_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_manager import PostgresManager

app = FastAPI(title="Validador Cierres Z API")

# Configurar CORS para permitir peticiones desde Vite (normalmente puerto 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción se debe restringir al dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = PostgresManager()

api_router = APIRouter(prefix="/api")


@api_router.get("/")
def read_root():
    return {"message": "API Validador Cierres Z funcionando correctamente"}


class GoogleToken(BaseModel):
    token: str

@api_router.post("/auth/google")
def google_auth(data: GoogleToken):
    try:
        # Validate the token with Google
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not client_id:
            raise HTTPException(status_code=500, detail="Google Client ID not configured")
            
        idinfo = id_token.verify_oauth2_token(data.token, google_requests.Request(), client_id)
        
        email = idinfo['email'].lower()
        name = idinfo.get('name', email.split('@')[0])
        
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                # Check if user exists (case insensitive)
                cur.execute("SELECT id, is_global_admin, active FROM tbl_users WHERE LOWER(email) = %s", (email,))
                user_row = cur.fetchone()
                
                if not user_row:
                    raise HTTPException(status_code=403, detail=f"Usuario '{email}' no registrado en el sistema (DB: {os.getenv('DB_HOST')})")
                
                if not user_row[2]: # active
                    raise HTTPException(status_code=403, detail="User account is deactivated")
                
                # Marcar como confirmado (guardar google_id) si no lo tiene
                google_sub = idinfo.get('sub')
                if google_sub:
                    cur.execute("UPDATE tbl_users SET google_id = %s WHERE id = %s AND google_id IS NULL", (google_sub, user_row[0]))
                    conn.commit()

                # Obtener company_id (si tiene una compañía asignada)
                cur.execute("SELECT company_id FROM tbl_company_users WHERE user_id = %s LIMIT 1", (user_row[0],))
                comp_row = cur.fetchone()
                company_id = comp_row[0] if comp_row else None
                
                # Return session info (In production, generate a JWT here)
                return {
                    "access_token": f"fake-jwt-for-{email}",
                    "user": {
                        "id": user_row[0],
                        "email": email,
                        "name": name,
                        "is_global_admin": user_row[1],
                        "company_id": company_id
                    }
                }
        finally:
            db.release_connection(conn)
    except ValueError:
        # Invalid token
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MicrosoftToken(BaseModel):
    token: str

@api_router.post("/auth/microsoft")
def microsoft_auth(data: MicrosoftToken):
    try:
        # Decode the token without verifying the signature for now (relies on HTTPS and MSAL)
        # In a strict production environment, you should fetch the JWKS from Microsoft and verify.
        unverified_claims = jwt.decode(data.token, options={"verify_signature": False})
        
        email = unverified_claims.get('preferred_username', '').lower()
        if not email:
            email = unverified_claims.get('email', '').lower()
            
        if not email:
            raise HTTPException(status_code=400, detail="Token does not contain an email address")
            
        name = unverified_claims.get('name', email.split('@')[0])
        
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                # Check if user exists (case insensitive)
                cur.execute("SELECT id, is_global_admin, active FROM tbl_users WHERE LOWER(email) = %s", (email,))
                user_row = cur.fetchone()
                
                if not user_row:
                    raise HTTPException(status_code=403, detail=f"Usuario '{email}' no registrado en el sistema")
                
                if not user_row[2]: # active
                    raise HTTPException(status_code=403, detail="User account is deactivated")
                
                # Marcar como confirmado (guardar microsoft_id/google_id)
                sub_id = unverified_claims.get('oid') or unverified_claims.get('sub')
                if sub_id:
                    cur.execute("UPDATE tbl_users SET google_id = %s WHERE id = %s AND google_id IS NULL", (sub_id, user_row[0]))
                    conn.commit()

                # Obtener company_id
                cur.execute("SELECT company_id FROM tbl_company_users WHERE user_id = %s LIMIT 1", (user_row[0],))
                comp_row = cur.fetchone()
                company_id = comp_row[0] if comp_row else None
                
                return {
                    "access_token": f"fake-jwt-for-{email}",
                    "user": {
                        "id": user_row[0],
                        "email": email,
                        "name": name,
                        "is_global_admin": user_row[1],
                        "company_id": company_id
                    }
                }
        finally:
            db.release_connection(conn)
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid Microsoft token")
    except HTTPException:
        raise
    except Exception as e:
        print("Microsoft Auth Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/dashboard/metrics")
def get_dashboard_metrics(company_id: int = 1):
    try:
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                from datetime import datetime
                today = datetime.now().strftime('%Y-%m-%d')
                
                # 1. Total Sales Today
                cur.execute("SELECT COALESCE(SUM(total_receipt), 0), COALESCE(SUM(difference_amount), 0) FROM tbl_cierres_z_master WHERE company_id = %s AND date_closed = %s", (company_id, today))
                today_stats = cur.fetchone()
                total_sales_today = float(today_stats[0])
                total_difference_today = float(today_stats[1])
                
                # 2. Closure Rate (Branches closed today vs Total active branches)
                cur.execute("SELECT COUNT(DISTINCT branch_id) FROM tbl_cierres_z_master WHERE company_id = %s AND date_closed = %s", (company_id, today))
                closed_branches = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM tbl_branches WHERE company_id = %s AND active = TRUE", (company_id,))
                total_branches = cur.fetchone()[0]
                
                # 3. Weekly Trend (Last 7 days)
                cur.execute("""
                    SELECT date_closed, SUM(total_receipt) 
                    FROM tbl_cierres_z_master 
                    WHERE company_id = %s AND date_closed >= current_date - interval '7 days'
                    GROUP BY date_closed 
                    ORDER BY date_closed ASC
                """, (company_id,))
                weekly_data = [{"date": str(row[0]), "sales": float(row[1])} for row in cur.fetchall()]
                
                # 4. Payment Methods Distribution (Today)
                cur.execute("""
                    SELECT pm.name, SUM(d.amount)
                    FROM tbl_cierre_payments_detail d
                    JOIN tbl_cierres_z_master m ON d.cierre_id = m.id
                    JOIN tbl_payment_methods pm ON d.payment_method_id = pm.id
                    WHERE m.company_id = %s AND m.date_closed = %s
                    GROUP BY pm.name
                """, (company_id, today))
                payment_distribution = [{"name": row[0], "value": float(row[1])} for row in cur.fetchall()]
                
                # 5. Recent Alerts (Unbalanced or AI Errors)
                cur.execute("""
                    SELECT id, z_number, branch_id, difference_amount, ai_comments, status
                    FROM tbl_cierres_z_master
                    WHERE company_id = %s AND (status != 'balanced' OR ai_comments IS NOT NULL)
                    ORDER BY id DESC LIMIT 5
                """, (company_id,))
                
                # Fetch branch names for alerts
                cur.execute("SELECT id, name FROM tbl_branches WHERE company_id = %s", (company_id,))
                branch_dict = {row[0]: row[1] for row in cur.fetchall()}
                
                alerts = []
                for row in cur.fetchall():
                    alerts.append({
                        "id": row[0],
                        "z_number": row[1],
                        "branch_name": branch_dict.get(row[2], "Desconocida"),
                        "difference_amount": float(row[3]) if row[3] else 0.0,
                        "ai_comments": row[4],
                        "status": row[5]
                    })
                
                return {
                    "kpis": {
                        "total_sales_today": total_sales_today,
                        "total_difference_today": total_difference_today,
                        "closed_branches": closed_branches,
                        "total_branches": total_branches
                    },
                    "weekly_trend": weekly_data,
                    "payment_distribution": payment_distribution,
                    "alerts": alerts
                }
        finally:
            db.release_connection(conn)
    except Exception as e:
        print("Dashboard Error:", e)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/companies")
def get_companies():
    try:
        companies = db.fetch_all("SELECT id, name, ruc, active FROM tbl_companies ORDER BY id DESC;")
        # Convertir tuplas a diccionarios
        result = [{"id": row[0], "name": row[1], "ruc": row[2], "active": row[3]} for row in companies]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CompanyCreate(BaseModel):
    name: str
    ruc: str

class CompanyUpdate(BaseModel):
    z_sequence_type: str | None = None
    z_current_sequence: int | None = None
    use_ai_validation: bool | None = None

class CompanyUserCreate(BaseModel):
    email: str
    role: str = 'user'
    branch_ids: list[int] = []

class BankAccountCreate(BaseModel):
    company_id: int
    name: str
    account_number: str | None = None
    accounting_code: str | None = None

class PaymentMethodCreate(BaseModel):
    company_id: int
    name: str
    bank_account_id: int

class UserCreate(BaseModel):
    email: str
    name: str
    is_global_admin: bool = False

class BranchCreate(BaseModel):
    company_id: int
    name: str

class CierrePayment(BaseModel):
    payment_method_id: int
    amount: float

class CierreCreate(BaseModel):
    company_id: int
    branch_id: int | None = None
    z_number: str | None = None
    date_closed: str
    taxable_sales: float
    exempt_sales: float
    tax_amount: float
    total_sales: float
    total_receipt: float
    difference_amount: float
    image_url: str | None = None
    pos_receipt_url: str | None = None
    deposit_receipt_url: str | None = None
    payments: list[CierrePayment]

@api_router.post("/companies")
def create_company(company: CompanyCreate):
    try:
        query = "INSERT INTO tbl_companies (name, ruc, z_sequence_type, z_current_sequence, use_ai_validation) VALUES (%s, %s, 'manual', 0, FALSE) RETURNING id;"
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (company.name, company.ruc))
                new_id = cur.fetchone()[0]
                conn.commit()
                return {"id": new_id, "name": company.name, "ruc": company.ruc, "active": True}
        finally:
            db.release_connection(conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/companies/{company_id}")
def update_company(company_id: int, company: CompanyUpdate):
    try:
        fields = []
        values = []
        if company.z_sequence_type is not None:
            fields.append("z_sequence_type = %s")
            values.append(company.z_sequence_type)
        if company.z_current_sequence is not None:
            fields.append("z_current_sequence = %s")
            values.append(company.z_current_sequence)
        if company.use_ai_validation is not None:
            fields.append("use_ai_validation = %s")
            values.append(company.use_ai_validation)
        
        if not fields:
            return {"status": "no updates"}

        values.append(company_id)
        query = f"UPDATE tbl_companies SET {', '.join(fields)} WHERE id = %s RETURNING id;"
        
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, tuple(values))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Company not found")
                conn.commit()
                return {"status": "success", "id": company_id}
        finally:
            db.release_connection(conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/companies/{company_id}/users")
def get_company_users(company_id: int):
    try:
        query = """
            SELECT u.id, u.email, u.name, u.active, cu.role, cu.created_at, u.google_id
            FROM tbl_users u
            JOIN tbl_company_users cu ON u.id = cu.user_id
            WHERE cu.company_id = %s
            ORDER BY u.name ASC;
        """
        users = db.fetch_all(query, (company_id,))
        return [
            {
                "id": row[0],
                "email": row[1],
                "name": row[2],
                "active": row[3],
                "role": row[4],
                "created_at": row[5],
                "confirmed": row[6] is not None
            }
            for row in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/companies/{company_id}/users")
def add_user_to_company(company_id: int, user: CompanyUserCreate):
    try:
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                # 1. Obtener nombre de la empresa para el correo
                cur.execute("SELECT name FROM tbl_companies WHERE id = %s;", (company_id,))
                comp_row = cur.fetchone()
                if not comp_row:
                    raise HTTPException(status_code=404, detail="Company not found")
                company_name = comp_row[0]

                # 2. Buscar si el usuario ya existe en tbl_users por email
                cur.execute("SELECT id FROM tbl_users WHERE email = %s;", (user.email,))
                user_row = cur.fetchone()
                if user_row:
                    user_id = user_row[0]
                else:
                    # Crear usuario provisional
                    cur.execute(
                        "INSERT INTO tbl_users (email, name, active) VALUES (%s, %s, true) RETURNING id;",
                        (user.email, user.email.split('@')[0])
                    )
                    user_id = cur.fetchone()[0]

                # 3. Vincular a la compañía
                query_link = """
                    INSERT INTO tbl_company_users (company_id, user_id, role) 
                    VALUES (%s, %s, %s) 
                    ON CONFLICT (company_id, user_id) DO NOTHING
                    RETURNING id;
                """
                cur.execute(query_link, (company_id, user_id, user.role))
                link_id = cur.fetchone()

                # 3.5 Vincular a sucursales
                for bid in user.branch_ids:
                    cur.execute(
                        "INSERT INTO tbl_user_branches (user_id, branch_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                        (user_id, bid)
                    )
                
                conn.commit()

                # 4. Enviar correo vía Resend
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                    <div style="background-color: #2563eb; padding: 20px; text-align: center;">
                        <h2 style="color: white; margin: 0;">Validador Cierre Z</h2>
                    </div>
                    <div style="padding: 30px; background-color: #f8fafc;">
                        <h3 style="color: #0f172a;">¡Hola! Tienes una nueva invitación</h3>
                        <p style="color: #475569; font-size: 16px; line-height: 1.5;">
                            Has sido invitado para unirte a <strong>{company_name}</strong> con el rol de <strong>{user.role}</strong>.
                        </p>
                        <p style="color: #475569; font-size: 16px; line-height: 1.5;">
                            Haz clic en el botón de abajo para iniciar sesión directamente con tu cuenta de Google:
                        </p>
                        <div style="text-align: center; margin-top: 30px; margin-bottom: 20px;">
                            <a href="https://cierrez.gfcontadorespa.com" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                                Iniciar sesión con Google
                            </a>
                        </div>
                        <p style="color: #94a3b8; font-size: 12px; text-align: center;">
                            Si no esperabas este correo, puedes ignorarlo de forma segura.
                        </p>
                    </div>
                </div>
                """
                
                try:
                    resend.Emails.send({
                        "from": "cierrez@gfcontadorespa.com",
                        "to": user.email,
                        "subject": f"Invitación a {company_name} - Validador Cierre Z",
                        "html": html_content
                    })
                except Exception as e:
                    print(f"Error enviando correo Resend: {e}")
                    # No fallamos la petición si solo falló el correo

                return {"status": "success", "user_id": user_id, "link_id": link_id[0] if link_id else None}
        finally:
            db.release_connection(conn)
    except Exception as e:
        print("Backend Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/companies/{company_id}/users/{user_id}")
def remove_user_from_company(company_id: int, user_id: int):
    try:
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                # 1. Eliminar la relación con la compañía
                cur.execute("DELETE FROM tbl_company_users WHERE company_id = %s AND user_id = %s", (company_id, user_id))
                
                # 2. Verificar si el usuario quedó huérfano (sin compañías) y si está "Pendiente" (google_id IS NULL)
                cur.execute("SELECT google_id FROM tbl_users WHERE id = %s", (user_id,))
                user_row = cur.fetchone()
                
                if user_row:
                    google_id = user_row[0]
                    cur.execute("SELECT COUNT(*) FROM tbl_company_users WHERE user_id = %s", (user_id,))
                    company_count = cur.fetchone()[0]
                    
                    if company_count == 0 and google_id is None:
                        # Limpiar usuario fantasma/pendiente
                        cur.execute("DELETE FROM tbl_users WHERE id = %s", (user_id,))
                
                conn.commit()
                return {"status": "success", "detail": "User removed successfully"}
        finally:
            db.release_connection(conn)
    except Exception as e:
        print("Backend Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/bank_accounts")
def get_bank_accounts(company_id: int | None = None):
    try:
        if company_id:
            query = "SELECT id, company_id, name, account_number, accounting_code, active FROM tbl_bank_accounts WHERE active = TRUE AND company_id = %s ORDER BY id DESC;"
            accounts = db.fetch_all(query, (company_id,))
        else:
            query = "SELECT id, company_id, name, account_number, accounting_code, active FROM tbl_bank_accounts WHERE active = TRUE ORDER BY id DESC;"
            accounts = db.fetch_all(query)
            
        result = [{"id": row[0], "company_id": row[1], "name": row[2], "account_number": row[3], "accounting_code": row[4], "active": row[5]} for row in accounts]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/bank_accounts")
def create_bank_account(account: BankAccountCreate):
    try:
        query = "INSERT INTO tbl_bank_accounts (company_id, name, account_number, accounting_code) VALUES (%s, %s, %s, %s) RETURNING id;"
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (account.company_id, account.name, account.account_number, account.accounting_code))
                new_id = cur.fetchone()[0]
                conn.commit()
                return {"id": new_id, **account.model_dump(), "active": True}
        finally:
            db.release_connection(conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/payment_methods")
def get_payment_methods(company_id: int | None = None):
    try:
        # Hacemos un JOIN con tbl_bank_accounts para devolver también el nombre del banco y su cuenta contable
        base_query = """
            SELECT pm.id, pm.company_id, pm.name, pm.bank_account_id, pm.active, 
                   ba.name as bank_name, ba.accounting_code 
            FROM tbl_payment_methods pm
            LEFT JOIN tbl_bank_accounts ba ON pm.bank_account_id = ba.id
            WHERE pm.active = TRUE
        """
        
        if company_id:
            query = base_query + " AND pm.company_id = %s ORDER BY pm.id DESC;"
            methods = db.fetch_all(query, (company_id,))
        else:
            query = base_query + " ORDER BY pm.id DESC;"
            methods = db.fetch_all(query)
            
        result = [{
            "id": row[0], "company_id": row[1], "name": row[2], 
            "bank_account_id": row[3], "active": row[4],
            "bank_name": row[5], "accounting_code": row[6]
        } for row in methods]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/payment_methods")
def create_payment_method(method: PaymentMethodCreate):
    try:
        query = "INSERT INTO tbl_payment_methods (company_id, name, bank_account_id) VALUES (%s, %s, %s) RETURNING id;"
        result = db.fetch_one(query, (method.company_id, method.name, method.bank_account_id))
        # Note: We should technically commit if fetch_one is used for INSERT, but since the previous ones worked, it might be auto-committing in some environments or failing silently. 
        # Actually, let's execute properly using a manual commit for this new POST to be safe.
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (method.company_id, method.name, method.bank_account_id))
                new_id = cur.fetchone()[0]
                conn.commit()
                return {"id": new_id, **method.model_dump(), "active": True}
        finally:
            db.release_connection(conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/users")
def get_users():
    try:
        query = "SELECT id, email, name, is_global_admin, active FROM tbl_users ORDER BY id DESC;"
        users = db.fetch_all(query)
        result = [{"id": row[0], "email": row[1], "name": row[2], "is_global_admin": row[3], "active": row[4]} for row in users]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/users")
def create_user(user: UserCreate):
    try:
        query = "INSERT INTO tbl_users (email, name, is_global_admin) VALUES (%s, %s, %s) RETURNING id;"
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (user.email, user.name, user.is_global_admin))
                new_id = cur.fetchone()[0]
                conn.commit()
                return {"id": new_id, "email": user.email, "name": user.name, "is_global_admin": user.is_global_admin, "active": True}
        finally:
            db.release_connection(conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/cierres")
def get_cierres(company_id: int | None = None):
    try:
        base_query = """
            SELECT id, company_id, branch_id, z_number, date_closed, 
                   taxable_sales, exempt_sales, tax_amount, total_sales, total_receipt, status, difference_amount, image_url, pos_receipt_url, deposit_receipt_url
            FROM tbl_cierres_z_master
        """
        if company_id:
            query = base_query + " WHERE company_id = %s ORDER BY date_closed DESC, id DESC;"
            cierres = db.fetch_all(query, (company_id,))
        else:
            query = base_query + " ORDER BY date_closed DESC, id DESC;"
            cierres = db.fetch_all(query)
            
        result = [{
            "id": row[0], "company_id": row[1], "branch_id": row[2], "z_number": row[3],
            "date_closed": str(row[4]), "taxable_sales": float(row[5]), "exempt_sales": float(row[6]),
            "tax_amount": float(row[7]), "total_sales": float(row[8]), "total_receipt": float(row[9]),
            "status": row[10], "difference_amount": float(row[11]) if row[11] is not None else 0.0,
            "image_url": row[12], "pos_receipt_url": row[13], "deposit_receipt_url": row[14]
        } for row in cierres]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/cierres")
def create_cierre(cierre: CierreCreate):
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            # Lógica de Secuencia de Compañía
            cur.execute("SELECT z_sequence_type, z_current_sequence FROM tbl_companies WHERE id = %s", (cierre.company_id,))
            comp = cur.fetchone()
            if not comp:
                raise HTTPException(status_code=404, detail="Company not found")
            
            if comp[0] == 'auto':
                next_seq = (comp[1] or 0) + 1
                cierre.z_number = f"Z-{next_seq}"
                cur.execute("UPDATE tbl_companies SET z_current_sequence = %s WHERE id = %s", (next_seq, cierre.company_id))
            elif not cierre.z_number:
                raise HTTPException(status_code=400, detail="z_number is required when sequence type is manual")

            # Determinar el estado
            status = 'unbalanced' if abs(cierre.difference_amount) >= 0.01 else 'balanced'

            # 1. Insertar el Master
            query_master = """
                INSERT INTO tbl_cierres_z_master 
                (company_id, branch_id, z_number, date_closed, taxable_sales, exempt_sales, tax_amount, total_sales, total_receipt, difference_amount, status, image_url, pos_receipt_url, deposit_receipt_url) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
            """
            cur.execute(query_master, (
                cierre.company_id, cierre.branch_id, cierre.z_number, cierre.date_closed,
                cierre.taxable_sales, cierre.exempt_sales, cierre.tax_amount, 
                cierre.total_sales, cierre.total_receipt, cierre.difference_amount, status, 
                cierre.image_url, cierre.pos_receipt_url, cierre.deposit_receipt_url
            ))
            cierre_id = cur.fetchone()[0]
            
            # 2. Insertar los Detalles (Pagos)
            if cierre.payments:
                query_detail = """
                    INSERT INTO tbl_cierre_payments_detail 
                    (cierre_id, payment_method_id, amount) 
                    VALUES (%s, %s, %s);
                """
                for payment in cierre.payments:
                    cur.execute(query_detail, (cierre_id, payment.payment_method_id, payment.amount))
                    
            conn.commit()
            return {"message": "Cierre registrado con éxito", "cierre_id": cierre_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.release_connection(conn)

@api_router.get("/cierres/{cierre_id}")
def get_cierre_details(cierre_id: int):
    try:
        query_master = """
            SELECT id, company_id, branch_id, z_number, date_closed, 
                   taxable_sales, exempt_sales, tax_amount, total_sales, total_receipt, status, difference_amount, image_url, pos_receipt_url, deposit_receipt_url
            FROM tbl_cierres_z_master WHERE id = %s
        """
        master_row = db.fetch_one(query_master, (cierre_id,))
        if not master_row:
            raise HTTPException(status_code=404, detail="Cierre no encontrado")
            
        master_data = {
            "id": master_row[0], "company_id": master_row[1], "branch_id": master_row[2], "z_number": master_row[3],
            "date_closed": str(master_row[4]), "taxable_sales": float(master_row[5]), "exempt_sales": float(master_row[6]),
            "tax_amount": float(master_row[7]), "total_sales": float(master_row[8]), "total_receipt": float(master_row[9]),
            "status": master_row[10], "difference_amount": float(master_row[11]) if master_row[11] is not None else 0.0,
            "image_url": master_row[12], "pos_receipt_url": master_row[13], "deposit_receipt_url": master_row[14]
        }
        
        query_details = """
            SELECT d.id, d.payment_method_id, pm.name as payment_method_name, d.amount
            FROM tbl_cierre_payments_detail d
            JOIN tbl_payment_methods pm ON d.payment_method_id = pm.id
            WHERE d.cierre_id = %s
        """
        details_rows = db.fetch_all(query_details, (cierre_id,))
        payments = [{
            "id": r[0], "payment_method_id": r[1], "payment_method_name": r[2], "amount": float(r[3])
        } for r in details_rows]
        
        master_data["payments"] = payments
        return master_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/branches")
def get_branches(company_id: int | None = None):
    try:
        if company_id:
            query = "SELECT id, company_id, name, active FROM tbl_branches WHERE company_id = %s ORDER BY name ASC;"
            branches = db.fetch_all(query, (company_id,))
        else:
            query = "SELECT id, company_id, name, active FROM tbl_branches ORDER BY name ASC;"
            branches = db.fetch_all(query)
            
        result = [{"id": row[0], "company_id": row[1], "name": row[2], "active": row[3]} for row in branches]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/branches")
def create_branch(branch: BranchCreate):
    try:
        query = "INSERT INTO tbl_branches (company_id, name) VALUES (%s, %s) RETURNING id;"
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (branch.company_id, branch.name))
                new_id = cur.fetchone()[0]
                conn.commit()
                return {"id": new_id, "company_id": branch.company_id, "name": branch.name, "active": True}
        finally:
            db.release_connection(conn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

load_dotenv()

@api_router.post("/upload/receipt")
async def upload_receipt(file: UploadFile = File(...)):
    endpoint_url = os.environ.get("R2_ENDPOINT_URL")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    bucket_name = os.environ.get("R2_BUCKET_NAME")
    public_url = os.environ.get("R2_PUBLIC_URL")

    if not all([endpoint_url, access_key, secret_key, bucket_name, public_url]):
        raise HTTPException(status_code=500, detail="Cloudflare R2 env vars missing")

    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        file_extension = file.filename.split(".")[-1]
        unique_filename = f"receipts/{uuid.uuid4()}.{file_extension}"

        s3.upload_fileobj(
            file.file, 
            bucket_name, 
            unique_filename,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        final_url = f"{public_url.rstrip('/')}/{unique_filename}"
        return {"url": final_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/jobs/daily-report")
def run_daily_report(target_date: str | None = None):
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Obtener empresas con admins
            cur.execute("""
                SELECT c.id, c.name, array_agg(u.email) as admin_emails
                FROM tbl_companies c
                JOIN tbl_company_users cu ON c.id = cu.company_id
                JOIN tbl_users u ON cu.user_id = u.id
                WHERE cu.role = 'admin' AND c.active = TRUE
                GROUP BY c.id, c.name
            """)
            companies = cur.fetchall()

            for comp in companies:
                comp_id, comp_name, admin_emails = comp[0], comp[1], comp[2]
                if not admin_emails: continue

                # 2. Sucursales
                cur.execute("SELECT id, name FROM tbl_branches WHERE company_id = %s", (comp_id,))
                all_branches = {row[0]: row[1] for row in cur.fetchall()}

                # 3. Cierres de hoy
                cur.execute("""
                    SELECT branch_id, z_number, taxable_sales, exempt_sales, tax_amount, 
                           total_sales, total_receipt, difference_amount, status 
                    FROM tbl_cierres_z_master 
                    WHERE company_id = %s AND date_closed = %s
                """, (comp_id, target_date))
                cierres_rows = cur.fetchall()

                closed_branch_ids = set()
                data_for_excel = []
                total_sales_day = 0.0
                total_receipt_day = 0.0
                descuadres = []

                for row in cierres_rows:
                    b_id = row[0]
                    closed_branch_ids.add(b_id)
                    b_name = all_branches.get(b_id, "Desconocida")
                    diff = float(row[7])
                    
                    if abs(diff) >= 0.01:
                        descuadres.append({"sucursal": b_name, "diferencia": diff})

                    total_sales_day += float(row[5])
                    total_receipt_day += float(row[6])

                    data_for_excel.append({
                        "Sucursal": b_name, "Número Z": row[1],
                        "Ventas Gravables": float(row[2]), "Ventas Exentas": float(row[3]), "Impuestos": float(row[4]),
                        "Total Ventas": float(row[5]), "Total Cobrado": float(row[6]), "Diferencia": diff, "Estado": row[8]
                    })

                # 4. Pendientes
                pending_branches = [name for b_id, name in all_branches.items() if b_id not in closed_branch_ids]
                if not data_for_excel and not pending_branches: continue

                # 5. Excel en BytesIO
                df = pd.DataFrame(data_for_excel) if data_for_excel else pd.DataFrame(columns=["Sucursal", "Número Z", "Ventas Gravables", "Ventas Exentas", "Impuestos", "Total Ventas", "Total Cobrado", "Diferencia", "Estado"])
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Cierres Z')
                excel_b64 = base64.b64encode(output.getvalue()).decode('utf-8')

                # 6. HTML del correo
                html_pendientes = "".join([f"<li>{p}</li>" for p in pending_branches])
                html_descuadres = "".join([f"<li>{d['sucursal']}: ${d['diferencia']:.2f}</li>" for d in descuadres])
                
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px;">
                    <div style="background-color: #0f172a; padding: 20px; text-align: center;">
                        <h2 style="color: white; margin: 0;">Reporte de Cierres Diarios</h2>
                        <p style="color: #cbd5e1; margin: 5px 0 0 0;">{comp_name} - {target_date}</p>
                    </div>
                    <div style="padding: 30px;">
                        <h3 style="color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">Resumen Gerencial</h3>
                        <div style="background-color: #f8fafc; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                            <p style="margin: 5px 0;"><strong>Ventas Totales Registradas:</strong> ${total_sales_day:,.2f}</p>
                            <p style="margin: 5px 0;"><strong>Efectivo/Pagos Cobrados:</strong> ${total_receipt_day:,.2f}</p>
                        </div>
                """
                if pending_branches:
                    html_content += f"""
                        <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin-bottom: 20px;">
                            <h4 style="color: #b91c1c; margin: 0 0 10px 0;">⚠️ Sucursales Pendientes de Cierre</h4>
                            <ul style="color: #7f1d1d; margin: 0; padding-left: 20px;">{html_pendientes}</ul>
                        </div>
                    """
                if descuadres:
                    html_content += f"""
                        <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 20px;">
                            <h4 style="color: #b45309; margin: 0 0 10px 0;">💰 Descuadres Detectados</h4>
                            <ul style="color: #92400e; margin: 0; padding-left: 20px;">{html_descuadres}</ul>
                        </div>
                    """
                
                html_content += """
                        <p style="color: #475569; font-size: 14px; margin-top: 30px;">
                            Adjunto a este correo encontrarás el reporte detallado en formato Excel con todas las transacciones del día.
                        </p>
                    </div>
                </div>
                """

                # 7. Enviar
                try:
                    resend.Emails.send({
                        "from": "cierrez@gfcontadorespa.com",
                        "to": admin_emails,
                        "subject": f"[{comp_name}] Reporte Consolidado de Ventas - {target_date}",
                        "html": html_content,
                        "attachments": [
                            {"filename": f"Cierres_{comp_name.replace(' ', '_')}_{target_date}.xlsx", "content": excel_b64}
                        ]
                    })
                except Exception as e:
                    print(f"Error enviando reporte a {comp_name}: {e}")

        return {"status": "success", "message": "Reportes enviados"}
    except Exception as e:
        print("Error en daily report:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.release_connection(conn)


app.include_router(api_router)

# Import StaticFiles and FileResponse here if not already imported
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount the static files for the React app
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'dist')
if os.path.exists(frontend_dist):
    app.mount('/assets', StaticFiles(directory=os.path.join(frontend_dist, 'assets')), name='assets')
    
    # Optional: Serve other static files like vite.svg, favicon.svg if they exist
    for file in os.listdir(frontend_dist):
        if file.endswith('.svg') or file.endswith('.png') or file.endswith('.ico'):
            @app.get(f'/{file}')
            def get_static_file(file=file):
                return FileResponse(os.path.join(frontend_dist, file))
    
    # Catch-all route to serve index.html for React Router SPA
    @app.get('/{catchall:path}')
    def serve_react_app(catchall: str):
        return FileResponse(os.path.join(frontend_dist, 'index.html'))
else:
    print('WARNING: frontend/dist directory not found. React app will not be served.')
