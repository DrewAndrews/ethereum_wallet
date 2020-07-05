import cognitive_face as cf
import cv2
import sys
from json import load
import time


with open("faceid.json") as key_data:
    data = load(key_data)
    key = data["MSkey"]
    base_url = data["serviceUrl"]
    groupID = data["groupId"]


try:
    cf.person_group.create(groupID, name)
except:
    pass


cf.BaseUrl.set(base_url)
cf.Key.set(key)


def get_face(name, image):
    person = cf.person.create(groupID, name)
    personID = person["personId"]
    face = cf.face.detect(image)
    print(face)
    print(person)


start = time.monotonic()

video = cv2.VideoCapture(0)
frame_width = int(video.get(3))
frame_height = int(video.get(4))

out = cv2.VideoWriter("out.avi", cv2.VideoWriter_fourcc("M", "P", "P", "G"), 10, (frame_width, frame_height))

while True:
    ret, frame = video.read()
    out.write(frame)
    end = time.monotonic()
    interval = int(end - start)
    if interval > 5:
        break
    ret, frame = video.read()
    out.write(frame)