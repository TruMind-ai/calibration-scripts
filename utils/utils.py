from pymongo import MongoClient
import os

all_scales = ['contrast', 'authority', 'consensus', 'consistency', 'scarcity', 'unity', 'liking', 'reciprocity']

def get_database() -> MongoClient:
    '''
    This function returns associated MongoDB database 
    for calibrations
    '''
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = os.getenv('CONNECTION_STRING')
    DB_NAME = os.getenv('CALIBRATIONS_DB')
    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)
    # return database
    return client[DB_NAME]
