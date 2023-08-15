from utils.utils import *
from dotenv import load_dotenv
load_dotenv('.env-db')
db = get_database()
print(db.list_database_names)
