import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Business, Promotion

app = FastAPI(title="Promotion SaaS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id format")


def serialize(doc: dict):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    # Convert datetime to isoformat strings
    for k, v in list(doc.items()):
        if hasattr(v, "isoformat"):
            doc[k] = v.isoformat()
    return doc


@app.get("/")
def read_root():
    return {"message": "Promotion SaaS API is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, "name", None) or "Unknown"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Business Endpoints
@app.post("/api/business", response_model=dict)
def create_business(business: Business):
    inserted_id = create_document("business", business)
    return {"id": inserted_id}


@app.get("/api/business", response_model=List[dict])
def list_businesses(q: Optional[str] = None, limit: int = 50):
    filter_dict = {}
    if q:
        filter_dict = {"$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"industry": {"$regex": q, "$options": "i"}},
        ]}
    docs = get_documents("business", filter_dict, limit)
    return [serialize(d) for d in docs]


@app.get("/api/business/{business_id}", response_model=dict)
def get_business(business_id: str):
    doc = db["business"].find_one({"_id": to_object_id(business_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Business not found")
    return serialize(doc)


# Promotion Endpoints
@app.post("/api/promotions", response_model=dict)
def create_promotion(promo: Promotion):
    # Ensure business exists
    if not db["business"].find_one({"_id": to_object_id(promo.business_id)}):
        raise HTTPException(status_code=400, detail="Related business does not exist")
    inserted_id = create_document("promotion", promo)
    return {"id": inserted_id}


@app.get("/api/promotions", response_model=List[dict])
def list_promotions(q: Optional[str] = None, tag: Optional[str] = None, business_id: Optional[str] = None, active: Optional[bool] = True, limit: int = 100):
    filter_dict: dict = {}
    and_clauses = []
    if q:
        and_clauses.append({"$or": [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"terms": {"$regex": q, "$options": "i"}},
        ]})
    if tag:
        and_clauses.append({"tags": tag})
    if business_id:
        and_clauses.append({"business_id": business_id})
    if active is not None:
        and_clauses.append({"is_active": active})
    if and_clauses:
        filter_dict = {"$and": and_clauses}
    docs = get_documents("promotion", filter_dict, limit)
    # Join with business basic info
    business_map = {str(b["_id"]): b for b in db["business"].find({}, {"name": 1, "industry": 1})}
    enriched = []
    for d in docs:
        d = serialize(d)
        biz = business_map.get(d.get("business_id"))
        if biz:
            d["business_name"] = biz.get("name")
            d["industry"] = biz.get("industry")
        enriched.append(d)
    return enriched


@app.get("/api/promotions/{promo_id}", response_model=dict)
def get_promotion(promo_id: str):
    doc = db["promotion"].find_one({"_id": to_object_id(promo_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return serialize(doc)


@app.patch("/api/promotions/{promo_id}", response_model=dict)
def update_promotion_status(promo_id: str, is_active: Optional[bool] = None):
    update = {}
    if is_active is not None:
        update["is_active"] = is_active
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    res = db["promotion"].update_one({"_id": to_object_id(promo_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promotion not found")
    updated = db["promotion"].find_one({"_id": to_object_id(promo_id)})
    return serialize(updated)


# Schema endpoint for viewer/debug
@app.get("/schema")
def get_schema():
    return {
        "business": Business.model_json_schema(),
        "promotion": Promotion.model_json_schema(),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
