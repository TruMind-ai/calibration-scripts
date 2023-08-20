from bson import ObjectId
import vllm
import json
import uuid
import time
import asyncio
class QueryBatch: 
    def __init__(self, query_list: list, worker_id: str, llm_name: str, dimension: str) -> None:
        self.query_list = query_list
        self.worker_id = worker_id
        self.llm_name = llm_name
        self.dimension = dimension
    @staticmethod
    def from_dict(raw_batch: dict):
        res = QueryBatch(query_list=raw_batch['query_list'], worker_id=raw_batch['worker_id'], 
                     llm_name=raw_batch['llm_name'], dimension=raw_batch['dimension'])
        res.query_list = [Query.from_dict(q) for q in res.query_list]
        return res
class Query:
    def __init__(self, _id: ObjectId, prefix_index: int, prompt_index: int , sample_index: int , num_tries: int = 0, latency: float = -1, rating: int = -1) -> None:
        self._id = _id
        self.prefix_index = prefix_index
        self.sample_index = sample_index
        self.num_tries = num_tries
        self.latency = latency
        self.rating = rating
    
    def from_dict(raw_query: dict):
        res = Query(_id=raw_query['_id'],
        prefix_index=raw_query['prefix_index'],
        prompt_index=raw_query['prompt_index'],
        ample_index=raw_query['sample_index'],
        num_tries=raw_query['num_tries'],
        latency=raw_query['latency'],
        rating=raw_query['rating'])
        return res
class WorkerInfo:
    '''
    Stores info about the worker related to server-side, such as worker 
    ID and resource availability. Model is shared between worker and orchestrator
    '''
    def __init__(self, worker_id: str, ip_address: str = "", compute_units: int = 1):
        self.worker_id = worker_id
        self.ip_address = ip_address 
        self.compute_units = compute_units
    def to_json(self):
        self_dict = {
            "worker_id": self.worker_id,
            "ip_address": self.ip_address,
            "compute_units": self.compute_units
        }
        
        return json.dumps(self_dict)
    
class WorkerState:

    def __init__(self, worker_id:str, llm:vllm.LLM=None, sampling_params:vllm.SamplingParams=None) -> None:
        self.worker_id = worker_id
        self.llm = llm
        self.sampling_params = sampling_params
    
