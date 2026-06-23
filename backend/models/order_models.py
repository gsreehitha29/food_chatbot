"""
=============================================================
ORDER PYDANTIC MODELS
=============================================================
Models for checkout and order tracking.

ORDER FLOW:
1. Cart is finalized → POST /checkout
2. Order is created with status "confirmed"
3. Status progresses: confirmed → preparing → out_for_delivery → delivered

PRICING BREAKDOWN:
- total_amount: Sum of item prices
- delivery_fee: Flat or distance-based fee
- tax_amount: Tax on total_amount
- discount_amount: Any coupons or offers applied
- final_amount: total_amount + delivery_fee + tax_amount - discount_amount
=============================================================
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# -------------------------------------------------------
# SUB-MODEL: Item snapshot in an order
# -------------------------------------------------------
class OrderItem(BaseModel):
    """Snapshot of an item at the time of ordering."""
    item_id: str
    item_name: str
    price: float
    quantity: int


# -------------------------------------------------------
# REQUEST MODEL: Checkout / Place order
# -------------------------------------------------------
class CheckoutRequest(BaseModel):
    """Data required to convert a cart into an order."""
    user_id: str = Field(..., description="ID of the user placing the order")
    payment_method: str = Field(
        default="cod",
        description="Payment method: 'cod', 'upi', 'card', 'wallet'"
    )
    delivery_address: str = Field(
        ...,
        description="Full delivery address string"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "USR001",
                    "payment_method": "upi",
                    "delivery_address": "123 MG Road, Apt 4B, Bangalore 560001"
                }
            ]
        }
    }


# -------------------------------------------------------
# RESPONSE MODEL: Full order data
# -------------------------------------------------------
class OrderResponse(BaseModel):
    """Complete order data returned to the client."""
    order_id: str
    user_id: str
    restaurant_id: str
    items: List[OrderItem] = []
    total_amount: float = 0.0
    delivery_fee: float = 0.0
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    final_amount: float = 0.0
    payment_method: str = "cod"
    payment_status: str = "pending"
    order_status: str = "confirmed"
    delivery_address: str = ""
    ordered_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
