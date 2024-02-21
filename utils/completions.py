
from typing import List
from pymongo.database import Database
import os
from pymongo import MongoClient
import re

from models import DimensionAsset, QueryBatch
from .constants import suffix, EMOJI_TO_INT, capture_emojis_pattern
import requests


def format_queries_for_vllm(query_batch: QueryBatch, assets: List[DimensionAsset], tokenizer):
    print("formatting queries for vllm...")

    assets_dict = {a.index: a for a in assets}

    # prefixes = {prefix['prefix_index']: prefix for prefix in list(db[f'prefixes'].find({}))}

    prompt_dict = {}
    for dim_rating in query_batch.query_list:
        prefix = assets_dict[dim_rating.prefix_index].text if dim_rating.prefix_index in assets_dict else ""
        prompt = assets_dict[dim_rating.prompt_index].text
        sample = assets_dict[dim_rating.sample_index].text
        combined = f"{prefix}{prompt}\nSample:\n{sample}{suffix}"
        try:
            combined = tokenizer.apply_chat_template(
                conversation=[{"role": "user", "content": combined}], tokenize=False)
        except:
            print("Applying Chat template Failed... Using default template...")
            combined = f"{combined}\n Integer:\n"

        prompt_dict[combined] = str(dim_rating.id)
    print(len(prompt_dict), "queries in batch")

    return prompt_dict


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
