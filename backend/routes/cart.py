"""
=============================================================
CART ROUTES — DEPRECATED FILE (FIX #14)
=============================================================
This file is intentionally empty and is NOT imported in main.py.

Cart endpoints are defined in routes/order.py since they share
the same flow (add → remove → view → checkout):

  POST /order/add    → Add item to cart
  POST /order/remove → Remove item from cart
  GET  /cart         → View cart contents
  POST /checkout     → Convert cart to an order

This file has been kept only to avoid breaking existing tooling
that expects a `routes/cart.py` file. It contains no logic.
=============================================================
"""

# All cart routes are in routes/order.py
# This file is a placeholder — do not add code here.
