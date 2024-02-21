from models import DimensionAsset
import time
from time import sleep
import requests
from utils.utils import get_database, extract_integer, calculate_num_shard
from src.state_management import QueryBatch, WorkerState
from vllm import LLM, SamplingParams
from dotenv import load_dotenv
import json
load_dotenv()

generic_suffix = "Output only the integer associated with the stage, step or sub-step level such that only a single integer between 1-90 is outputted, where Stage 7 Step 1 is integer 1, and Stage 16 Step 6 is integer 90, and all stages and steps in between follow a sequential order from 1-90. For the output to this prompt, ONLY OUTPUT the integer associated to the stage and step/sub-step the experts have decided on."

# ORCHESTRATOR_URL=os.getenv('ORCHESTRATOR_URL')

ORCHESTRATOR_URL = "http://20.228.162.220:8000"

# initialize state
worker_state = WorkerState(worker_id="")

# set sampling params
worker_state.sampling_params = SamplingParams(
    temperature=1, max_tokens=4)

# initialize database
db = get_database("dimension_creation")

# initialize LLM templates
# LLM_TEMPLATES = LLM_TEMPLATES_V2


# def register_worker_with_orchestrator() -> bool:
#     headers = {
#         'Content-Type': 'application/json',
#     }
#     data = json.dumps(vars(worker_info))
#     res = requests.post(
#         f'{ORCHESTRATOR_URL}/calibrations/register-worker', headers=headers, data=data)
#     return res.status_code == 200

suffix = "Output only the integer associated with the stage, step or sub-step level such that only a single integer between 1-90 is outputted, where Stage 7 Step 1 is integer 1, and Stage 16 Step 6 is integer 90, and all stages and steps in between follow a sequential order from 1-90. For the output to this prompt, ONLY OUTPUT the integer associated to the stage and step/sub-step the experts have decided on."


def format_queries_for_vllm(query_batch: QueryBatch):
    print("formatting queries for vllm...")
    qb = query_batch
    assets = DimensionAsset.from_list(
        list(db[f'{qb.dimension_id}/assets'].find({})))
    assets_dict = {a.index: a for a in assets}

    # prefixes = {prefix['prefix_index']: prefix for prefix in list(db[f'prefixes'].find({}))}

    prompt_dict = {}
    for dim_rating in query_batch.query_list:
        prefix = assets_dict[dim_rating.prefix_index].text if dim_rating.prefix_index in assets_dict else ""
        prompt = assets_dict[dim_rating.prompt_index].text
        sample = assets_dict[dim_rating.sample_index].text
        combined = f"{prefix}{prompt}\nSample:\n{sample}{suffix}"
        # prompt_dict[LLM_TEMPLATES[query_batch.llm_name].format(
        # prompt=combined)] = query.id
        prompt_dict[combined] = dim_rating.id
    print(len(prompt_dict), "queries in batch")

    return prompt_dict


def get_query_batch_from_controller() -> QueryBatch:
    print("getting query batch from controller...")
    url = f'{ORCHESTRATOR_URL}/calibration/get-new-batch'
    headers = {
        'Content-Type': 'application/json',
    }
    res = requests.get(url, headers=headers)
    print(res)
    res = res.json()
    qb = QueryBatch(**res)
    print(len(qb.query_list), "Queries in batch")
    if worker_state.llm == None:  # or worker_state.llm != qb.llm_name:
        # torch.cuda.empty_cache()
        worker_state.llm = LLM(model=qb.llm_name, trust_remote_code=True,  download_dir='/dev/shm/',
                               gpu_memory_utilization=0.98, tensor_parallel_size=calculate_num_shard(llm=qb.llm_name))
    return qb


def upload_query_batch(query_batch: QueryBatch) -> bool:
    print("uploading query batch...")
    headers = {
        'Content-Type': 'application/json',
    }
    data = json.dumps(query_batch.to_dict())
    res = requests.post(
        f"{ORCHESTRATOR_URL}/calibration/upload-queries", headers=headers, data=data)
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
    outputs = worker_state.llm.generate(
        cur_prompts, worker_state.sampling_params, use_tqdm=True)
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
        avg_query_time = (time.time()-batch_start) / \
            len(current_query_batch.query_list)
        if query.latency == -1:
            query.latency = avg_query_time
        else:
            query.latency = ((query.num_tries-1)*query.latency +
                             avg_query_time)/query.num_tries

    # upload batch
    upload_query_batch(current_query_batch)


def main():
    # register_worker_with_orchestrator()
    while True:
        try:
            do_one_batch()
        except Exception as e:
            print("ERROR - trying to re-do batch...")
            print(str(e))
            # traceback.print_exc()
            # if not register_worker_with_orchestrator():
            # print("ERROR RE-REGISTERING")
            # print("error doing batch... sleeping for 30s")
            sleep(30)


if __name__ == '__main__':
    main()
