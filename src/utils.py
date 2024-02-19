import re
from typing import Any
from typing import Annotated, Union
from bson import ObjectId
from pydantic import PlainSerializer, AfterValidator, WithJsonSchema
import requests


def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[
    Union[str, ObjectId],
    AfterValidator(validate_object_id),
    PlainSerializer(lambda x: str(x), return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]


def calculate_num_shard(llm: str) -> int:
    '''calculates the `--num-shard` parameter based 
    on assumed GPU memory of 80GB and model is float16.

    :param llm: name of llm
    :type llm: str
    :return: number of shards (1-4)
    :rtype: int
    '''
    # billions of params
    model_num_params = 80
    try:
        # find model params from huggingface
        model_page = requests.get(f"https://huggingface.co/{llm}").text
        params = re.findall("([\d\.]+)B params", model_page)
        if not params:
            params = re.findall("([\d\.]+)B", llm)
        model_num_params = float(params[0])
    except:
        print(
            f"Couldn't find number of model params from huggingface. Defaulting to {model_num_params}...")
    # calculate approx. memory footprint
    memory_footprint = (model_num_params * 4) + 0.2*model_num_params
    return int(min(memory_footprint//80, 4))
