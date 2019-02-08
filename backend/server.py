from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
import json
import dlib
import cv2
import random
import os
import time
import flask
from flask_cors import CORS
import user, vision
from config import config
import glob
from face import *
from threading import Thread, Lock
import transactions
import helpers
from base64 import decodestring
import base64

from OpenSSL import SSL
context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('server.key')
context.use_certificate_file('server.crt')


face_detector = dlib.get_frontal_face_detector()

ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
CORS(app)




@app.route('/')
def hello_world():
	return 'Relax Taus, I\'m still alive'

@app.route('/user/balance', methods=['POST'])
def getBalance():
	params = ['username', 'password']
	data = request.form
	for p in params:
		if p not in data:
			return json.dumps({'error': 'Required params missing', 'success': False}), 200

	ret, success = user.getUserBalance(data['username'], data['password'])
	if not success:
		return json.dumps({'error': ret, 'success': False})
	else:
		return json.dumps({'success': True, 'balance': ret})

	
@app.route('/user/signup_base64', methods=['POST'])
def signUpBase64():
	params = ['name', 'starting_balance', 'username', 'password', 'image']

	data = request.form

	for p in params:
		if p not in data:
			return json.dumps({'error': 'Required params missing', 'success': False}), 200

	try:
		float(data['starting_balance'])
	except ValueError:
		return json.dumps({'error': 'Invalid balance', 'success': False}), 400
		
	image_string = data['image']
	tmp_file = str(random.randint(1, 1000)) + '_' + str(random.randint(1, 1000)) + '.jpg'
	fh = open(tmp_file, "wb")
	fh.write(str(image_string.split(",")[1].decode('base64')))
	fh.close()

	images = []
	
	img = cv2.imread(tmp_file)
	os.remove(tmp_file)

	if img is None:
		return json.dumps({'error': 'Invalid file uploaded', 'success': False}), 200

	faces = face_detector(img, 1)

	if len(faces) < 1:
		return json.dumps({'error': 'Please upload different images; we cannot detect a face in at least one image', 'success': False}), 200

	if len(faces) > 1:
		return json.dumps({'error': 'Please upload images that only has your face in it', 'success': False}), 200

	images.append(img)

	ret, success = getUserFromImage(images[0])

	if success:
		return json.dumps({'error': 'Sorry, user already exists.'})

	ret, success = user.createUser(data['name'], data['starting_balance'], data['username'], data['password'], images)

	if not success:
		return json.dumps({'error': ret, 'success': False})
	else:
		return json.dumps({'success': True})



@app.route('/user/signup', methods=['POST'])
def signUp():
	params = ['name', 'starting_balance', 'username', 'password']

	data = request.form

	for p in params:
		if p not in data:
			return json.dumps({'error': 'Required params missing', 'success': False}), 200

	try:
		float(data['starting_balance'])
	except ValueError:
		return json.dumps({'error': 'Invalid balance', 'success': False}), 400


	files = request.files.getlist('file')

	if len(files) < 1:
		return json.dumps({'error': 'You need an image', 'success': False}), 200

	images = []
	for file in files:
		if not allowed_file(file.filename):
			return json.dumps({'error': 'You uploaded an invalid image type'})
		filename = secure_filename(file.filename)
		tmp_file = str(random.randint(1, 1000)) + '_' + str(random.randint(1, 1000)) + '.' + filename.rsplit('.', 1)[1].lower()

		file.save(tmp_file)
		img = cv2.imread(tmp_file)
		os.remove(tmp_file)

		if img is None:
			return json.dumps({'error': 'Invalid file uploaded', 'success': False}), 200

		faces = face_detector(img, 1)

		if len(faces) < 1:
			return json.dumps({'error': 'Please upload different images; we cannot detect a face in at least one image', 'success': False}), 200

		if len(faces) > 1:
			return json.dumps({'error': 'Please upload images that only has your face in it', 'success': False}), 200

		images.append(img)

	ret, success = getUserFromImage(images[0])

	if success:
		return json.dumps({'error': 'Sorry, user already exists.'})

	ret, success = user.createUser(data['name'], data['starting_balance'], data['username'], data['password'], images)

	if not success:
		return json.dumps({'error': ret, 'success': False})
	else:
		return json.dumps({'success': True})




