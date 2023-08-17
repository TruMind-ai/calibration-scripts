class CalibratorState:
    def __init__(self, llm_name, rating_log, instance_name) -> None:
        self.llm_name = llm_name
        self.rating_log = rating_log
        self.instance_name = instance_name
        self.rating_queue
