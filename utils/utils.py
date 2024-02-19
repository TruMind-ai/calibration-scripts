from pymongo.database import Database
import os
from pymongo import MongoClient
import re
from src.constants import *


def get_database(name: str = "dimension_creation") -> Database:
    '''
    This function returns associated MongoDB database 
    for calibrations
    '''
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = os.getenv('CONNECTION_STRING')
    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)
    # return database
    return client[name]


def extract_integer(text: str):
    res = -1
    int_pat = r'\d{1,2}'
    try:
        res = int(re.findall(int_pat, text)[0])
    except Exception as e:
        try:
            res = EMOJI_TO_INT[re.findall(capture_emojis_pattern, text)[
                0].encode('unicode_escape').decode()]
        except Exception as f:
            print(text)

    return res


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
