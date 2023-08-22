import time
from time import sleep
import requests
from utils.utils import get_database, extract_integer
from src.state_management import WorkerInfo, QueryBatch, WorkerState
from vllm import LLM, SamplingParams
import uuid
from src.constants import LLM_TEMPLATES_V2
from dotenv import load_dotenv
import json 
load_dotenv('.env-db')



# ORCHESTRATOR_URL=os.getenv('ORCHESTRATOR_URL')

ORCHESTRATOR_URL = "http://20.228.162.220:8000"
# instantiate worker info
worker_info = WorkerInfo(worker_id=str(uuid.uuid1()), ip_address='', compute_units=1)

# initialize state
worker_state = WorkerState(worker_info.worker_id)

# set sampling params
worker_state.sampling_params = SamplingParams(temperature=1 ,max_tokens=3)

#initialize databse
db = get_database()

# initialize LLM templates
LLM_TEMPLATES = LLM_TEMPLATES_V2


def register_worker_with_orchestrator() -> bool:
    headers = {
        'Content-Type': 'application/json',
    }
    data = json.dumps(vars(worker_info))
    res = requests.post(f'{ORCHESTRATOR_URL}/calibrations/register-worker', headers=headers, data=data)
    return res.status_code == 200
        
def format_queries_for_vllm(query_batch: QueryBatch):
    print("formatting queries for vllm...")
    
    prefixes = {prefix['prefix_index']
        : prefix for prefix in list(db[f'prefixes'].find({}))}
    prompts = {prompt['prompt_index']
        : prompt for prompt in list(db[f'core_prompts/{query_batch.dimension}'].find({}))}
    samples = {sample['sample_index']
        : sample for sample in list(db[f'samples/{query_batch.dimension}'].find({}))}
    
    prompt_dict = {}
    for query in query_batch.query_list:
        prefix = prefixes[query.prefix_index]['prefix']
        prompt = prompts[query.prompt_index]['combined_prompt']
        sample = samples[query.sample_index]['sample']
        combined = f"{prefix}\n{prompt}\nSample:\n{sample}"
        prompt_dict[LLM_TEMPLATES[query_batch.llm_name].format(
            prompt=combined)] = query.id
    print(len(prompt_dict),"queries in batch")
    
    return prompt_dict
        

def get_query_batch_from_controller() -> QueryBatch:
    print("getting query batch from controller...")
    url = f'{ORCHESTRATOR_URL}/calibrations/get-new-batch/{worker_info.worker_id}'
    headers = {
        'Content-Type': 'application/json',
    }
    res = requests.get(url, headers=headers)
    print(res)
    res = res.json()
    qb = QueryBatch.from_dict(res)
    print(len(qb.query_list), "Queries in batch")
    if worker_state.llm == None: #or worker_state.llm != qb.llm_name:
        # torch.cuda.empty_cache()
        worker_state.llm = LLM(model=qb.llm_name, trust_remote_code=True, download_dir='./models-weights', gpu_memory_utilization=0.98, swap_space=4, tensor_parallel_size=1,  max_num_batched_tokens=3800)
    return qb
    

def upload_query_batch(query_batch: QueryBatch) -> bool:
    print("uploading query batch...")
    headers = {
        'Content-Type': 'application/json',
    }
    data = json.dumps(query_batch.to_dict())
    res = requests.post(f"{ORCHESTRATOR_URL}/calibration/upload-queries", headers=headers, data=data)
    return res.status_code == 200

def do_one_batch() -> None:
    # get ratings from controller 
    current_query_batch = get_query_batch_from_controller()
    batch_start = time.time()
    if not current_query_batch or not current_query_batch.query_list:
        print("No more queries to rate!!! Sleeping for 30 seconds")
        sleep(30)
        return

    # Format query in LLM prompt style
    cur_prompts_dict = format_queries_for_vllm(current_query_batch)
    cur_prompts = list(cur_prompts_dict.keys())
    # call "generate" on the list
    ratings = {}
    outputs = worker_state.llm.generate(cur_prompts, worker_state.sampling_params, use_tqdm=True)
    for i, output in enumerate(outputs):
        query_id = cur_prompts_dict[output.prompt]
        ratings[query_id] = extract_integer(output.outputs[0].text)
        print('output #', i, 'rating:', ratings[query_id])

    print(f"Sample Ratings: {list(ratings.values())[-10:]}")

    # update queries with ratings, collect timing stats
    for _, query in enumerate(current_query_batch.query_list):
        query.rating = -1
        if query.id in ratings:
            query.rating = ratings[query.id]
        else:
            print("Error: query id not in ratings!")
        query.num_tries += 1
        avg_query_time = (time.time()-batch_start)/len(current_query_batch.query_list)
        if query.latency == -1:
            query.latency = avg_query_time
        else:
            query.latency = ((query.num_tries-1)*query.latency + avg_query_time)/query.num_tries
            
    # upload batch
    upload_query_batch(current_query_batch)
    
def main():
    register_worker_with_orchestrator()
    while True:
        try:
            do_one_batch()
        except Exception as e:
            print("ERRORS - trying to re-register...")
            print(str(e))
            if not register_worker_with_orchestrator():
                print("ERROR RE-REGISTERING")
            print("error doing batch... sleeping for 30s")
            sleep(30)
                    
if __name__ == '__main__': 
    main()


