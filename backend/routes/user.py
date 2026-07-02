"""
=============================================================
USER ROUTES
=============================================================
API endpoints for user registration and profile management.

FIX #5: Business logic has been moved out of the route
handlers and into services/user_service.py. The routes now
only handle HTTP concerns (request parsing, error codes).

ENDPOINTS:
  POST /user/register     → Register a new user
  GET  /user/{user_id}    → Get user profile
=============================================================
"""

from fastapi import APIRouter, HTTPException
from models.user_models import UserRegisterRequest
from services.user_service import register_user, get_user

# Create router with /user prefix and "Users" tag for Swagger
router = APIRouter(prefix="/user", tags=["Users"])


@router.post(
    "/register",
    summary="Register a new user",
    description="Creates a new user account with profile information and delivery addresses."
)
def register_user_endpoint(request: UserRegisterRequest):
    """
    POST /user/register

    Registers a new user in the system. Email must be unique.

    Sample Request:
    {
        "name": "Rahul Sharma",
        "email": "rahul@example.com",
        "phone": "9876543210",
        "addresses": [
            {
                "label": "Home",
                "full_address": "123 MG Road, Apt 4B",
                "city": "Bangalore",
                "state": "Karnataka",
                "pincode": "560001",
                "is_default": true
            }
        ],
        "preferred_language": "en",
        "favorite_cuisines": ["Indian", "Chinese"]
    }

    Sample Response:
    {
        "status": "success",
        "message": "User registered successfully",
        "user": {
            "user_id": "USR-A1B2C3D4",
            "name": "Rahul Sharma",
            ...
        }
    }
    """
    try:
        user_doc = register_user(
            name=request.name,
            email=request.email,
            phone=request.phone,
            addresses=[addr.model_dump() for addr in request.addresses],
            preferred_language=request.preferred_language,
            favorite_cuisines=request.favorite_cuisines,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "success",
        "message": "User registered successfully",
        "user": user_doc,
    }


@router.get(
    "/{user_id}",
    summary="Get user profile",
    description="Returns the profile details for a specific user."
)
def get_user_endpoint(user_id: str):
    """
    GET /user/USR-A1B2C3D4

    Returns the user's profile including addresses and preferences.

    Sample Response:
    {
        "status": "success",
        "user": {
            "user_id": "USR-A1B2C3D4",
            "name": "Rahul Sharma",
            "email": "rahul@example.com",
            "phone": "9876543210",
            "addresses": [...],
            "preferred_language": "en",
            "favorite_cuisines": ["Indian", "Chinese"],
            "created_at": "2024-01-15T10:30:00Z"
        }
    }
    """
    user = get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with ID '{user_id}' not found"
        )

    return {"status": "success", "user": user}
