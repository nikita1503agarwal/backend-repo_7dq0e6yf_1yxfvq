import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Restaurant, MenuItem, Order, OrderItem, Customer

app = FastAPI(title="Food Delivery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utility

def to_obj_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


def serialize(doc: dict):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/")
def read_root():
    return {"message": "Food Delivery Backend Ready"}


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
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response


# Seed sample data if empty
@app.post("/seed")
def seed_sample_data():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    if db["restaurant"].count_documents({}) == 0:
        r1_id = create_document("restaurant", Restaurant(
            name="Pasta Palace",
            description="Authentic Italian pastas and pizzas",
            cuisine="Italian",
            image_url="https://images.unsplash.com/photo-1603133872878-684f208fb84f",
            rating=4.7,
            delivery_fee=2.99,
            eta_minutes=30
        ))
        r2_id = create_document("restaurant", Restaurant(
            name="Spice Route",
            description="North Indian curries and tandoori",
            cuisine="Indian",
            image_url="https://images.unsplash.com/photo-1604908177673-3f4f5463f2ef",
            rating=4.6,
            delivery_fee=3.49,
            eta_minutes=35
        ))
        # Menu items
        create_document("menuitem", MenuItem(restaurant_id=r1_id, name="Margherita Pizza", description="Classic with fresh basil", price=12.99, image_url="https://images.unsplash.com/photo-1548365328-9f547fb09530"))
        create_document("menuitem", MenuItem(restaurant_id=r1_id, name="Fettuccine Alfredo", description="Creamy parmesan sauce", price=14.5, image_url="https://images.unsplash.com/photo-1529042410759-befb1204b468"))
        create_document("menuitem", MenuItem(restaurant_id=r2_id, name="Butter Chicken", description="Rich tomato gravy", price=13.99, image_url="https://images.unsplash.com/photo-1588167056547-c183313da70a"))
        create_document("menuitem", MenuItem(restaurant_id=r2_id, name="Paneer Tikka", description="Grilled cottage cheese", price=11.25, is_veg=True, image_url="https://images.unsplash.com/photo-1596797038530-2c107229f829"))

    return {"status": "ok"}


# Restaurants
@app.get("/restaurants")
def list_restaurants():
    docs = get_documents("restaurant")
    return [serialize(d) for d in docs]


@app.get("/restaurants/{restaurant_id}")
def get_restaurant(restaurant_id: str):
    doc = db["restaurant"].find_one({"_id": to_obj_id(restaurant_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return serialize(doc)


@app.get("/restaurants/{restaurant_id}/menu")
def get_menu(restaurant_id: str):
    docs = list(db["menuitem"].find({"restaurant_id": restaurant_id}))
    return [serialize(d) for d in docs]


# Orders
class CreateOrder(BaseModel):
    restaurant_id: str
    items: List[OrderItem]
    customer_name: str
    customer_address: str
    customer_email: Optional[str] = None


@app.post("/orders")
def create_order(payload: CreateOrder):
    # Compute totals
    menu_docs = {str(d["_id"]): d for d in db["menuitem"].find({"_id": {"$in": [to_obj_id(i.menu_item_id) for i in payload.items]}})}
    if not menu_docs:
        raise HTTPException(status_code=400, detail="Invalid items")

    subtotal = 0.0
    for it in payload.items:
        doc = menu_docs.get(it.menu_item_id)
        if not doc:
            raise HTTPException(status_code=400, detail="Menu item not found")
        subtotal += float(doc.get("price", 0)) * it.quantity

    rest = db["restaurant"].find_one({"_id": to_obj_id(payload.restaurant_id)})
    if not rest:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    delivery_fee = float(rest.get("delivery_fee", 0))
    total = round(subtotal + delivery_fee, 2)

    order_doc = Order(
        restaurant_id=payload.restaurant_id,
        customer_name=payload.customer_name,
        customer_address=payload.customer_address,
        customer_email=payload.customer_email,
        items=payload.items,
        subtotal=round(subtotal, 2),
        delivery_fee=delivery_fee,
        total=total,
        status="pending",
    )
    order_id = create_document("order", order_doc)
    return {"id": order_id, "status": "pending", "total": total}


@app.get("/orders")
def list_orders(limit: int = 50):
    docs = get_documents("order", limit=limit)
    return [serialize(d) for d in docs]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
