"""
=============================================================
USER PYDANTIC MODELS
=============================================================
These models define the data shape for user-related operations.

Pydantic models serve two purposes:
1. REQUEST VALIDATION  - Ensures incoming API data is correct
2. RESPONSE FORMATTING - Controls what data goes back to the client

The 'model_config' with json_schema_extra provides example
values that show up in the Swagger docs (/docs) for testing.
=============================================================
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


# -------------------------------------------------------
# Address sub-model (embedded inside the user document)
# -------------------------------------------------------
class Address(BaseModel):
    """A single delivery address for a user."""
    label: str = Field(..., description="Label like 'Home', 'Work', 'Other'")
    full_address: str = Field(..., description="Complete street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State name")
    pincode: str = Field(..., description="Postal/ZIP code")
    is_default: bool = Field(default=False, description="Whether this is the default address")


# -------------------------------------------------------
# REQUEST MODEL: Register a new user
# -------------------------------------------------------
class UserRegisterRequest(BaseModel):
    """Data required to register a new user."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")
    email: str = Field(..., description="Email address (must be unique)")
    phone: str = Field(..., min_length=10, max_length=15, description="Phone number")
    addresses: List[Address] = Field(default=[], description="List of delivery addresses")
    preferred_language: str = Field(default="en", description="Preferred language code")
    favorite_cuisines: List[str] = Field(default=[], description="List of favorite cuisine types")

    model_config = {
        "json_schema_extra": {
            "examples": [
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
                            "is_default": True
                        }
                    ],
                    "preferred_language": "en",
                    "favorite_cuisines": ["Indian", "Chinese"]
                }
            ]
        }
    }


# -------------------------------------------------------
# RESPONSE MODEL: User profile data returned to client
# -------------------------------------------------------
class UserResponse(BaseModel):
    """User data returned in API responses (no MongoDB _id)."""
    user_id: str
    name: str
    email: str
    phone: str
    addresses: List[Address] = []
    preferred_language: str = "en"
    favorite_cuisines: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
