from pydantic import BaseModel


class Item(BaseModel):
    """
    Define the attributes of an Item
    """

    db_name: str = None
    collection_name: str = None
    name: str = None
    description: str = None
    redis_id: str = None


class Collection(BaseModel):
    """
    Define the attributes needed to create a Collection
    """

    db_name: str = None
    collection_name: str = None
    redis_id: str = None
