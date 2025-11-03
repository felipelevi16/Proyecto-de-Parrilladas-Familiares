# backend/security.py
from passlib.context import CryptContext

# 1. Configurar el contexto de hashing
# Le decimos a passlib que use 'bcrypt' como algoritmo por defecto
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara una contraseña en texto plano (del login) 
    con una contraseña hasheada (de la DB).
   
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Toma una contraseña en texto plano (del registro) 
    y devuelve su hash.
   
    """
    return pwd_context.hash(password)