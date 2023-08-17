import time
import signal
import re
from time import sleep
from bson import ObjectId
import requests
from utils.utils import *
from llm_prompt_templates_v2 import *
import tqdm
import json
from vllm import LLM, SamplingParams
import argparse
import os
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
import asyncio
from state import CalibratorState
from dotenv import load_dotenv
load_dotenv('.env-db')
proc_controller_url = os.getenv('PROC_CONTROLLER_URL')

state = CalibratorState(instance_name='SYNTHETIC_RATER_N')

# Handle interrupts gracefully


def send_cleanup_signal(queries: list, collection_name: str) -> bool:
    # call calibration controller
    headers = {
        'Content-Type': 'application/json',
    }
    queries = [{i: str(query[i]) if isinstance(
        query[i], ObjectId) else query[i] for i in query} for query in queries]
    data = json.dumps({'queries': queries, 'collection_name': collection_name})
    response = requests.post(
        f'{proc_controller_url}/calibrations/cleanup', headers=headers, data=data)
    if response.status_code != 200:
        print(f"Error with cleanup: {response.status_code}")
        return False
    return True


async def get_all_docs_from_collection(coll: AsyncIOMotorCollection):
    res = await coll.find({}).to_list(length=2_000_000)
    return res


def get_raw_queries(n_queries: int = 512):
    """_summary_
    Calls process controller for queries to rate next
    Args:
        n_queries (int, optional): _description_. Defaults to 10000.

    Returns:
        _type_: _description_
    """
    # call calibration controller
    headers = {
        'Content-Type': 'application/json',
    }
    data = json.dumps({'n_queries': n_queries, 'llm_name': llm_name})

    try:
        response = requests.post(
            f'{proc_controller_url}/calibrations/get-batch', headers=headers, data=data)
    except Exception as e:
        print("error getting queries from proc controller")
        sleep(30)
        return [], {}, ''
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return [], {}, ''
    response = response.json()
    queries, collection_name = response['queries'], response['collection_name']


def get_queries(n_queries: int = 10000, samples: dict = {}, prompts: dict = {}, prefixes: dict = {}) -> tuple:

    # format into prompts
    prompt_dict = {}
    try:
        for query in queries:
            query['_id'] = ObjectId(query['_id'])
            prefix = prefixes[query['prefix_index']]['prefix']
            prompt = prompts[query['prompt_index']]['combined_prompt']
            sample = samples[query['sample_index']]['sample']
            combined = f"{prefix}\n{prompt}\nSample:\n{sample}"
            prompt_dict[LLM_TEMPLATES[llm_name].format(
                prompt=combined)] = query['_id']
    except Exception as e:
        print(query)
        print(prefix, prompt, sample)
        print(combined)
        print(e)

        send_cleanup_signal(queries, collection_name)
        print("error indexing prompts/samples/prefixes get_queries")
        exit()
    return queries, prompt_dict, collection_name


async def update_queries_with_ratings(queries: list, collection: Motoro):
    for query in queries:
        collection.update_one(
            {'_id': query['_id']}, {'$set': query})


