from pydantic import BaseModel, HttpUrl
from datetime import datetime
from enum import Enum
from typing import Optional

class ParserSource(Enum):
    EBAY = "EBAY"
    AMAZON = "AMAZON"

class ProductSchema(BaseModel):
    product_id: str
    parsed_source: ParserSource
    product_title: str
    product_price: float
    product_rating: Optional[float] = None
    product_sold_out: Optional[int] = None
    product_views: Optional[int] = None
    product_image: Optional[HttpUrl] = None
    product_url: HttpUrl
    product_parsed_date: datetime