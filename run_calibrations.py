from dotenv import load_dotenv
load_dotenv('.env-db')
from pymongo import MongoClient
import os
import argparse
from vllm import LLM, SamplingParams
import json
import tqdm
from llm_prompt_templates import *
import time 

llms = ['']


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

def get_query_collections(db: MongoClient):
    collection_names = [f'calibration_queries/{llm}' for llm in llms]
    return collection_names

def get_output_collections():
    collection_names = [f'calibration_outputs/{llm}' for llm in llms]
    return collection_names


if __name__ == "__main__":

    

    parser = argparse.ArgumentParser()
    parser.add_argument("--llm_name", type=str)
    parser.add_argument("--gpus", type=int)
    parser.add_argument("--temp", type=float, default=0.2)
    parser.add_argument("--topp", type=float, default=1)
    parser.add_argument("--max_gen", type=int, default=float('inf'))
    parser.add_argument("--test_run_dir", type=str, default='./test_prompts.json')
    parser.add_argument("--is_test_run", type=bool, default=True)


    args = parser.parse_args()
    assert args.llm_name in LLM_TEMPLATES.keys(), f"llm_name must be one of {LLM_TEMPLATES.keys()}"
    assert 1<=args.gpus<=4, "gpus must be between 1 and 4"
    assert args.test_run in [True, False], "test_run must be True or False"

    llm_name = args.llm_name
    # initialize LLM
    llm = LLM(model=llm_name, tensor_parallel_size=args.gpus, trust_remote_code=True, download_dir='./models-weights')
    sampling_params = SamplingParams(temperature=args.temp, top_p=args.topp, max_tokens=1)
    batch_size = 128
    # initialize dbs
    collection = None


    if args.is_test_run:
        with open(args.test_run_dir, 'r') as f:
            print("Loading test prompts")
            prompts = json.load(f)
            print(f"Loaded {len(prompts)} prompts!")
    else:
        prompts = ['hello my name is ']
    
    prompts = prompts[:args.max_gen]
    batch_num=0
    start = time.time()
    while True: 
        # Poll database for n queries in the 'ready' state
        cur_prompts = prompts[batch_num*batch_size: (batch_num+1)*batch_size]
        if not cur_prompts:
            print("No more prompts to generate")
            break
        cur_prompts = [LLM_TEMPLATES[llm_name].format(prompt=prompt) for prompt in cur_prompts]
		# If there are none, poll for queries in the 'defective' state

	    # Format query in LLM prompt style

        # Add queries to list

        # call "generate" on the list
        outputs = llm.generate(cur_prompts, sampling_params, use_tqdm=True).output
        print(f"Generated text: {[output.text for output in outputs]}")
		#extract integer rating
        
		#collect timing stats

		#update db listings with status="processed" and the value of the rating
        batch_num+=1

    end = time.time()
    print("Done! Overall timing stats: ")
    print("LATENCY:", (start-end)/len(prompts))
    print("THROUGHPUT:", len(prompts)/(start-end))
    print("NUM_PROMPTS:", len(prompts))

