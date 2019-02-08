from database import *
import datetime, os
import json, cv2, hashlib
from config import config
from bson.objectid import ObjectId

def addTransaction(user, token, amount):
	inserted_id = transactions.insert_one({'user_id': str(user['_id']), 'token': str(token), 'amount': amount, 'created': datetime.datetime.now()}).inserted_id
	user['balance'] -= amount
	users.update_one({'_id': ObjectId(user['_id'])}, {'$set': user})

	return inserted_id, True

def addTransactionSplit(user_list, token, amount):
	average_amount = float(amount) / len(user_list)

	inserted_ids = []
	for user in user_list:
		inserted_id = transactions.insert_one({'user_id': str(user['_id']), 'token': str(token), 'amount': average_amount, 'created': datetime.datetime.now(), 'split': True}).inserted_id
		user['balance'] -= average_amount
		users.update_one({'_id': ObjectId(user['_id'])}, {'$set': user})
		inserted_ids.append(inserted_id)

	return inserted_ids, True
