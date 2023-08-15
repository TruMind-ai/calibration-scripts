# TODO: separate files for handling leadership/calibration use cases
# A simple server that receives prompts as inputs to a 'POST' endpoint and
# returns a response from the chatbot.
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from utils.utils import *
from pymongo.collection import Collection
from bson.objectid import ObjectId
from fastapi.staticfiles import StaticFiles


load_dotenv('.env-db')
load_dotenv('.env-controller')

CUR_DIMENSION = os.getenv('CURRENT_DIMENSION')

app = FastAPI()
app.mount("/calibrations/get-startup-script", StaticFiles(directory="startup-scripts"), name="static")

# TODO: only allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


db = get_database()

collection_name_f='queries/{llm_name}/{dimension}'

# initialize internal dict of ratings
ratings_queue = {}

class GetBatchParams(BaseModel):
    '''
    Parameters for calibration.
    '''
    n_queries: int
    llm_name: str

class GetBatchResponse(BaseModel):
    '''
    Response for calibration.
    '''
    queries: list
    collection_name: str

def update_queries_to_processing_status(queries: list,  collection: Collection):
    if 'reference' in collection.name:
        print("Not allowed to modify reference collection!")
        return
    for query in queries:
        try:
            collection.update_one({'_id': query['_id']}, {'$set': {'rating': '0'}})
        except Exception as e:
            print('Error updating query to processing status!')
            print(e)
            break
def revert_query_status(queries:list, collection: Collection):
    if 'reference' in collection.name:
        print("Not allowed to modify reference collection!")
        return
    for query in queries:
        try:
            collection.update_one({'_id': query['_id']}, {'$set': {'rating': '-1'}})
        except Exception as e:
            print('Error updating query to ready status!')
            print(e)
            break


@app.post('/calibrations/get-batch', response_model=GetBatchResponse)
async def chat(request: GetBatchParams, background_tasks: BackgroundTasks):
    '''
    Get a batch of n calibrations to perform.
    Returns a list of tuples [(prefix_index, prompt_index, sample_index)]
    Also returns the name of the collection to save into.
    '''
    queries = []
    coll = db[collection_name_f.format(dimension=CUR_DIMENSION, llm_name=request.llm_name)]
    print(coll.name)
    if request.llm_name not in ratings_queue or len(ratings_queue[request.llm_name]) == 0:
        ratings_queue[request.llm_name] = list(coll.find({'rating': -1}))
        ratings_queue[request.llm_name].sort(key=lambda x: -1*x['num_tries'])

    for _ in range(request.n_queries):
        # get the next query
        try:
            query = ratings_queue[request.llm_name].pop()
            query = {i: str(query[i]) if isinstance(query[i], ObjectId) else query[i] for i in query}
            # add it to the list of queries to return
            queries.append(query)
        except IndexError:
            print('No more queries to rate!')
            break
    
    background_tasks.add_task(update_queries_to_processing_status, queries, coll)
    # return the sample id
    resp = GetBatchResponse(queries=queries, collection_name=coll.name)
    return resp

@app.post('/calibrations/cleanup')
async def clean_up(request: GetBatchResponse, background_tasks: BackgroundTasks):
    '''
    Clean up when calibration runner process fails
    '''
    coll = db[request.collection_name]
    background_tasks.add_task(revert_query_status, request.queries, coll)
    return {'status': 'reverting queries to ready status...'}