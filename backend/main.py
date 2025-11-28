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
    
    # Obtenemos el rol (si no tiene, asumimos que es cliente)
    user_role = user_db.get("role", "cliente")
    
    # Devolvemos el rol al frontend
    return {
        "message": "¡Sesión iniciada correctamente!", 
        "email": user_db["email"],
        "role": user_role  
    }

# --- Agrega o actualiza esto en backend/main.py ---

@app.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(pedido: models.Pedido):
    # 1. Conectamos a la colección
    order_collection = get_order_collection()
    
    # 2. Preparamos los datos
    pedido_dict = pedido.dict(by_alias=True, exclude={"id"})
    
    # 3. Asignamos estado inicial automático
    pedido_dict["estado"] = "Ingresado" 
    
    # 4. Insertamos en MongoDB
    new_order = await order_collection.insert_one(pedido_dict)
    
    # 5. Devolvemos el ID del pedido creado
    return {"id": str(new_order.inserted_id), "mensaje": "Pedido recibido exitosamente"}
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

@app.get("/products/{id}")
async def get_product_detail(id: str):
    # 1. Validamos si el ID tiene el formato correcto de MongoDB
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID de producto inválido")
    
    # 2. Buscamos el producto específico
    product = await get_product_collection().find_one({"_id": ObjectId(id)})
    
    # 3. Si no existe, error 404
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    # 4. Convertimos el ID a texto para enviarlo
    product["_id"] = str(product["_id"])
    return product
    # --- Agrega esto al final de backend/main.py ---

@app.get("/orders")
async def get_orders():
    # 1. Conectamos a la colección
    order_collection = get_order_collection()
    
    # 2. Traemos todos los pedidos (los más nuevos primero)
    # sort("_id", -1) ordena de forma descendente por fecha
    orders_cursor = order_collection.find({}).sort("_id", -1)
    orders = await orders_cursor.to_list(length=100)
    
    # 3. Limpieza de datos para enviar al frontend
    results = []
    for order in orders:
        order["id"] = str(order["_id"]) # Convertir ID a texto
        del order["_id"]
        results.append(order)
        
    return results

# 1. Crear Reserva (Para el Cliente)
@app.post("/reservations", status_code=status.HTTP_201_CREATED)
async def create_reservation(reserva: models.Reserva):
    # Puedes crear una colección nueva "reservations"
    db = get_order_collection().database # Truco para obtener la referencia a la DB
    reservations_collection = db["reservations"]
    
    reserva_dict = reserva.dict(by_alias=True, exclude={"id"})
    new_reserva = await reservations_collection.insert_one(reserva_dict)
    
    return {"id": str(new_reserva.inserted_id), "mensaje": "Reserva solicitada"}

# 2. Leer Reservas (Para el Dashboard)
@app.get("/reservations")
async def get_reservations():
    db = get_order_collection().database
    reservations_collection = db["reservations"]
    
    cursor = reservations_collection.find({}).sort("_id", -1)
    reservas = await cursor.to_list(length=100)
    
    for r in reservas:
        r["id"] = str(r["_id"])
        del r["_id"]
        
    return reservas

# backend/main.py

@app.get("/orders/{id}")
async def get_single_order(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
        
    order = await get_order_collection().find_one({"_id": ObjectId(id)})
    
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
    order["id"] = str(order["_id"])
    del order["_id"]
    return order

# --- Agrega esto al final de backend/main.py ---

# 1. Para E6F3 (Admin Catálogo): Crear nuevos productos
@app.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product(producto: models.Producto):
    product_collection = get_product_collection()
    
    # Preparamos el producto (excluyendo el ID para que Mongo lo genere)
    prod_dict = producto.dict(by_alias=True, exclude={"id"})
    
    new_prod = await product_collection.insert_one(prod_dict)
    
    return {"id": str(new_prod.inserted_id), "mensaje": "Producto creado exitosamente"}

# 2. Para E6F2 (Admin Reservas): Confirmar/Actualizar reserva
@app.put("/reservations/{id}")
async def update_reservation_status(id: str, estado: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
        
    db = get_order_collection().database
    reservations_collection = db["reservations"]
    
    # Actualizamos solo el campo 'estado'
    result = await reservations_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estado": estado}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
    return {"mensaje": f"Reserva actualizada a {estado}"}