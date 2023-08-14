from dotenv import load_dotenv
load_dotenv('.env-db')
from pymongo import MongoClient
import random
import os
import argparse
from vllm import LLM, SamplingParams
from pymongo.collection import Collection
import json
import tqdm
from llm_prompt_templates import *
import time 



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

def get_queries(n_queries=10000):
    '''
    get n queries from the query collection
    '''
    queries = []
    num_tries = 0
    # get n queries from the query collection
    while len(queries) < n_queries and num_tries < 1:
        q = query_collection.find_one_and_update({'rating':-1, 'num_tries':num_tries},
                                                                    {'$set':{'rating':0}})
        if q is None:
            num_tries += 1
            continue
        queries.append(q)
    # format into prompts
    prompt_dict = {}
    for query in queries:
        prefix = prefixes[query['prefix_index']]['prefix']
        prompt = prompts[query['prompt_index']]['combined_prompt']
        sample = samples[query['sample_index']]['sample']
        combined = f"{prefix}\n{prompt}\nSample:\n{sample}"
        prompt_dict[LLM_TEMPLATES[llm_name].format(prompt=combined)] = query['_id']
    return queries, prompt_dict

if __name__ == "__main__":
    load_dotenv('.env-db')
    db = get_database()

    parser = argparse.ArgumentParser()
    parser.add_argument("--llm_name", type=str)
    parser.add_argument("--gpus", type=int)
    parser.add_argument("--temp", type=float, default=1)
    parser.add_argument("--topp", type=float, default=1)
    parser.add_argument("--topk", type=int, default=10)
    parser.add_argument("--max_gen", type=int, default=float('inf'))
    parser.add_argument("--test_run_dir", type=str, default='./test_prompts.json')
    parser.add_argument("--is_test_run", type=bool, default=False)
    parser.add_argument('--debug', type=bool, default=False)
    parser.add_argument('--batch_size', type=int, default=3000)
    parser.add_argument('-d','--dimension', action='append', help='<Required> Set flag', required=True)


    args = parser.parse_args()
    
    debugprint = print if args.debug else lambda *x: None

    assert args.llm_name in LLM_TEMPLATES.keys(), f"llm_name must be one of {LLM_TEMPLATES.keys()}"
    assert 1<=args.gpus<=4, "gpus must be between 1 and 4"
    assert args.is_test_run in [True, False], "test_run must be True or False"

    llm_name = args.llm_name


    # initialize LLM
    llm = LLM(model=llm_name, tensor_parallel_size=args.gpus, trust_remote_code=True, download_dir='./models-weights', 
              max_num_batched_tokens=3600, swap_space=16)
    sampling_params = SamplingParams(temperature=args.temp, max_tokens=1)

    # if args.is_test_run:
    #     with open(args.test_run_dir, 'r') as f:
    #         print("Loading test prompts")
    #         prompts = json.load(f)
    #         prompts = random.sample(prompts, len(prompts))
    #         print(f"Loaded {len(prompts)} prompts!")
    
    # prompts = prompts[:min(args.max_gen, len(prompts))]
    batch_size = args.batch_size
    debugprint(f"Batch size: {batch_size}")
    batch_num=0

    # Poll database for n queries in the 'ready' state

    for dim in args.dimension:
        prefixes = {prefix['prefix_index']:prefix for prefix in list(db['prefixes'].find({}))}
        debugprint(f"Loaded {len(prefixes)} prefixes successfully")

        prompts = {prompt['prompt_index']:prompt for prompt in list(db[f'core_prompts/{dim}'].find({}))}
        debugprint(f"Loaded {len(prompts)} prompts successfully")

        samples = {sample['sample_index']:sample for sample in list(db[f'samples/{dim}'].find({}))}
        debugprint(f"Loaded {len(samples)} samples successfully")

        query_collection = db[f'queries/{dim}/{llm_name}']
        debugprint(f"Loaded query_collection successfully")
        start = time.time()

        while True: 
            debugprint('Batch:', batch_num)
            # get batch of queries from mongoDB
            queries, cur_prompts_dict = get_queries(n_queries=batch_size)
            debugprint(f"Loaded {len(queries)} queries successfully")
            if not cur_prompts_dict:
                print("No more prompts to generate")
                break
            # debugprint(f"Sample prompt: {cur_prompts_dict[0]}")

            # Format query in LLM prompt style
            cur_prompts = list(cur_prompts_dict.keys())
            
            # call "generate" on the list
            outputs = llm.generate(cur_prompts, sampling_params)
            #extract integer rating
            ratings = {}
            for output in tqdm.tqdm(outputs):
                query_id = cur_prompts_dict[output.prompt]
                try:
                    ratings[query_id] = int(output.outputs[0].text)
                except:
                    ratings[query_id] = -1

            debugprint(f"Sample Ratings: {list(ratings.values())[-10:]}")
            
            #collect timing stats
            #update db listings with the value of the rating
            for i, query in enumerate(queries):
                if query['_id'] not in ratings:
                    print("Error: query id not in ratings")
                    continue
                query['rating'] = ratings[query['_id']]
                query['num_tries'] += 1
                query['latency'] = (time.time()-start)/batch_size
                query_collection.update_one({'_id':query['_id']}, {'$set':query})
            batch_num+=1

        end = time.time()
        print("Done! Overall timing stats: ")
        print("LATENCY:", (end-start)/len(prompts))
        print("THROUGHPUT:", len(prompts)/(end-start))
        print("NUM_PROMPTS:", len(prompts))

