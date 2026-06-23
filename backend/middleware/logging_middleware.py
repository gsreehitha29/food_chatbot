"""
=============================================================
REQUEST LOGGING MIDDLEWARE
=============================================================
Logs every incoming API request with timing information.

This middleware wraps every request and:
1. Records the start time
2. Lets the request proceed normally
3. Records the end time
4. Prints a log line with method, path, status, and duration

WHAT IS MIDDLEWARE?
Middleware sits between the client and your route handlers.
Every request passes through middleware BEFORE reaching the
route, and every response passes through it AFTER.

    Client → Middleware → Route Handler → Middleware → Client
=============================================================
"""

import time
from fastapi import Request


async def log_request_middleware(request: Request, call_next):
    """
    Middleware function that logs request details and timing.
    
    Args:
        request: The incoming HTTP request
        call_next: Function to call the next middleware/route
    
    Returns:
        The HTTP response from the route handler
    """
    # Record start time
    start_time = time.time()

    # Get request details
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"

    # Let the request proceed to the route handler
    response = await call_next(request)

    # Calculate how long the request took
    duration_ms = round((time.time() - start_time) * 1000, 2)

    # Log the request details
    status_code = response.status_code
    print(
        f"📡 {method} {path} → {status_code} "
        f"({duration_ms}ms) from {client_ip}"
    )

    return response
