"""
=============================================================
CART PYDANTIC MODELS
=============================================================
Models for shopping cart operations.

CART FLOW:
1. User adds items → POST /order/add
2. User removes items → POST /order/remove
3. User views cart → GET /cart
4. User checks out → POST /checkout

Each cart belongs to ONE user and ONE restaurant at a time.
=============================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# -------------------------------------------------------
# SUB-MODEL: A single item inside the cart
# -------------------------------------------------------
class CartItem(BaseModel):
    """Represents one item in the cart with quantity."""
    item_id: str = Field(..., description="Menu item ID")
    item_name: str = Field(..., description="Name of the item")
    price: float = Field(..., gt=0, description="Price per unit")
    quantity: int = Field(default=1, ge=1, description="Number of units")


# -------------------------------------------------------
# REQUEST MODEL: Add item to cart
# -------------------------------------------------------
class AddToCartRequest(BaseModel):
    """Data required to add an item to the cart."""
    user_id: str = Field(..., description="ID of the user")
    restaurant_id: str = Field(..., description="ID of the restaurant")
    item_id: str = Field(..., description="ID of the menu item to add")
    item_name: str = Field(..., description="Name of the menu item")
    price: float = Field(..., gt=0, description="Price of the item")
    quantity: int = Field(default=1, ge=1, description="Quantity to add")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "USR001",
                    "restaurant_id": "REST001",
                    "item_id": "ITEM001",
                    "item_name": "Margherita Pizza",
                    "price": 299.0,
                    "quantity": 2
                }
            ]
        }
    }


# -------------------------------------------------------
# REQUEST MODEL: Remove item from cart
# -------------------------------------------------------
class RemoveFromCartRequest(BaseModel):
    """Data required to remove an item from the cart."""
    user_id: str = Field(..., description="ID of the user")
    item_id: str = Field(..., description="ID of the menu item to remove")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "USR001",
                    "item_id": "ITEM001"
                }
            ]
        }
    }


# -------------------------------------------------------
# RESPONSE MODEL: Full cart data
# -------------------------------------------------------
class CartResponse(BaseModel):
    """Complete cart data returned to the client."""
    cart_id: str
    user_id: str
    restaurant_id: str
    items: List[CartItem] = []
    cart_total: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
