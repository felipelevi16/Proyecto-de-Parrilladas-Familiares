
from fastapi import FastAPI, HTTPException, status
from typing import List, Optional
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware

# Importación de los componentes ya definidos
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

#

# Eventos de inicio y apagado
@app.on_event("startup")
async def startup_event():
    """ Conecta a la base de datos al iniciar la app. """
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    """ Desconecta de la base de datos al apagar la app. """
    await close_mongo_connection()

# --- Rutas de la API ---

# ÉPICA E01: AUTENTICACIÓN SEGURA


@app.post("/register", 
          response_model=models.UserInDB, 
          status_code=status.HTTP_201_CREATED,
          summary="Registrar un nuevo usuario")
async def register_user(user_in: models.UserCreate):
    """
    Registra un nuevo usuario en la base de datos.
    - Valida que las contraseñas coincidan.
    - Valida la aceptación de términos.
    - Verifica que el email no exista.
    - Hashea la contraseña antes de guardarla.
   
    """
    
    # 1. Validaciones del frontend
    if user_in.password != user_in.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Las contraseñas no coinciden"
        )
    
    if not user_in.terminos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Debes aceptar los términos y condiciones"
        )

    # 2. Verificar si el usuario ya existe
    user_collection = get_user_collection()
    existing_user = await user_collection.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El correo electrónico ya está registrado"
        )

    # 3. Hashear la contraseña
    hashed_password = security.get_password_hash(user_in.password)
    
    # 4. Crear el objeto para la DB (sin 'confirm')
    user_db_data = user_in.dict(exclude={"confirm"})
    user_db_data["hashed_password"] = hashed_password
    del user_db_data["password"] # Eliminar la contraseña en texto plano

    # 5. Insertar en la base de datos
    new_user = await user_collection.insert_one(user_db_data)
    
    # 6. Devolver el usuario creado
    created_user = await user_collection.find_one({"_id": new_user.inserted_id})
    return created_user

@app.post("/login", summary="Iniciar sesión")
async def login_user(form_data: models.UserLogin):
    """
    Autentica a un usuario y (en el futuro) devuelve un token.
   
    """
    user_collection = get_user_collection()
    
    # 1. Buscar al usuario por email
    user_db = await user_collection.find_one({"email": form_data.email})
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Correo no registrado"
        )

    # 2. Verificar la contraseña
    if not security.verify_password(form_data.password, user_db["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Contraseña incorrecta"
        )

    # (Aquí es donde generarías un token JWT en un proyecto real)
    
    return {"message": "¡Sesión iniciada correctamente!", "email": user_db["email"]}

# (Aquí iría la ruta para E1F3 - Recuperar Contraseña, que es más compleja)


# ÉPICA E02: CATÁLOGO DE PRODUCTOS

@app.get("/products", 
         response_model=List[models.Producto],
         summary="Obtener lista de productos")
async def get_products(
    categoria: Optional[str] = None, 
    search: Optional[str] = None
):
    """
    Obtiene todos los productos del catálogo.
    Permite filtrar por categoría y búsqueda por nombre/descripción.
   
    """
    product_collection = get_product_collection()
    query = {}
    
    if categoria:
        query["categoria"] = categoria
    
    if search:
        # Búsqueda simple (case-insensitive) en nombre y descripción
        query["$or"] = [
            {"nombre": {"$regex": search, "$options": "i"}},
            {"descripcion": {"$regex": search, "$options": "i"}}
        ]

    products_cursor = product_collection.find(query)
    products = await products_cursor.to_list(length=100)
    return products

@app.get("/products/{id}", 
         response_model=models.Producto,
         summary="Obtener detalle de un producto")
async def get_product_detail(id: str):
    """
    Obtiene la información detallada de un solo producto por su ID.
   
    """
    product_collection = get_product_collection()
    
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID de producto inválido")
        
    product = await product_collection.find_one({"_id": ObjectId(id)})
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Producto no encontrado"
        )
    return product

# (Las rutas de 'admin' para CREAR, ACTUALIZAR, BORRAR productos irían aquí)
#

# ÉPICA E03: CARRITO Y PEDIDOS ONLINE


@app.post("/orders", 
          response_model=models.Pedido,
          status_code=status.HTTP_201_CREATED,
          summary="Crear un nuevo pedido")
async def create_order(pedido_in: models.Pedido):
    """
    Recibe el pedido final (carrito + datos de entrega) y lo guarda.
    Esto se llamaría al final del proceso de pago.
   
    """
    # (Aquí faltaría lógica de validación de precios, stock, y vincular al usuario)
    
    order_collection = get_order_collection()
    
    # Añadimos un estado inicial basado en E7F2
    pedido_data = pedido_in.dict()
    pedido_data["estado"] = "Confirmado" # Estado inicial
    
    new_order = await order_collection.insert_one(pedido_data)
    
    created_order = await order_collection.find_one({"_id": new_order.inserted_id})
    return created_order

# (Aquí iría la ruta para E7F2 - Seguimiento de Pedido)
# GET /orders/{id}/status