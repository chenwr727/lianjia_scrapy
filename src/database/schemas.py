from pydantic import BaseModel


class HouseBase(BaseModel):
    url: str
    sell_detail: dict
    base_content: dict
    transaction_content: dict
    des_content: dict
