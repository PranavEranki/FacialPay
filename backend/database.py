from pymongo import MongoClient
from config import config



client = MongoClient(config['db']['url'])


db = client[config['db']['name']]

users = db.users
tokens = db.tokens
transactions = db.transactions
faces = db.faces