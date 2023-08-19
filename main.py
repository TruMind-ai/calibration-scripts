import time
from time import sleep
import requests
from utils.utils import get_database
from src.state_management import WorkerInfo, QueryBatch, Query, WorkerState
from vllm import LLM, SamplingParams
import os
from bson import ObjectId
import uuid
from src.constants import LLM_TEMPLATES_V2
from dotenv import load_dotenv

load_dotenv('.env')



ORCHESTRATOR_URL=os.getenv('ORCHESTRATOR_URL')

# instantiate worker info
worker_info = WorkerInfo()
worker_info.id = uuid.uuid1()
worker_info.ip_address = ''
worker_info.compute_units = 1

# initialize state
worker_state = WorkerState(worker_info.id)

# set sampling params
sampling_params = SamplingParams(max_tokens=2)

#initialize databse
db = get_database()

# initialize LLM templates
LLM_TEMPLATES = LLM_TEMPLATES_V2


def register_worker_with_orchestrator() -> bool:
    headers = {
        'Content-Type': 'application/json',
    }
    data = worker_info.model_dump_json()
    res = requests.post('/calibrations/register-worker', headers=headers, data=data)
    return res.status_code == 200
        
def format_queries_for_vllm(query_batch: QueryBatch):
    
    prefixes = list(db[f'prefixes'])
    prompts = list(db[f'core_prompts/{query_batch.dimension}'])
    samples = list(db[f'samples/{query_batch.dimension}'])
    
    prompt_dict = {}
    for query in query_batch.query_list:
        query['_id'] = ObjectId(query['_id'])
        prefix = prefixes[query['prefix_index']]['prefix']
        prompt = prompts[query['prompt_index']]['combined_prompt']
        sample = samples[query['sample_index']]['sample']
        combined = f"{prefix}\n{prompt}\nSample:\n{sample}"
        prompt_dict[LLM_TEMPLATES[query_batch.llm_name].format(
            prompt=combined)] = query['_id']
    return prompt_dict
        

def get_query_batch_from_controller() -> QueryBatch:
    url = f'{ORCHESTRATOR_URL}/calibrations/get-new-batch/{worker_info.id}'
    headers = {
        'Content-Type': 'application/json',
    }
    res = requests.get(url, headers=headers)
    res = res.json()
    qb = QueryBatch()
    qb.llm_name = res['llm_name']
    qb.dimension = res['dimension']
    qb.query_list = res['query_list']
    qb.worker_id = res['worker_id']
    return qb
    

def upload_query_batch(query_batch: QueryBatch) -> bool:
    headers = {
        'Content-Type': 'application/json',
    }
    data = query_batch.model_dump_json()
    res = requests.post("/calibration/upload-queries", headers=headers, data=data)
    return res.status_code == 200

def do_one_batch() -> None:
    batch_start = time.time()
    # get ratings from controller 
    current_query_batch = get_query_batch_from_controller()
    if not current_query_batch.query_list:
        print("No more queries to rate!!! Sleeping for 1 minute")
        sleep(60)

    # Format query in LLM prompt style
    cur_prompts_dict = format_queries_for_vllm(current_query_batch)
    cur_prompts = list(cur_prompts_dict.keys())
    # call "generate" on the list
    outputs = llm.generate(cur_prompts, sampling_params)
    
    # extract integer rating
    ratings = {}
    for output in outputs:
        query_id = cur_prompts_dict[output.prompt]
        text = output.outputs[0].text
        try:
            ratings[query_id] = int(text)
        except:
            try:
                ratings[query_id] = int(text[0])
            except:
                ratings[query_id] = -1

    print(f"Sample Ratings: {list(ratings.values())[-10:]}")

    # update queries with ratings, collect timing stats
    for _, query in enumerate(current_query_batch.query_list):
        query['rating'] = -1
        if query['_id'] in ratings:
            query['rating'] = ratings[query['_id']]
        else:
            print("Error: query id not in ratings!")
        query['num_tries'] += 1
        avg_query_time = (time.time()-batch_start)/len(current_query_batch.query_list)
        if query['total_seconds'] == -1:
            query['total_seconds'] = avg_query_time
        else:
            query['total_seconds'] += avg_query_time
            
    # upload batch
    upload_query_batch(current_query_batch)
    
def main():
    while True:
        do_one_batch()
                    
if __name__ == '__main__': 
    main()


