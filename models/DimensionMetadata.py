from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum
import time
from .utils import PyObjectId
from typing import List, Dict, Any, Literal, Optional


class DimensionTask(BaseModel):
    name: Literal["asset_generation",  # for the Daemon
                  "rating_collection",
                  "calibration"] = "asset_generation"

    # list of arguments to give to the daemon (e.g. which type of asset to generate)
    arguments: Dict[str, Any] = {}

    status: Literal["not_started", "in_progress",
                    "done", "error"] = "not_started"

    timestamp: int = Field(default_factory=lambda: int(time.time()))

    messages: List[str] = []


class DimensionCreationStatus(Enum):
    '''Status of the Dimension (which task should be in progress)

    :param Enum: _description_
    :type Enum: _type_
    '''
    # created, but prompt/sample meta-prompts not defined/created
    NOT_STARTED = "not_started"
    # prompts/samples began creation
    PROMPT_SAMPLE_CREATION = "prompt_sample_creation"
    # Configuring LLMs, double-checking prompts/samples before turning on LLMS
    RATING_CONFIGURATION = "rating_configuration"
    # Rating process in full blast
    IN_PROGRESS = "in_progress"
    # Rating process finished/user stops early
    FINISHED = "finished"
    FAILED = "failed"


class DimensionMetadata(BaseModel):

    id: PyObjectId = Field(alias="_id", default=None)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    owner: str
    llms: List[str] = []
    dimension_name: str
    tasks: List[DimensionTask] = []
    # status: DimensionCreationStatus = DimensionCreationStatus.NOT_STARTED
    max_tries: int = 1

    @staticmethod
    def from_list(dim_metadata_list: List[Dict[str, Any]]) -> List[DimensionMetadata]:
        res = []
        for dim_meta in dim_metadata_list:
            res.append(DimensionMetadata(**dim_meta))
        return res

    # gets the current running task based on `tasks`
    def get_current_tasks(self) -> List[DimensionTask]:
        return sorted(self.tasks, key=lambda t: -t.timestamp)

    def mark_as_finished_and_add_task(self, new_task: DimensionTask, old_task: Optional[DimensionTask] = None):
        '''The old_task has to match in name and timestamp

        :param old_task: _description_
        :type old_task: DimensionTask
        :param new_task: _description_
        :type new_task: DimensionTask
        '''
        if old_task:
            for i, t in enumerate(self.tasks):
                if t.name == old_task.name and t.timestamp == old_task.timestamp:
                    t.status = "done"
        self.tasks.append(new_task)
