docker container prune -f
docker run --name inference --gpus '"device=0"' -p 8000:80 -i -t -d -v vllm:/mnt/inference --shm-size=16g nvcr.io/nvidia/pytorch:22.12-py3
docker exec -i -t -d -w /mnt/inference/calibration-scripts inference /bin/bash -c "git pull && source env/bin/activate && python run_calibrations.py --llm_name openchat/openchat_v3.1 --gpus 1 -d contrast"