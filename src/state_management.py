from bson import ObjectId
import vllm

class QueryBatch:
    def __init__(self,query_list: list, worker_id: str, llm_name: str, dimension: str) -> None:
        self.query_list = query_list
        self.worker_id = worker_id
        self.llm_name = llm_name
        self.dimension = dimension
    
class Query:
    def __init__(self, _id: ObjectId, prefix_index: int, prompt_index: int, sample_index: int, num_tries: int, total_seconds: float, rating: int) -> None:
        self._id = _id
        self.prefix_index = prefix_index
        self.prompt_index = prompt_index
        self.sample_index = sample_index
        self.num_tries = num_tries
        self.total_seconds = total_seconds
        self.rating = rating
        
class WorkerInfo:
    '''
    Stores info about the worker related to server-side, such as worker 
    ID and resource availability. Model is shared between worker and orchestrator
    '''
    def __init__(self, worker_id: str, ip_address: str = "", compute_units: int = 1):
        self.worker_id = worker_id
        self.ip_address = ip_address 
        self.compute_units = compute_units
    
class WorkerState:

    def __init__(self, worker_id:str, llm:vllm.LLM=None, sampling_params:vllm.SamplingParams=None) -> None:
        self.worker_id = worker_id
        self.llm = llm
        self.sampling_params = sampling_params
    