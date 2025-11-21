from typing import List
from schema import ProductSchema

class ParserClass:
    @classmethod
    def parse(cls, product_name: str) -> List[ProductSchema]:
        """
        Abstract method to parse products.
        Should be overridden by each marketplace service.
        """
        raise NotImplementedError("Parser must implement the parse method")
