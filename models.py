from typing import Optional, List
from sqlmodel import Field, SQLModel


class InventoryItemBase(SQLModel):
    product_id: int
    quantity: int
    warehouse: Optional[str] = "main"
    low_stock_threshold: Optional[int] = 10


class InventoryItem(InventoryItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(SQLModel):
    quantity: Optional[int] = None
    warehouse: Optional[str] = None
    low_stock_threshold: Optional[int] = None
