# backend/models.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Any
from bson import ObjectId
from pydantic_core import core_schema

#CLASE ESPECIAL PARA EL ID 
class PyObjectId(str):
    """
    Clase personalizada para que Pydantic v2 pueda manejar
    los ObjectIds de MongoDB convertiéndolos a string.
    """
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.str_schema(),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

#Modelos de Usuario 

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    confirm: str
    terminos: bool

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(BaseModel):

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: EmailStr
    hashed_password: str
    terminos: bool
    is_active: bool = Field(default=True)
    role: str = Field(default="cliente") 

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

#Modelos de Producto 

class Especificacion(BaseModel):
    nombre: str
    valor: str

class Producto(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    nombre: str
    descripcion: str
    precio: float
    categoria: str
    imagen: str
    especificaciones: Optional[List[Especificacion]] = []
    
    es_oferta: bool = False
    precio_normal: Optional[float] = None 

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

#Modelos de Pedido

class ProductoEnCarrito(BaseModel):
    producto_id: str
    cantidad: int
    nombre: Optional[str] = "Producto" 
    precio: Optional[float] = 0        

class Pedido(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    items: List[ProductoEnCarrito]
    subtotal: float
    envio: float
    descuento: float
    total: float
    metodo_entrega: str
    

    metodo_pago: str 
    user_email: Optional[str] = None
    
    sucursal: Optional[str] = None
    direccion: Optional[str] = None
    estado: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
class Reserva(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    cliente_nombre: str 
    telefono: str
    fecha_hora: str
    asistentes: int
    sucursal: str
    menu: Optional[str] = None
    estado: str = "Pendiente" 

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class UserUpdate(BaseModel):
    email: EmailStr
    nombre: Optional[str] = None
    telefono: Optional[str] = None

class PasswordChange(BaseModel):
    email: EmailStr
    current_password: str
    new_password: str