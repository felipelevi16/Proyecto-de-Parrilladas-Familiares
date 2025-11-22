# backend/security.py
import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara una contraseña en texto plano con el hash guardado.
    """
    # bcrypt necesita trabajar con bytes, no con texto normal (strings)
    # Por eso usamos .encode('utf-8')
    password_byte = plain_password.encode('utf-8')
    
    # Nos aseguramos de que el hash también esté en bytes
    if isinstance(hashed_password, str):
        hashed_byte = hashed_password.encode('utf-8')
    else:
        hashed_byte = hashed_password

    return bcrypt.checkpw(password_byte, hashed_byte)

def get_password_hash(password: str) -> str:
    """
    Genera un hash seguro para la contraseña.
    """
    password_byte = password.encode('utf-8')
    # Generamos un "salt" (aleatoriedad) y creamos el hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_byte, salt)
    
    # Devolvemos el resultado convertido a texto (string) para guardarlo en MongoDB
    return hashed.decode('utf-8')