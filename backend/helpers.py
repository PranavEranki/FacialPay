import cv2
from config import config
import base64, random, os

def encodeImage(img):
	tmp_file = str(random.randint(1, 1000)) + '_' + str(random.randint(1, 1000)) + '.jpg'
	cv2.imwrite(tmp_file, img)
	tmp_f = open(tmp_file).read()
	imageString = 'data:image/jpg;base64,' + base64.encodestring(tmp_f)
	os.remove(tmp_file)
	return imageString

def drawBox(img, coords, color):
	cv2.rectangle(img, (coords[0], coords[1]), (coords[2], coords[3]), tuple(color), config['detection_params']['face']['box_thickness'])
			