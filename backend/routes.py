from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count")
def count():
    song_count = db.songs.count_documents({})
    return {"count":song_count}, 200

@app.route("/song")
def songs():
    songs_cursor = db.songs.find({})
    songs_list = []
    for song in songs_cursor:
        song['_id'] = str(song['_id'])
        songs_list.append(song)
    return {"songs": songs_list}, 200

@app.route("/song/<id>")
def get_song_by_id(id):
    song = db.songs.find_one({"id": int(id)})
    if song:
        song['_id'] = str(song['_id'])
        return {"song": song}, 200
    else:
        return {"message": "song with id not found"}, 404 

@app.route("/song", methods=["POST"])
def create_song():
    song = request.json
    ifSong = db.songs.find_one({"id": int(song['id'])})
    if ifSong:
        return {"Message": f"song with id {song['id']} already present"}, 302
    db.songs.insert_one(song)
    song['_id'] = str(song['_id'])
    return {"inserted id":{"$oid":song['_id']}}


@app.route("/song/<id>", methods=["PUT"])
def update_song(id):
    song = request.json
    ifSong = db.songs.find_one({"id": int(id)})
    if not ifSong:
        return {"message": "song not found"}, 404
    db.songs.update_one({"id": int(id)}, {"$set": song})
    updated_song = db.songs.find_one({"id": int(id)})
    if updated_song:
        updated_song['_id'] = str(updated_song['_id'])
        return jsonify(updated_song), 200

@app.route("/song/<id>", methods=["DELETE"])
def delete_song(id):
    ifSong = db.songs.find_one({"id": int(id)})
    if not ifSong:
        return {"message": "song not found"}, 404
    toDelete = db.songs.delete_one({"id": int(id)})
    if toDelete.deleted_count == 1:
        return '', 204