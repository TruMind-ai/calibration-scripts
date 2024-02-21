from vllm import SamplingParams
from dotenv import load_dotenv
import json

from worker.Worker import Worker
load_dotenv()


# ORCHESTRATOR_URL=os.getenv('ORCHESTRATOR_URL')


def main():
    worker = Worker(worker_id="", sampling_params=SamplingParams(
        temperature=1.2, max_tokens=5))
    worker.start_worker(10, True)


if __name__ == '__main__':
    main()
