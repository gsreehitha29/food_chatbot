"""
=============================================================
ORDER & CART ROUTES
=============================================================
API endpoints for cart management and checkout.

ENDPOINTS:
  POST /order/add      → Add an item to the cart
  POST /order/remove   → Remove an item from the cart
  GET  /cart            → View the current cart
  POST /checkout       → Convert cart to order (checkout)

IMPORTANT: The cart is a temporary holding area. When the user
checks out, the cart items become a permanent order.
=============================================================
"""

from fastapi import APIRouter, HTTPException, Query
from models.cart_models import AddToCartRequest, RemoveFromCartRequest
from models.order_models import CheckoutRequest
from services.cart_service import add_to_cart, remove_from_cart, get_cart
# FIX #18: Import get_user_orders to expose order history endpoint
from services.order_service import create_order, get_user_orders

# Create a router — note: no common prefix since /order and /cart are different
router = APIRouter(tags=["Order & Cart"])


@router.post(
    "/order/add",
    summary="Add item to cart",
    description="Adds a menu item to the user's shopping cart."
)
def add_item_to_cart(request: AddToCartRequest):
    """
    POST /order/add
    
    Adds an item to the user's cart. If the user already has items
    from a different restaurant, the old cart is cleared first.
    
    Sample Request:
    {
        "user_id": "USR001",
        "restaurant_id": "REST001",
        "item_id": "ITEM001",
        "item_name": "Margherita Pizza",
        "price": 299.0,
        "quantity": 2
    }
    
    Sample Response:
    {
        "status": "success",
        "message": "Item added to cart",
        "cart": {
            "cart_id": "CART-A1B2C3D4",
            "user_id": "USR001",
            "items": [...],
            "cart_total": 598.0
        }
    }
    """
    cart = add_to_cart(
        user_id=request.user_id,
        restaurant_id=request.restaurant_id,
        item_id=request.item_id,
        item_name=request.item_name,
        price=request.price,
        quantity=request.quantity
    )

    return {
        "status": "success",
        "message": "Item added to cart",
        "cart": cart
    }


@router.post(
    "/order/remove",
    summary="Remove item from cart",
    description="Removes a specific item from the user's cart."
)
def remove_item_from_cart(request: RemoveFromCartRequest):
    """
    POST /order/remove
    
    Removes an item from the cart. If the cart becomes empty,
    it is deleted automatically.
    
    Sample Request:
    {
        "user_id": "USR001",
        "item_id": "ITEM001"
    }
    """
    result = remove_from_cart(
        user_id=request.user_id,
        item_id=request.item_id
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Cart not found or item not in cart"
        )

    return {
        "status": "success",
        "message": "Item removed from cart",
        "cart": result
    }


@router.get(
    "/cart",
    summary="View cart",
    description="Returns the current cart for a user."
)
def view_cart(
    user_id: str = Query(
        ...,
        description="User ID to fetch cart for"
    )
):
    """
    GET /cart?user_id=USR001
    
    Returns the full cart contents including items and total.
    Returns 404 if no active cart exists.
    
    Sample Response:
    {
        "status": "success",
        "cart": {
            "cart_id": "CART-A1B2C3D4",
            "user_id": "USR001",
            "restaurant_id": "REST001",
            "items": [
                {
                    "item_id": "ITEM001",
                    "item_name": "Margherita Pizza",
                    "price": 299.0,
                    "quantity": 2
                }
            ],
            "cart_total": 598.0
        }
    }
    """
    cart = get_cart(user_id)

    if not cart:
        raise HTTPException(
            status_code=404,
            detail=f"No active cart found for user '{user_id}'"
        )

    return {
        "status": "success",
        "cart": cart
    }


@router.post(
    "/checkout",
    summary="Checkout / Place order",
    description="Converts the user's cart into a confirmed order and clears the cart."
)
def checkout(request: CheckoutRequest):
    """
    POST /checkout
    
    Processes the checkout:
    1. Takes the user's cart
    2. Calculates total + delivery fee + tax
    3. Creates an order with status "confirmed"
    4. Clears the cart
    
    Sample Request:
    {
        "user_id": "USR001",
        "payment_method": "upi",
        "delivery_address": "123 MG Road, Bangalore 560001"
    }
    
    Sample Response:
    {
        "status": "success",
        "message": "Order placed successfully!",
        "order": {
            "order_id": "ORD-X1Y2Z3W4",
            "total_amount": 598.0,
            "delivery_fee": 40.0,
            "tax_amount": 29.9,
            "final_amount": 667.9,
            "order_status": "confirmed"
        }
    }
    """
    order = create_order(
        user_id=request.user_id,
        payment_method=request.payment_method,
        delivery_address=request.delivery_address
    )

    if not order:
        raise HTTPException(
            status_code=400,
            detail="Cannot checkout: Cart is empty or not found"
        )

    return {
        "status": "success",
        "message": "Order placed successfully!",
        "order": order
    }


@router.get(
    "/orders",
    summary="Get order history",
    description="Returns all past orders for a user, sorted by most recent first."
)
def get_orders(
    user_id: str = Query(
        ...,
        description="User ID to fetch order history for"
    )
):
    """
    GET /orders?user_id=USR001

    FIX #18: Previously there was no way to retrieve past orders via the API.
    The orders collection had indexes for user_id but no GET endpoint.

    Sample Response:
    {
        "status": "success",
        "user_id": "USR001",
        "total_orders": 2,
        "orders": [
            {
                "order_id": "ORD-X1Y2Z3W4",
                "restaurant_id": "REST001",
                "items": [...],
                "final_amount": 667.9,
                "order_status": "confirmed",
                "ordered_at": "2024-01-15T10:30:00Z"
            }
        ]
    }
    """
    orders = get_user_orders(user_id)
    return {
        "status": "success",
        "user_id": user_id,
        "total_orders": len(orders),
        "orders": orders,
    }
