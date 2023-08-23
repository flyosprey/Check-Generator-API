from typing import List, Optional

from pydantic import BaseModel, Field, constr


class Product(BaseModel):
    name: str
    price: float = Field(gt=0)
    quantity: int = Field(gt=0)


class Payment(BaseModel):
    type: constr(regex="cash|cashless")
    amount: float = Field(gt=0)


class Order(BaseModel):
    products: List[Product]
    payment: Payment
    buyer_name: str
    comment: Optional[str]
