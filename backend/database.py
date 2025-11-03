
from motor.motor_asyncio import AsyncIOMotorClient
import os

# --- Configuración de Conexión ---

# Lo siguiente lee la cadena de conexión de MongoDB de una variable de entorno
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = "parrilladas_familiares_db" 

class Database:
    client: AsyncIOMotorClient = None

# Variable global para la base de datos
db = None

async def connect_to_mongo():
    """ Se ejecuta al iniciar la aplicación FastAPI para conectar a MongoDB """
    global db
    print("Conectando a MongoDB...")
    Database.client = AsyncIOMotorClient(MONGO_URI)
    db = Database.client[DATABASE_NAME]
    print("¡Conexión a MongoDB establecida!")

async def close_mongo_connection():
    """ Se ejecuta al apagar la aplicación FastAPI para cerrar la conexión """
    print("Cerrando conexión con MongoDB...")
    Database.client.close()
    print("Conexión cerrada.")

# --- Funciones de Acceso a Colecciones ---

def get_user_collection():
    """ Obtiene la colección 'users' """
    if db is None:
        raise Exception("La base de datos no está conectada. Asegúrate de llamar a connect_to_mongo().")
    return db["users"]

def get_product_collection():
    """ Obtiene la colección 'products' """
    if db is None:
        raise Exception("La base de datos no está conectada.")
    return db["products"]

def get_order_collection():
    """ Obtiene la colección 'orders' """
    if db is None:
        raise Exception("La base de datos no está conectada.")
    return db["orders"]