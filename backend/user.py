from database import *
import datetime, os
import json, cv2, hashlib
from config import config
from bson.objectid import ObjectId
import hashlib


def getUserBalance(username, password):
	sha_1 = hashlib.sha1()
	sha_1.update(password)
	password = sha_1.hexdigest()

	userObj = users.find_one({"username": username, "password": password})
	if userObj is None:
		return "No such user found", False

	return userObj['balance'], True

def createUser(name, start_balance, username, password, images):
	if not name.replace(" ", "").isalnum():
		return 'Your name is invalid', False

	if not username.replace("_", "").isalnum():
		return 'Your username can only contain letters, numbers and underscores', False

	if len(password) < 6:
		return 'Your password must be at least 6 characters long', False

	usernameUser = users.find_one({'username': username})
	if usernameUser is not None:
		return 'Your desired username is not available', False
	sha_1 = hashlib.sha1()
	sha_1.update(password)
	password = sha_1.hexdigest()

	inserted_id = users.insert_one({'name': name, 'balance': float(start_balance), 'created': datetime.datetime.now(), 'username': username, 'password': password}).inserted_id

	if not os.path.exists(os.path.join(config['storage']['faces'], str(inserted_id))):
		os.makedirs(os.path.join(config['storage']['faces'], str(inserted_id)))

	count = 0
	for image in images:
		cv2.imwrite(os.path.join(config['storage']['faces'], str(inserted_id), str(count) + '.jpg'), image)
		count += 1

	return inserted_id, True

def verifyAccessToken(access_token):
	if not ObjectId.is_valid(access_token):
		return 'Invalid access token', False

	token = tokens.find_one({'_id': ObjectId(access_token)})
	if token is None:
		return 'Invalid access token', False

	return None, True

def getUserCredentialsById(uid):
	if not ObjectId.is_valid(uid):
		return 'Invalid ID', False

	user = users.find_one({'_id': ObjectId(uid)})
	if user is None:
		print("User with id " + uid + "was not found")
		return 'No user found', False

	return user, True

