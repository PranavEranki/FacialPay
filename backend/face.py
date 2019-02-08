import cv2, dlib, os
from config import config
import time, numpy as np
import glob
from threading import Lock
import user
from scipy import spatial

face_detector = dlib.get_frontal_face_detector()

shape_predictor = dlib.shape_predictor(str(config['models']['face']['landmark']))
face_recognition_model = dlib.face_recognition_model_v1(str(config['models']['face']['recognition']))

face_recognition_data = {'names': [], 'kdtree': None, 'ordered_names': []}
face_recognition_lock = Lock()


def get_face_encodings(image):
	detected_faces = face_detector(image, 1)
	
	face_shapes = [(shape_predictor(image, x), x) for x in detected_faces]
	return [(np.array(face_recognition_model.compute_face_descriptor(image, x[0], 4)), x) for x in face_shapes]

def match_faces(img):
	faces_list = get_face_encodings(img)

	recognized = []
	distances = []

	face_recognition_lock.acquire()

	if face_recognition_data['kdtree'] is None:
		face_recognition_lock.release()
		return []

	for x in faces_list:
		distance, index = face_recognition_data['kdtree'].query(x[0])
		print(index)
		print(face_recognition_data['names'])
		distances.append(distances)
		if distance < config['detection_params']['face']['threshold']:
			recognized.append(face_recognition_data['ordered_names'][index])
		else:
			recognized.append('')


	face_recognition_lock.release()

	for i in range(len(faces_list)):
		x = faces_list[i]
		nom = recognized[i]

		for j in range(i + 1, len(faces_list)):
			nom2 = recognized[j]
			if nom2 == nom:
				if distances[i] > distances[j]:
					recognized[i] = ''
				else:
					recognized[j] = ''

	face_objects = []
	for i in range(len(faces_list)):
		x = faces_list[i]
		det = x[1][1]
		xmin, xmax, ymin, ymax = (det.left(), det.right(), det.top(), det.bottom())
		if recognized[i] != '':
			face_objects.append({'id': recognized[i], 'img': img[ymin:ymax, xmin:xmax]})

	return face_objects

def getUserFromImage(img):
	face_objects = match_faces(img)
	if len(face_objects) < 1:
		return "Sorry, no recognized face.", False

	rec_id = face_objects[0]['id']
	retval, success = user.getUserCredentialsById(rec_id)

	if not success:
		return retval, False

	return retval, True

def getUsersFromImage(img):
	face_objects = match_faces(img)
	if len(face_objects) < 1:
		return "Sorry, no recognized face.", False

	recognized = []
	
	for face_object in face_objects:
		rec_id = face_object['id']
		retval, success = user.getUserCredentialsById(rec_id)
		if success:
			recognized.append(retval)
		else:
			recognized.append(None)

	return recognized, True


def get_faces(frdata, frlock):
	while True:
		print("Loading faces...")
		faces = {}

		names = filter(lambda x: os.path.isdir(os.path.join(config['storage']['faces'], x)), os.listdir(config['storage']['faces']))

		if len(names) == len(frdata['names']):
			time.sleep(2)
			continue

		size = len(glob.glob(os.path.join(config['storage']['faces'], '*/*.jpg'))) + len(glob.glob(os.path.join(config['storage']['faces'], '*/*.png')))
		data = np.zeros((size, 128))

		count = 0

		ordered_names = []
		for name in names:
			images = filter(lambda x: x.endswith('.png') or x.endswith('.jpg'), os.listdir(os.path.join(config['storage']['faces'], name)))

			for image_name in images:
				image = cv2.imread(os.path.join(config['storage']['faces'], name, image_name))
				face_encodings = get_face_encodings(image)

				if len(face_encodings) > 0:
					data[count, :] = face_encodings[0][0]
					count += 1
					ordered_names.append(name)

		frlock.acquire()
		frdata['names'] = names
		frdata['kdtree'] = spatial.KDTree(data)
		frdata['ordered_names'] = ordered_names

		print("Loaded faces")
		frlock.release()

		time.sleep(2)

def start_get_faces():
	get_faces(face_recognition_data, face_recognition_lock)
