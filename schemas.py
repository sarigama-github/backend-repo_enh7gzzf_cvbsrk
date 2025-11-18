"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import date

# Promotion SaaS Schemas

class Business(BaseModel):
    """
    Businesses collection schema
    Collection name: "business"
    """
    name: str = Field(..., description="Business name")
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    website: Optional[str] = Field(None, description="Website URL")
    description: Optional[str] = Field(None, description="Short description of the business")
    location: Optional[str] = Field(None, description="City/Country or address")
    industry: Optional[str] = Field(None, description="Industry category, e.g., Retail, Food, Tech")
    is_verified: bool = Field(False, description="Whether the business is verified by the platform")

class Promotion(BaseModel):
    """
    Promotions collection schema
    Collection name: "promotion"
    """
    business_id: str = Field(..., description="Related business document id (string)")
    title: str = Field(..., description="Promotion title")
    description: Optional[str] = Field(None, description="Promotion details")
    image_url: Optional[str] = Field(None, description="Banner or product image URL")
    start_date: Optional[date] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="End date (YYYY-MM-DD)")
    discount_type: Optional[str] = Field(None, description="Type of discount: percent, amount, bogo, free_shipping, etc.")
    discount_value: Optional[float] = Field(None, ge=0, description="Numerical discount amount or percent")
    terms: Optional[str] = Field(None, description="Terms and conditions")
    tags: Optional[List[str]] = Field(default_factory=list, description="Searchable tags")
    is_active: bool = Field(True, description="Whether the promotion is active")

# Example schemas kept for reference (not used directly by the app)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# The Flames database viewer may read these via GET /schema
SCHEMAS_META = {
    "business": {
        "fields": {
            "name": "string",
            "email": "string?",
            "phone": "string?",
            "website": "string?",
            "description": "string?",
            "location": "string?",
            "industry": "string?",
            "is_verified": "boolean"
        }
    },
    "promotion": {
        "fields": {
            "business_id": "string",
            "title": "string",
            "description": "string?",
            "image_url": "string?",
            "start_date": "date?",
            "end_date": "date?",
            "discount_type": "string?",
            "discount_value": "number?",
            "terms": "string?",
            "tags": "string[]?",
            "is_active": "boolean"
        }
    }
}
