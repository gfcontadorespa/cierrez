import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-default-key-please-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token ha expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def verify_company_access(user: dict, company_id: int, require_admin: bool = False):
    """
    Verifies that the authenticated user has access to the requested company_id.
    If require_admin is True, also verifies that the user is an admin of the company.
    """
    if user.get("is_global_admin"):
        return True
    
    if user.get("company_id") == company_id:
        if require_admin and user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Esta acción requiere privilegios de administrador de compañía")
        return True
        
    raise HTTPException(status_code=403, detail="No tienes permisos para acceder a esta compañía")
