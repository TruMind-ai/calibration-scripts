from models import DimensionRating
from pydantic import BaseModel
from typing import List

class QueryBatch(BaseModel):
    query_list: List[DimensionRating]
    llm_name: str
    dimension_id: str

