# backend/models.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Any 
from bson import ObjectId 
from pydantic_core import core_schema 

# --- Clases Auxiliares ---

class PyObjectId(ObjectId):
    """ Clase personalizada para validar el ObjectId de MongoDB (Compatible con Pydantic v2) """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        """
        Define el validador principal (reemplaza a __get_validators__).
        Valida que el valor sea un ObjectId válido.
        """
        def validate_object_id(v: Any) -> ObjectId:
            """Función de validación"""
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return ObjectId(v)

        # Usamos un validador "plain" que llama a nuestra función
        return core_schema.with_info_plain_validator_function(
            validate_object_id,
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: Any
    ) -> dict:
        """
        Define cómo se debe representar este tipo en el JSON Schema (Swagger/docs).
        (Reemplaza a __modify_schema__)
        Lo representamos como un 'string'.
        """
        return {"type": "string"}

# --- Modelos de Usuario (Épica E01) ---

class UserCreate(BaseModel):
    """ Modelo para el registro de un nuevo usuario """
    email: EmailStr
    password: str = Field(..., min_length=8, description="Debe tener min 8 caracteres, 1 mayúscula, 1 número y 1 símbolo especial")
    confirm: str # Solo para validación, no se guarda en DB
    terminos: bool

class UserLogin(BaseModel):
    """ Modelo para el inicio de sesión """
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    """ Modelo de cómo el usuario se guarda en la Base de Datos """
    id: Optional[PyObjectId] = Field(alias="_id")
    email: EmailStr
    hashed_password: str # NUNCA guardamos la contraseña en texto plano
    terminos: bool
    is_active: bool = Field(default=True)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# --- Modelos de Producto (Épica E02) ---

class Especificacion(BaseModel):
    """ Especificaciones del producto """
    nombre: str
    valor: str

class Producto(BaseModel):
    """ Modelo completo del producto en la Base de Datos """
    id: Optional[PyObjectId] = Field(alias="_id")
    nombre: str
    descripcion: str
    precio: float # Usamos float o int para precios
    categoria: str
    imagen: str # URL de la imagen
    especificaciones: Optional[List[Especificacion]] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# --- Modelos de Carrito y Pedido (Épica E03) ---

class ProductoEnCarrito(BaseModel):
    """ Un item dentro del carrito """
    producto_id: str # Referencia al ID del Producto
    cantidad: int
    # El nombre y precio se pueden obtener de la DB al momento de mostrar

class Pedido(BaseModel):
    """ Modelo para el pedido final """
    id: Optional[PyObjectId] = Field(alias="_id")
    # user_id: str # Para vincular al usuario que hizo el pedido
    
    # Lista de productos comprados
    items: List[ProductoEnCarrito]
    
    # Resumen del carrito
    subtotal: float
    envio: float
    descuento: float
    total: float
    
    # Datos de Entrega
    metodo_entrega: str # 'retiro' o 'delivery'
    
    # Opcional si es 'retiro'
    sucursal: Optional[str] = None
    hora_retiro: Optional[str] = None
    
    # Opcional si es 'delivery'
    direccion: Optional[str] = None
    comuna: Optional[str] = None
    telefono: Optional[str] = None
    horario_preferido: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}