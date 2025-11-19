"""
Database Schemas for Food Delivery App

Each Pydantic model represents a MongoDB collection. Collection name is the lowercase of the class name.
- Restaurant -> "restaurant"
- MenuItem -> "menuitem"
- Order -> "order"
- Customer -> "customer"

These schemas are used for validation and for the database viewer.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class Restaurant(BaseModel):
    name: str = Field(..., description="Restaurant name")
    description: Optional[str] = Field(None, description="Short description")
    cuisine: Optional[str] = Field(None, description="Cuisine type, e.g., Italian, Indian")
    image_url: Optional[str] = Field(None, description="Cover image URL")
    rating: Optional[float] = Field(4.5, ge=0, le=5, description="Average rating")
    delivery_fee: Optional[float] = Field(2.99, ge=0, description="Delivery fee")
    eta_minutes: Optional[int] = Field(30, ge=1, description="Estimated delivery time in minutes")


class MenuItem(BaseModel):
    restaurant_id: str = Field(..., description="Restaurant ObjectId as string")
    name: str = Field(..., description="Menu item name")
    description: Optional[str] = Field(None, description="Item description")
    price: float = Field(..., ge=0, description="Price in dollars")
    image_url: Optional[str] = Field(None, description="Item image URL")
    is_veg: Optional[bool] = Field(False, description="Is vegetarian")
    spicy_level: Optional[int] = Field(0, ge=0, le=3, description="Spicy level 0-3")


class Customer(BaseModel):
    name: str
    email: EmailStr
    address: str
    phone: Optional[str] = None


class OrderItem(BaseModel):
    menu_item_id: str
    quantity: int = Field(..., ge=1)


class Order(BaseModel):
    restaurant_id: str
    customer_id: Optional[str] = Field(None, description="Optional: link to customer")
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    items: List[OrderItem]
    subtotal: float = 0
    delivery_fee: float = 0
    total: float = 0
    status: str = Field("pending", description="pending, confirmed, preparing, out_for_delivery, delivered, cancelled")
