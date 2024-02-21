from vllm import LLM

print("TESTING MISTRAL 7B...")
llm = LLM(model="mistralai/Mistral-7B-Instruct-v0.2",
          trust_remote_code=True,  download_dir='/dev/shm/',)