@app.route('/pay/<amount>', methods=['POST'])
def payUsingFace(amount):
	if 'image' not in request.form:
		return json.dumps({"error": "Image missing", success: False}), 400

	image_string = request.form['image']


	access_token = request.args.get('access_token')

	ret, success = user.verifyAccessToken(access_token)
	if not success:
		return json.dumps({'error': ret, 'success': False})

	amount = float(amount)

	tmp_file = str(random.randint(1, 1000)) + '_' + str(random.randint(1, 1000)) + '.jpg'

	fh = open(tmp_file, "wb")
	fh.write(str(image_string.split(",")[1].decode('base64')))
	print(image_string.split(",")[1])
	fh.close()

	img = cv2.imread(tmp_file)

	os.remove(tmp_file)

	if img is None:
		return json.dumps({'error': 'Image could not be read', 'success': False}), 200

	faces = face_detector(img, 1)

	if len(faces) < 1:
		return json.dumps({'error': 'Sorry, we could not detect a face.', 'success': False, 'num_faces': len(faces), 'image': helpers.encodeImage(img)}), 200


	curFace = faces[0]

	# if len(faces) > 1:
	# 	for curFace in faces:
	# 		helpers.drawBox(img, [curFace.left(), curFace.top(), curFace.right(), curFace.bottom()], (0, 0, 255))
	# 	return json.dumps({'error': 'Sorry, we detected more than once face.', 'success': False, 'num_faces': len(faces), 'image': helpers.encodeImage(img)}), 200


	ret, success = getUsersFromImage(img)

	if not success:
		return json.dumps({'error': "Sorry, no face was recognized", 'success': False, 'num_faces': len(faces), 'image': helpers.encodeImage(img)})

	notRecognized = filter(lambda x: x is None, ret)
	if len(notRecognized) > 0 or len(ret) < len(faces):
		for curFaceCount in range(len(faces)):
			curFace = faces[curFaceCount]
			helpers.drawBox(img, [curFace.left(), curFace.top(), curFace.right(), curFace.bottom()], (95, 230, 232))

		return json.dumps({'error': "Sorry, not all faces were recognized", 'success': False, 'num_faces': len(faces), 'image': helpers.encodeImage(img)})

	full_names = [x['name'] for x in ret]

	ret, success = transactions.addTransactionSplit(ret, access_token, amount)

	for curFaceCount in range(len(faces)):
		curFace = faces[curFaceCount]
		helpers.drawBox(img, [curFace.left(), curFace.top(), curFace.right(), curFace.bottom()], (0, 230, 0))

	imageString = helpers.encodeImage(img)

	if not success:
		return json.dumps({'error': ret, 'success': False, 'num_faces': len(faces)})
	else:
		return json.dumps({'success': True, 'image': imageString, 'names': full_names})




@app.route('/faces/<face_id>', methods=['GET'])
def getFace(face_id):
	access_token = request.args.get('access_token')
	ret, success = user.verifyAccessToken(access_token)

	if not success:
		return json.dumps({'error': ret, 'success': False}), 400

	file_path = os.path.join(config['storage']['face_crops'], face_id + '.jpg')
	if not os.path.isfile(file_path):
		return json.dumps({'error': 'Sorry, file does not exist'}), 404

	return flask.send_file(file_path)



if __name__ == '__main__':
	Thread(target=start_get_faces, args=[]).start()
	context = ('server.crt', 'server.key')
	app.run(host='0.0.0.0', port=3000, threaded=True, ssl_context=context)
        