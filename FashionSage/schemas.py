from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# ---------------- User Schemas ----------------
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


# ---------------- Auth Schemas ----------------
class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: str
    password: str


# ---------------- Product Schemas ----------------
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
    tags: Optional[List[str]] = None   # 👈 FIX: list instead of dict/str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------- Chat Schemas ----------------
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    session_id: str
    products: Optional[List[ProductResponse]] = None
    orders: Optional[List[Dict[str, Any]]] = None


# ---------------- Order Schemas ----------------
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
