import cognitive_face as cf
import cv2 as cv 
from json import load, dump
import sys
import thread_video


with open("faceid.json") as key_data:
    data = load(key_data)
    key = data["MSkey"]
    base_url = data["serviceUrl"]
    groupID = data["groupId"]

cf.BaseUrl.set(base_url)
cf.Key.set(key)

try:
	cf.person_group.create(groupID)
except:
	pass


def add_new(name, video):
	is_here = False
	person_id = ""
	for person in cf.person.lists(groupID):
		if person["name"] == name:
			is_here = True
			person_id = person["personId"]
	if not is_here:
		video = cv.VideoCapture(video)
		if video.get(cv.CAP_PROP_FRAME_COUNT) < 5:
			print("Video does not contain any face")
			return
		creation = cf.person.create(groupID, name)
		person_id = creation["personId"]

		shift = video.get(cv.CAP_PROP_FRAME_COUNT) // video.get(cv.CAP_PROP_FPS) // 5
		print("5 frames extracted")
		print("PersonId:", person_id)
		print("FaceIds")
		print("=======")
		for i in range(5): 
			video.set(cv.CAP_PROP_POS_FRAMES, shift * i)
			res, frame = video.read()
			cv.imwrite("frame{}.jpg".format(i), frame)
			face_id = cf.person.add_face("frame{}.jpg".format(i), groupID, person_id)
			print(face_id["persistedFaceId"])
	else:
		video = cv.VideoCapture(video)
		if video.get(cv.CAP_PROP_FRAME_COUNT) < 5:
			print("Video does not contain any face")
			return
		shift = video.get(cv.CAP_PROP_FRAME_COUNT) // video.get(cv.CAP_PROP_FPS) // 5
		for i in range(5): 
			video.set(cv.CAP_PROP_POS_FRAMES, shift * i)
			res, frame = video.read()
			cv.imwrite("frame{}.jpg".format(i), frame)
			face_det = cf.face.detect("frame{}.jpg".format(i))
			if len(face_det) == 0:
				print("Video does not contain any face")
				return
			elif cf.face.verify(face_det[0]["faceId"], person_group_id = groupID, person_id = person_id)["isIdentical"] != True:
				print("Video does not contain any face")
				return
		print("5 frames extracted")
		print("PersonId:", person_id)
		print("FaceIds")
		print("=======")
		for i in range(5):
			face_id = cf.person.add_face("frame{}.jpg".format(i), groupID, person_id)
			print(face_id["persistedFaceId"])
		with open("person.json", 'w') as prs:
			dump({"personID": person_id})


def deletion(name):
	for person in cf.person.lists(groupID):
		if person["name"] == name:
			print("Person with id {} deleted".format(person["personId"]))
			cf.person.delete(groupID, person["personId"])
			return
	print("No person with name \"{}\"".format(name))


def train():
	cf.person_group.train(groupID)
	print("Training task for {} persons started".format(len(cf.person.lists(groupID))))


def identify(video):
	try:
		status = cf.person_group.get_status(groupID)
	except:
		print("The system is not ready yet")
		return
	if status["status"] != "succeeded":
		print("The system is not ready yet")
		return
	vid = cv.VideoCapture(video)
	shift = vid.get(cv.CAP_PROP_FRAME_COUNT) // vid.get(cv.CAP_PROP_FPS) // 5
	perc_cons = 0
	person_id = ""
	for i in range(5):
		vid.set(cv.CAP_PROP_POS_FRAMES, shift * i)
		res, frame = vid.read()
		cv.imwrite("ident_frame{}.jpg".format(i), frame)
		response = cf.face.detect("ident_frame{}.jpg".format(i))
		faces_ids = [response[0]["faceId"]]
		identified_faces = cf.face.identify(faces_ids, person_group_id = groupID)
		for x in identified_faces:
			if len(x["candidates"]) > 0 and int(x["candidates"][0]["confidence"] * 100) > 50:
				perc_cons += 1
				person_id = x["candidates"][0]["personId"]
	if perc_cons == 5:
		name = cf.person.get(groupID, person_id)["name"]
		print("The person is \"{}\"".format(name))
		with open("person.json", 'w') as person:
			dump({"personID": person_id}, person)
	else:
		print("The person cannot be identified")
		

if len(sys.argv) == 1:
	print("Unknown command")
elif sys.argv[1] == "--name":
	name = sys.argv[2]
	video = sys.argv[3]
	add_new(name, video)
elif sys.argv[1] == "--del":
	name = sys.argv[2]
	deletion(name)
elif sys.argv[1] == "--train":
	train()
elif sys.argv[1] == "--identify":
	video = sys.argv[2]
	identify(video)