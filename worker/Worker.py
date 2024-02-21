
import code
import json
from time import sleep
import time
import requests
from models import DimensionAsset, QueryBatch
from utils import calculate_num_shard
from utils.completions import extract_integer, format_queries_for_vllm
from utils.database import get_database
from vllm import LLM, SamplingParams
import vllm


class Worker:
    def __init__(self, worker_id: str, llm: vllm.LLM = None, sampling_params: vllm.SamplingParams = None) -> None:
        self.worker_id = worker_id
        self.llm = llm
        self.sampling_params = sampling_params
        self.db = get_database("dimension_creation")
        self.orchestrator_url = "http://20.228.162.220:8000"

    def get_query_batch_from_controller(self) -> QueryBatch:
        print("getting query batch from controller...")
        url = f'{self.orchestrator_url}/calibration/get-new-batch'
        headers = {
            'Content-Type': 'application/json',
        }
        res = requests.get(url, headers=headers)
        print(res)
        res = res.json()
        qb = QueryBatch(**res)
        print(len(qb.query_list), "Queries in batch")
        if not self.llm:  # or worker.llm != qb.llm_name:
            # torch.cuda.empty_cache()
            self.llm = LLM(model=qb.llm_name, trust_remote_code=True,  download_dir='/dev/shm/',
                           gpu_memory_utilization=0.95, tensor_parallel_size=calculate_num_shard(llm=qb.llm_name),
                           max_model_len=8000)
        return qb

    def upload_query_batch(self, query_batch: QueryBatch) -> bool:
        print("uploading query batch...")
        headers = {
            'Content-Type': 'application/json',
        }
        data = json.dumps(query_batch.model_dump())
        res = requests.post(
            f"{self.orchestrator_url}/calibration/upload-queries", headers=headers, data=data)
        return res.status_code == 200

    def do_one_batch(self, num_max_queries=-1, debug=False) -> None:
        # get ratings from controller
        current_query_batch = self.get_query_batch_from_controller()
        if num_max_queries > 0:
            current_query_batch.query_list = current_query_batch.query_list[-num_max_queries:]
        batch_start = time.time()
        if not current_query_batch or not current_query_batch.query_list:
            print("No more queries to rate!!! Sleeping for 30 seconds")
            sleep(30)
            return

        # Format query in LLM prompt style
        if not self.assets:
            self.assets = DimensionAsset.from_list(
                list(self.db[f'{current_query_batch.dimension_id}/assets'].find({})))
        cur_prompts_dict = format_queries_for_vllm(
            current_query_batch, self.assets, self.llm.get_tokenizer())
        cur_prompts = list(cur_prompts_dict.keys())
        # call "generate" on the list
        ratings = {}

        outputs = self.llm.generate(
            cur_prompts, self.sampling_params, use_tqdm=True)
        for i, output in enumerate(outputs):
            query_id = str(cur_prompts_dict[output.prompt])
            ratings[query_id] = extract_integer(output.outputs[0].text)
            print('output #', i, 'rating:', ratings[query_id])

        print(f"Sample Ratings: {list(ratings.values())[-10:]}")

        # update queries with ratings, collect timing stats
        for _, query in enumerate(current_query_batch.query_list):
            query.rating = -1
            query_id = str(query.id)
            if query_id in ratings:
                query.rating = ratings[query_id]
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
        if debug:
            code.InteractiveConsole(locals=globals())
        # upload batch
        self.upload_query_batch(current_query_batch)

    def start_worker(self, num_max_queries=-1, debug=False):
        while True:
            try:
                self.do_one_batch(num_max_queries=num_max_queries, debug=debug)
            except Exception as e:
                print("ERROR - trying to re-do batch...")
                print(e.with_traceback())
                print(str(e))
                # traceback.print_exc()
                # if not register_worker_with_orchestrator():
                # print("ERROR RE-REGISTERING")
                # print("error doing batch... sleeping for 30s")
                sleep(60)
