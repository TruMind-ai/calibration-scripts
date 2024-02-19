import vllm
from typing import List, Dict, Any
from models import DimensionRating
from pydantic import BaseModel


class QueryBatch(BaseModel):
    query_list: List[DimensionRating]
    llm_name: str
    dimension_id: str


# class WorkerInfo:
#     '''
#     Stores info about the worker related to server-side, such as worker
#     ID and resource availability. Model is shared between worker and orchestrator
#     '''

#     def __init__(self, worker_id: str, ip_address: str = "", compute_units: int = 1):
#         self.worker_id = worker_id
#         self.ip_address = ip_address
#         self.compute_units = compute_units

#     def to_json(self):
#         self_dict = {
#             "worker_id": self.worker_id,
#             "ip_address": self.ip_address,
#             "compute_units": self.compute_units
#         }

    # return json.dumps(self_dict)


class WorkerState:

    def __init__(self, worker_id: str, llm: vllm.LLM = None, sampling_params: vllm.SamplingParams = None) -> None:
        self.worker_id = worker_id
        self.llm = llm
        self.sampling_params = sampling_params
