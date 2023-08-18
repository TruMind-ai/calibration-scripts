docker container prune -f
docker run --name inference --gpus '"device=0"' -p 8000:80 -i -t -d -v vllm:/mnt/inference --shm-size=16g nvcr.io/nvidia/pytorch:22.12-py3
until [ "`docker inspect -f {{.State.Running}} inference`"=="true" ]; do
    sleep 0.1;
done;
docker exec -i -t -d -w /mnt/inference/calibration-scripts inference /bin/bash -c "git pull && source env/bin/activate && python run_calibrations.py --llm_name baichuan-inc/Baichuan-13B-Base --gpus 1 --batch_size 512"