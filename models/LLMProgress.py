class LLMProgress():
    def __init__(self, llm_name: str, dimension_name: str, dimension_id: str, completed: int, unfinished: int, total: int) -> None:
        self.llm_name = llm_name
        self.dimension_name = dimension_name
        self.dimension_id = dimension_id
        # number of completed ratings
        self.completed = completed
        # number of ratings that haven't been tried
        self.unfinished = unfinished
        # number of total ratings
        self.total = total
