from tqdm import tqdm
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv('.env-db')
# from transformers import LlamaTokenizerFast
# tokenizer = LlamaTokenizerFast.from_pretrained('hf-internal-testing/llama-tokenizer')
# def count_tokens(prompt):
# return len(tokenizer.tokenize(prompt))

all_scales = ['contrast', 'authority', 'consensus',
              'consistency', 'scarcity', 'unity', 'liking', 'reciprocity']
all_llms = ['OpenAssistant/llama2-13b-orca-8k-3319',
            'openchat/openchat_v3.1', 'baichuan-inc/Baichuan-13B-Base']

llm_short_name_mapping = {
    'OpenAssistant/llama2-13b-orca-8k-3319': 'Llama-2-orca-13B',
    'openchat/openchat_v3.1': 'Openchat_v3.1-13B',
    'baichuan-inc/Baichuan-13B-Base': 'Baichuan-13B'
}


def get_database() -> MongoClient:
    '''
    This function returns associated MongoDB database 
    for calibrations
    '''
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = os.getenv('CONNECTION_STRING')
    DB_NAME = os.getenv('CALIBRATIONS_DB')
    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)
    # return database
    return client[DB_NAME]


def display_rating_progress_many(scales=['contrast'], llms=[''], db=get_database(), bar_format='{percentage:3.0f}%| {bar} |{n_fmt}/{total_fmt}'):
    for dim in scales:
        for llm_name in llms:
            display_rating_progress_single(
                dim, llm_name, db=db, bar_format=bar_format)


def display_rating_progress_single(dim: str, llm_name: str, all_llm_ratings_in_scale=None, db=get_database(), bar_format='{percentage:3.0f}%| {bar} |{n_fmt}/{total_fmt}'):
    if not all_llm_ratings_in_scale:
        all_llm_ratings_in_scale = list(
            db[f'queries/{llm_name}/{dim}'].find({}))
    num_in_progress, num_done, num_ready, num_need_to_retry = 0, 0, 0, 0
    for rating_doc in (all_llm_ratings_in_scale):
        if rating_doc['rating'] == -1 and rating_doc['latency'] == -1:
            num_ready += 1
        elif rating_doc['rating'] == -1 and rating_doc['latency'] > 0:
            num_need_to_retry += 1
        elif rating_doc['rating'] > -1:
            num_done += 1
        # TODO: case for in_progress ratings.

    print("============================")
    meta = {
        'DIMENSION': dim.upper(),
        'LLM': llm_short_name_mapping[llm_name]
    }
    print(*[f'{k}: {meta[k]}' for k in meta], sep=' || ')

    # Print progress bar
    pbar = tqdm(total=len(all_llm_ratings_in_scale), bar_format=bar_format)
    pbar.update(num_done)
    pbar.close()

    stats = {'IN PROGRESS': num_in_progress, 'DONE': num_done,
             'READY': num_ready, 'DEFECTIVE': num_need_to_retry}
    print(*[f'{k}: {stats[k]}' for k in stats], sep=' || ')
    print("============================")
