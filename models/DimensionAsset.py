import json
import bson
import time
from pydantic import BaseModel, ConfigDict, Field

from .utils import PyObjectId
from typing import List, Dict, Any

import pandas as pd


class DimensionAssetType:
    PROMPT = "prompt"
    SAMPLE = "sample"


class DimensionAsset(BaseModel):

    id: PyObjectId = Field(alias="_id")
    model_config = ConfigDict(arbitrary_types_allowed=True)
    asset_type: str
    # Codes for formatting to fortran
    codes: Dict[str, Any] = {}
    text: str
    task_timestamp: int = -1
    index: int = -1
    exclude_from_rating: bool = True

    @staticmethod
    def from_list(dim_assets: List[Dict[str, Any]]):
        res = []
        for asset in dim_assets:
            res.append(DimensionAsset(**asset))
        return res

    def from_df(dim_assets: pd.DataFrame):
        res = []
        for _, row in dim_assets.iterrows():
            exclude_from_rating = row["exclude_from_rating"] if row["exclude_from_rating"] else True
            codes = json.loads(row["codes"].replace("'", '"'))
            id = row["id"] if row["id"] else row["_id"]
            res.append(DimensionAsset(_id=id, type=row["asset_type"], codes=codes, text=row["text"],
                                      index=row["index"], exclude_from_rating=exclude_from_rating))
        return res
