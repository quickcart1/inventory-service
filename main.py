import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, create_engine, select
from typing import List
from models import InventoryItem, InventoryItemCreate, InventoryItemUpdate

# Try to use PostgreSQL from env vars first, fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Build PostgreSQL URL from Spring Boot style env vars if available
    host = os.getenv("SPRING_DATASOURCE_URL", "").replace("jdbc:postgresql://", "").split("/")[0]
    if host and ":" in host:
        host, port = host.split(":")
        db_name = os.getenv("SPRING_DATASOURCE_URL", "").split("/")[-1]
        username = os.getenv("SPRING_DATASOURCE_USERNAME", "postgres")
        password = os.getenv("SPRING_DATASOURCE_PASSWORD", "password")
        DATABASE_URL = f"postgresql://{username}:{password}@{host}:{port}/{db_name}"
    else:
        # Fallback to SQLite for local development
        DATABASE_URL = "sqlite:///./inventory.db"

engine = create_engine(DATABASE_URL, echo=True)

app = FastAPI(title="QuickKart Inventory Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_db_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def on_startup():
    create_db_tables()
    seed_data()


def seed_data():
    with Session(engine) as session:
        existing = session.exec(select(InventoryItem)).first()
        if existing:
            return  # Already seeded

        items = [
            InventoryItem(product_id=1,  quantity=50,  warehouse="Mumbai",    low_stock_threshold=10),
            InventoryItem(product_id=2,  quantity=35,  warehouse="Mumbai",    low_stock_threshold=5),
            InventoryItem(product_id=3,  quantity=200, warehouse="Delhi",     low_stock_threshold=20),
            InventoryItem(product_id=4,  quantity=80,  warehouse="Bangalore", low_stock_threshold=10),
            InventoryItem(product_id=5,  quantity=150, warehouse="Delhi",     low_stock_threshold=15),
            InventoryItem(product_id=6,  quantity=60,  warehouse="Bangalore", low_stock_threshold=8),
            InventoryItem(product_id=7,  quantity=90,  warehouse="Mumbai",    low_stock_threshold=10),
            InventoryItem(product_id=8,  quantity=45,  warehouse="Hyderabad", low_stock_threshold=5),
            InventoryItem(product_id=9,  quantity=40,  warehouse="Delhi",     low_stock_threshold=5),
            InventoryItem(product_id=10, quantity=70,  warehouse="Hyderabad", low_stock_threshold=10),
        ]
        for item in items:
            session.add(item)
        session.commit()
        print("✅ Seeded 10 dummy inventory items.")


@app.get("/api/inventory", response_model=List[InventoryItem])
def get_all_inventory(session: Session = Depends(get_session)):
    return session.exec(select(InventoryItem)).all()


@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@app.get("/api/inventory/product/{product_id}", response_model=InventoryItem)
def get_inventory_by_product(product_id: int, session: Session = Depends(get_session)):
    item = session.exec(
        select(InventoryItem).where(InventoryItem.product_id == product_id)
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory not found for product")
    return item


@app.post("/api/inventory", response_model=InventoryItem, status_code=201)
def create_inventory(item: InventoryItemCreate, session: Session = Depends(get_session)):
    db_item = InventoryItem.from_orm(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@app.patch("/api/inventory/{item_id}", response_model=InventoryItem)
def update_inventory(
    item_id: int,
    update_data: InventoryItemUpdate,
    session: Session = Depends(get_session),
):
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.delete("/api/inventory/{item_id}", status_code=204)
def delete_inventory(item_id: int, session: Session = Depends(get_session)):
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    session.delete(item)
    session.commit()


@app.get("/health")
def health():
    return {"status": "ok", "service": "inventory-service"}
