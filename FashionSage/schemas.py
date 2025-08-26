from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ProductResponse(BaseModel):
    id: int | None = None
    name: str | None = None
    price: float | None = None
    category: str | None = None
    stock_quantity: int | None = None
    created_at: datetime | None = None


# Product schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str
    color: Optional[str] = None
    size: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    stock_quantity: int
    tags: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Chat schemas
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    session_id: str
    products: Optional[List[ProductResponse]] = None
    orders: Optional[List[Dict[str, Any]]] = None

# Order schemas
class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product: ProductResponse
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    order_number: str
    status: str
    total_amount: float
    created_at: datetime
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: Optional[int]
    name: Optional[str]
    price: Optional[float]
    category: Optional[str]
    stock_quantity: Optional[int]
    created_at: Optional[datetime]