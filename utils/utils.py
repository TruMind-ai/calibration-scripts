from pymongo.database import Database
import os
from pymongo import MongoClient
import re
from src.constants import *


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


def extract_integer(text: str):
    res = -1
    int_pat = r'\d{1,2}'
    try:
        res = int(re.findall(int_pat, text)[0])
    except Exception as e:
        try:
            res = EMOJI_TO_INT[re.findall(capture_emojis_pattern, text)[
                0].encode('unicode_escape').decode()]
        except Exception as f:
            print(text)

    return res
