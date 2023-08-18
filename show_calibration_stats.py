import pandas as pd
from tqdm import tqdm
from utils.utils import get_database, all_scales, all_llms
from dotenv import load_dotenv
load_dotenv('.env-db')


def count_tokens(prompt):
    return len(tokenizer.tokenize(prompt))


db = get_database()

scales = ['contrast']
llms = all_llms

llm_name = llms[0]
dim = scales[0]
all_llm_ratings_in_scale = list(db[f'queries/{llm_name}/{dim}'].find({}))


# TQDM SETTINGS
bar_format = '{desc}: {percentage:3.0f}%\\n| {bar}| \\n {n_fmt}/{total_fmt}{postfix} '
for dim in scales:
    for llm_name in llms:
        num_in_progress, num_done, num_ready, num_need_to_retry = 0, 0, 0, 0
        for rating_doc in (all_llm_ratings_in_scale):
            if rating_doc['rating'] == -1 and rating_doc['latency'] == -1:
                num_ready += 1
            elif rating_doc['rating'] == -1 and rating_doc['latency'] > 0:
                num_need_to_retry += 1
            elif rating_doc['rating'] > -1:
                num_done += 1
            # TODO: case for in_progress ratings.
        pbar = tqdm(
            total=len(all_llm_ratings_in_scale), bar_format=bar_format)
        pbar.set_description('SCLAE: ' + dim.upper() + ' || ' +
                             'LLM: ' + llm_name[llm_name.index('/') + 1:])
        pbar.update(num_done)
        pbar.set_postfix({'# in progress': num_in_progress, '# done': num_done,
                         '# ready': num_ready, '# need_to_retry': num_need_to_retry})