async def main():
    load_dotenv('.env-db')
    proc_controller_url = os.getenv('PROC_CONTROLLER_URL')
    db = get_aDatabase()
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm_name", type=str)
    parser.add_argument("--gpus", type=int)
    parser.add_argument("--temp", type=float, default=1)
    parser.add_argument("--topp", type=float, default=1)
    parser.add_argument("--topk", type=int, default=10)
    parser.add_argument("--max_gen", type=int, default=float('inf'))
    parser.add_argument("--test_run_dir", type=str,
                        default='./test_prompts.json')
    parser.add_argument("--is_test_run", type=bool, default=False)
    parser.add_argument('--debug', type=bool, default=False)
    parser.add_argument('--batch_size', type=int, default=3000)

    args = parser.parse_args()

    debugprint = print if args.debug else lambda *x: None

    assert args.llm_name in LLM_TEMPLATES.keys(
    ), f"llm_name must be one of {LLM_TEMPLATES.keys()}"
    assert 1 <= args.gpus <= 4, "gpus must be between 1 and 4"
    assert args.is_test_run in [True, False], "test_run must be True or False"

    llm_name = args.llm_name

    # initialize LLM
    llm = LLM(model=llm_name, tensor_parallel_size=args.gpus, trust_remote_code=True, download_dir='./models-weights',
              max_num_batched_tokens=3600, swap_space=4, gpu_memory_utilization=0.96)
    sampling_params = SamplingParams(temperature=args.temp, max_tokens=2)

    batch_size = args.batch_size
    debugprint(f"Batch size: {batch_size}")
    batch_num = 0
    prefixes = await db['prefixes'].find({}).to_list()
    prefixes = {prefix['prefix_index']: prefix for prefix in list()}
    debugprint(f"Loaded {len(prefixes)} prefixes successfully")

    prompts = {}
    samples = {}
    start = time.time()
    queries = []
    # Handle interrupts gracefully

    def handler(signum, frame):
        if queries:
            send_cleanup_signal(queries, collection_name)
        exit(1)
    signal.signal(signal.SIGINT, handler)

    while not collection_name:
        try:
            _, _, collection_name = get_queries(n_queries=0)

            # get batch of queries from controller
            dim = re.findall(r'/(\w+)$', collection_name)[0]

            prompts = {prompt['prompt_index']: prompt for prompt in list(
                db[f'core_prompts/{dim}'].find({}))}
            assert len(prompts) > 0
            debugprint(f"Loaded {len(prompts)} prompts successfully")
            samples = {sample['sample_index']: sample for sample in list(
                db[f'samples/{dim}'].find({}))}
            assert len(samples) > 0
            debugprint(f"Loaded {len(samples)} samples successfully")
        except:
            print("Error connecting to controller!! Sleeping for 1 minute")
        sleep(60)
    while True:
        batch_start = time.time()
        debugprint('Queries rated:', batch_num*batch_size)
        queries, cur_prompts_dict, collection_name = get_queries(
            n_queries=batch_size, samples=samples, prompts=prompts, prefixes=prefixes)

        debugprint(f"Loaded {len(queries)} queries successfully")

        if not queries or len(queries) == 0:
            print("No more queries to rate!!! Sleeping for 1 minute")
            sleep(60)

        # Format query in LLM prompt style
        cur_prompts = list(cur_prompts_dict.keys())

        # call "generate" on the list
        outputs = llm.generate(cur_prompts, sampling_params)
        # extract integer rating
        ratings = {}
        for output in tqdm.tqdm(outputs):
            query_id = cur_prompts_dict[output.prompt]
            try:
                ratings[query_id] = int(output.outputs[0].text)
            except:
                try:
                    ratings[query_id] = int(output.outputs[0].text[0])
                except:
                    ratings[query_id] = -1

        debugprint(f"Sample Ratings: {list(ratings.values())[-10:]}")

        cur_finished_query_tasks = []
        # update db listings with the value of the rating
        for query in queries:
            query['rating'] = -1
            if query['_id'] in ratings:
                query['rating'] = ratings[query['_id']]
            else:
                debugprint("Error: query id not in ratings!")
            query['num_tries'] += 1
            query['latency'] = (time.time()-batch_start)/batch_size
            task = asyncio.create_task(db[collection_name].update_one(
                {'_id': query['_id']}, {'$set': query}))
            cur_finished_query_tasks.append(task)
        batch_num += 1
    send_cleanup_signal(
        queries=queries, collection_name=collection_name)
    end = time.time()
    print("Done! Overall timing stats: ")
    print("LATENCY:", (end-start)/len(prompts))
    print("NUM_PROMPTS:", len(prompts))

if __name__ == "__main__":
    main()
