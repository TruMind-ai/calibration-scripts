class InferenceOrchestrator:
    def __init__(self, db, collection_name_) -> None:
        self.db = get_database()
        self.collection_name_f = 'queries/{llm_name}/{dimension}'
