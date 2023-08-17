from pymongo import MongoClient
from pymongo.database import Database
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os

all_scales = ['contrast', 'authority', 'consensus',
              'consistency', 'scarcity', 'unity', 'liking', 'reciprocity']


def get_database() -> Database:
    """_summary_
    Gets the database 'CALIBRATIONS_DB' from the corresponding environment variable.
    Returns:
        Database: 
    """
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = os.getenv('CONNECTION_STRING')
    DB_NAME = os.getenv('CALIBRATIONS_DB')
    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING)
    # return database
    return client[DB_NAME]


def get_aDatabase() -> AsyncIOMotorDatabase:
    """_summary_
    Gets the database 'CALIBRATIONS_DB' from the corresponding environment variable, with the motor driver.
    Returns:
        AsyncIOMotorDatabase
    """
    CONNECTION_STRING = os.getenv('CONNECTION_STRING')
    DB_NAME = os.getenv('CALIBRATIONS_DB')
    client = AsyncIOMotorClient(CONNECTION_STRING)
    return client[DB_NAME]


def get_aClient() -> AsyncIOMotorClient:
    CONNECTION_STRING = os.getenv('CONNECTION_STRING')
    client = AsyncIOMotorClient(CONNECTION_STRING)
    return client
