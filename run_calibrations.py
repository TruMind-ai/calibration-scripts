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
from pymongo.collection import Collection
from vllm import LLM, SamplingParams
import argparse
import os
import random
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv('.env-db')


def handler(signum, frame):
    if queries:
        send_cleanup_signal(queries, collection_name)
    exit(1)


signal.signal(signal.SIGINT, handler)


def send_cleanup_signal(queries: list, collection_name: str, excep: str):
    # call calibration controller
    headers = {
        'Content-Type': 'application/json',
    }
    queries = [{i: str(query[i]) if isinstance(
        query[i], ObjectId) else query[i] for i in query} for query in queries]
    data = json.dumps(
        {'queries': queries, 'collection_name': collection_name, 'exception': excep})
    response = requests.post(
        f'{proc_controller_url}/calibrations/cleanup', headers=headers, data=data)
    if response.status_code != 200:
        print(f"Error with cleanup: {response.status_code}")
        return False
    return True


def get_queries(n_queries=10000, samples={}, prompts={}, prefixes={}):
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

        send_cleanup_signal(queries, collection_name, str(e))
        print("error indexing prompts/samples/prefixes get_queries")
        exit()
    return queries, prompt_dict, collection_name


if __name__ == "__main__":
    load_dotenv('.env-db')
    proc_controller_url = os.getenv('PROC_CONTROLLER_URL')
    db = get_database()
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

    prefixes = {prefix['prefix_index']
        : prefix for prefix in list(db['prefixes'].find({}))}
    debugprint(f"Loaded {len(prefixes)} prefixes successfully")

    prompts = {}

    samples = {}
    start = time.time()
    queries = []
    while True:
        batch_start = time.time()
        debugprint('Queries rated:', batch_num*batch_size)
        # get batch of queries from controller
        try:
            if prompts == {} or samples == {}:
                _, _, collection_name = get_queries(n_queries=0)
                if collection_name == '':
                    print("Error connecting to controller!! Sleeping for 1 minute")
                    sleep(60)
                    continue
                dim = re.findall(r'/(\w+)$', collection_name)[0]
                prompts = {prompt['prompt_index']: prompt for prompt in list(
                    db[f'core_prompts/{dim}'].find({}))}
                debugprint(f"Loaded {len(prompts)} prompts successfully")
                samples = {sample['sample_index']: sample for sample in list(
                    db[f'samples/{dim}'].find({}))}
                debugprint(f"Loaded {len(samples)} samples successfully")
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

            # collect timing stats
            # update db listings with the value of the rating
            for i, query in enumerate(queries):
                query['rating'] = -1
                if query['_id'] in ratings:
                    query['rating'] = ratings[query['_id']]
                else:
                    debugprint("Error: query id not in ratings!")
                query['num_tries'] += 1
                query['latency'] = (time.time()-batch_start)/batch_size
                db[collection_name].update_one(
                    {'_id': query['_id']}, {'$set': query})
            batch_num += 1
        except Exception as e:
            send_cleanup_signal(
                queries=queries, collection_name=collection_name, excep=str(e))
    end = time.time()
    print("Done! Overall timing stats: ")
    print("LATENCY:", (end-start)/len(prompts))
    print("THROUGHPUT:", len(prompts)/(end-start))
    print("NUM_PROMPTS:", len(prompts))
