from pymongo.database import Database
import os
from pymongo import MongoClient
import re
from .constants import *


def get_database(name: str = "dimension_creation") -> Database:
    '''
    This function returns associated MongoDB database 
    for calibrations
    '''
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = os.getenv('CONNECTION_STRING')
    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)
    # return database
    return client[name]

