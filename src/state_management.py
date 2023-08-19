from bson import ObjectId
import vllm
from pydantic import BaseModel

class QueryBatch(BaseModel):
    query_list: list
    worker_id: str
    llm_name: str
    dimension: str
    
class Query(BaseModel):
    _id: ObjectId
    prefix_index: int
    prompt_index: int 
    sample_index: int 
    num_tries: int 
    total_seconds: float 
    rating: int 
        
class WorkerInfo(BaseModel):
    '''
    Stores info about the worker related to server-side, such as worker 
    ID and resource availability. Model is shared between worker and orchestrator
    '''
    worker_id: str
    ip_address: str = ""
    # number of A100 80GB Cards this worker has
    compute_units: int = 1
    
class WorkerState:

    def __init__(self, worker_id:str, llm:vllm.LLM=None, sampling_params:vllm.SamplingParams=None) -> None:
        self.worker_id = worker_id
        self.llm = llm
        self.sampling_params = sampling_params
    