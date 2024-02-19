from pydantic import BaseModel, ConfigDict, Field

from .utils import PyObjectId


class DimensionRating(BaseModel):

    id: PyObjectId = Field(alias="_id", default=None)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    rating: int = -1
    num_tries: int = 0
    latency: float = -1
    sample_index: int = -1
    prompt_index: int = -1
    prefix_index: int = -1
