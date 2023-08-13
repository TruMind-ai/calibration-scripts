from dotenv import load_dotenv
load_dotenv('.env-db')
from pymongo import MongoClient
import os
import argparse
from vllm import LLM, SamplingParams
import json
import tqdm
from llm_prompt_templates import *

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
    parser.add_argument("--batch_size", type=int)
    parser.add_argument("--test_run", type=bool)

    args = parser.parse_args()
    llm_name = args.llm_name
    # initialize LLM
    llm = LLM(model=llm_name, tensor_parallel_size=args.gpus, trust_remote_code=True)
    sampling_params = SamplingParams(temperature=0, top_p=1, max_tokens=1)
    batch_size = 128
    temp = 0

    # initialize dbs
    collection = None

    with open('./test_prompts.json', 'r') as f:
        prompts=json.load(f)
    
    while True: 
        if args.test_run:
            with open('./test_prompts.json', 'r') as f:
                prompts = json.load(f)
        else:
            prompts = ['hello my name is ']

        prompts = [LLM_TEMPLATES[llm_name].format(prompt=prompt) for prompt in prompts[:batch_size]]
        # Poll database for n queries in the 'ready' state
		# If there are none, poll for queries in the 'defective' state
	    # Format query in LLM prompt style
        # Add queries to list
        # call "generate" on the list
        outputs = llm.generate(prompts, sampling_params)
        for output in tqdm.tqdm(outputs):
            generated_text = output.outputs[0].text
            print(f"Generated text: {generated_text!r}")
		#extract integer rating
		#wait for all results
        
		#collect timing stats
		#update db listings with status="processed" and the value of the rating
        pass