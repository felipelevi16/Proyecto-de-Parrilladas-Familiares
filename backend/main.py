# backend/main.py
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from bson import ObjectId

# Importamos los componentes locales
from . import models
from . import security
from .database import (
    connect_to_mongo, 
    close_mongo_connection, 
    get_user_collection, 
    get_product_collection, 
    get_order_collection
)

# --- Configuración de la Aplicación ---

app = FastAPI(
    title="API de Parrilladas Familiares",
    description="Backend para gestionar usuarios, productos y pedidos.",
    version="1.0.0"
)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")
# --- CONFIGURACIÓN DE CORS (PERMISOS) ---
# Esto debe ir justo después de crear la 'app'
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:5500",  # Puerto común de Live Server
    "*"  # Comodín: permite conexiones desde cualquier lugar (útil para desarrollo)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Eventos de inicio y apagado
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# --- Rutas (Endpoints) ---

@app.get("/")
def read_root():
    return {"mensaje": "¡La API está funcionando correctamente!"}

@app.post("/register", response_model=models.UserInDB, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: models.UserCreate):
    # 1. Validaciones
    if user_in.password != user_in.confirm:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")
    if not user_in.terminos:
        raise HTTPException(status_code=400, detail="Debes aceptar los términos")

    user_collection = get_user_collection()
    
    # 2. Verificar duplicados
    existing_user = await user_collection.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    # 3. Guardar
    hashed_password = security.get_password_hash(user_in.password)
    user_db_data = user_in.dict(exclude={"confirm"})
    user_db_data["hashed_password"] = hashed_password
    del user_db_data["password"]
    
    new_user = await user_collection.insert_one(user_db_data)
    created_user = await user_collection.find_one({"_id": new_user.inserted_id})
    return created_user

@app.post("/login")
async def login_user(form_data: models.UserLogin):
    user_collection = get_user_collection()
    user_db = await user_collection.find_one({"email": form_data.email})
    
    if not user_db or not security.verify_password(form_data.password, user_db["hashed_password"]):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    
    return {"message": "¡Sesión iniciada correctamente!", "email": user_db["email"]}

@app.get("/products")
async def get_products():
    # 1. Conectamos a la colección de productos
    product_collection = get_product_collection()
    
    # 2. Buscamos todos los productos (limitado a 100 para no saturar)
    products_cursor = product_collection.find({})
    products = await products_cursor.to_list(length=100)
    
    # 3. Convertimos los _id a string para que no den error
    for product in products:
        if "_id" in product:
            product["_id"] = str(product["_id"])
            
    return products