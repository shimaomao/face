import os
import re
import scipy.misc
import numpy as np
import face_recognition
import pickle
import warnings
from pymongo import MongoClient
from bson.binary import Binary
from sanic import Sanic
from sanic import response
from sanic_cors import CORS
from tempfile import NamedTemporaryFile

data_set_path = os.environ['BM_IMAGES_DATA_PATH']
mongo_host = os.environ['MONGO_HOST']
client = MongoClient(mongo_host, 27017)
db = client['bm-platform']

def image_files_in_folder(folder):
    return [os.path.join(folder, f) for f in os.listdir(folder) if re.match(r'.*\.(jpg|jpeg|png)', f, flags=re.I)]

def scan_known_people(known_people_folder):
    for file in image_files_in_folder(known_people_folder):
        basename = os.path.splitext(os.path.basename(file))[0]
        try:
            img = face_recognition.load_image_file(file)
            encodings = face_recognition.face_encodings(img)
        except:
            continue

        if len(encodings) != 0:
            db.imageencodings.update_one({"name": basename}, {
                "$set": {"encodings": Binary(pickle.dumps(encodings[0], protocol=2))}
            }, upsert=True)

def update_data(name, image):
    print(['yay', name, image])

def test_image(image_to_check, tolerance=0.6, show_distance=False):
    unknown_image = face_recognition.load_image_file(image_to_check)

    # Scale down image if it's giant so things run a little faster
    if unknown_image.shape[1] > 1600:
        scale_factor = 1600.0 / unknown_image.shape[1]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            unknown_image = scipy.misc.imresize(unknown_image, scale_factor)

    unknown_encodings = face_recognition.face_encodings(unknown_image)

    data = []

    for doc in db.imageencodings.find():
        new_doc = {}
        new_doc['name'] = doc['name']
        new_doc['encodings'] = pickle.loads(doc['encodings'])
        data.append(new_doc)

    known_names = list(map(lambda x: x['name'], data))
    known_face_encodings = list(map(lambda x: x['encodings'], data))

    for unknown_encoding in unknown_encodings:
        distances = face_recognition.face_distance(known_face_encodings, unknown_encoding)
        result = list(distances <= tolerance)

        if True in result:
            return [{"name":name, "distance": distance} for is_match, name, distance in zip(result, known_names, distances) if is_match]
        else:
            return []

app = Sanic()
CORS(app)

@app.route("/scan", methods=['POST'])
async def test(request):
    #scan_known_people(data_set_path)
    return response.json({"ok": True})

@app.route("/update", methods=['POST'])
async def test(request):
    return response.json({"ok": True})

@app.route("/", methods=['POST'])
async def test(request):
    f = NamedTemporaryFile()
    f.write(request.files.get('image').body)
    result = test_image(f.name)
    f.close()
    return response.json({"result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
