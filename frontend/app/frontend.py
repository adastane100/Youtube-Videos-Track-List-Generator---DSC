#!/usr/bin/env python3

##
## Flask REST server for tracklist generator homepage
##
from flask import Flask, render_template, request, Response, jsonify, redirect, url_for
import json, jsonpickle
import os, sys, platform
import uuid
from redis import Redis
from minio import Minio

# Initialize the Flask application
app = Flask(__name__)
app.logger.info("instance created")

# Redis
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379
redisClient = Redis(host=redisHost, port=redisPort, db=0)

# Logging
infoKey = "{}.rest.info".format(platform.node())
debugKey = "{}.rest.debug".format(platform.node())
def log_debug(message, key=debugKey):
    print("DEBUG:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{key}:{message}")
def log_info(message, key=debugKey):
    print("INFO:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{key}:{message}")

# Minio
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

minioClient = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)
log_info(f"Demucs worker connected to minio client {minioClient}")

@app.route('/')
def home():
    log_info(f"Home route")
    return render_template('index.html', result_success=False)

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    log_info(f"Healthcheck")
    return json.dumps({"Healthcheck": "Healthy"})

@app.route('/generate_request', methods=['POST'])
def generate_request():
    log_info("Generate request endpoint")
    input_link = request.form.get("url_link")
    input_val = input_link.strip()
    request_id = str(uuid.uuid4().hex)
    log_info(f"Request ID: {request_id}, Input: {input_val}")
    redisClient.rpush('to-downloader', f"{request_id}:{input_val}")
    # response = {'request_id': request_id}
    # return Response(response=jsonpickle.encode(response), status=200, mimetype='application/json')
    return jsonify({"request_id": request_id, "request_status": 'processing'})

@app.route('/check_status/<request_id>', methods=['GET'])
def check_status(request_id):
    log_info("Status check")
    try:
        result = redisClient.lpop(f"{request_id}-done")
    except Exception as exp:
        log_debug(f"Request is not done: {str(exp)}")
    if result:
        log_info("Track list found")
        return redirect(url_for("track_list", id=request_id))
    else:
        log_info("Still processing")
        return jsonify({"request_id": request_id, "request_status": 'processing'})

@app.route('/track_list', methods=['GET'])
def track_list():
    # Wait for done message
    # TODO: Dynamically update page as results are found
    # redisClient.blpop(f"{request_id}-done") # Wait until results are done
    # log_info(f"Request ID: {request_id} tracks are done")
    request_id = request.args['id']

    identified_tracks = []
    raw_pop = redisClient.lpop(request_id)
    log_info(raw_pop)
    if(not raw_pop):
        return jsonify({"status": "No tracks found"})
    result = raw_pop.decode()
    log_info(result)
    while(result):
        log_info(f"Result popped from redis: {result}")
        result_unpickled = jsonpickle.decode(result)
        log_info(f"Result decoded: {result_unpickled}")
        identified_tracks.append(result_unpickled)
        bytes = redisClient.lpop(request_id)
        if (bytes):
            result = redisClient.lpop(request_id).decode()
        else:
            break

    log_info(f"Multipop loop done. Identified tracks: {identified_tracks}")        
        
    if identified_tracks is not None and len(identified_tracks) > 0:
        log_info("Tracks found")
        return render_template(
            'index.html',
            # url=input_val,
            tracks=identified_tracks,
            len=len(identified_tracks),
            result_success=True
        )
    else:
        log_info("No tracks found")
        return render_template(
            'index.html',
            # url=input_val,
            tracks='NO TRACKS FOUND',
            result_success=False
        ) 

# @app.route('/track_list', methods=['POST'])
# def generate_tracks():
#     log_info(f"Track list endpoint")

#     input_link = request.form.get("url_link")
#     input_val = input_link.strip()
#     request_id = str(uuid.uuid4().hex)
#     log_info(f"Request ID: {request_id}, Input: {input_val}")
#     redisClient.rpush('to-downloader', f"{request_id}:{input_val}")

#     # Wait for done message
#     # TODO: Dynamically update page as results are found
#     redisClient.blpop(f"{request_id}-done") # Wait until results are done
#     log_info(f"Request ID: {request_id} tracks are done")
    
#     identified_tracks = []
#     raw_pop = redisClient.lpop(request_id)
#     log_info(raw_pop)
#     result = raw_pop.decode()
#     log_info(result)
#     while(result):
#         log_info(f"Result popped from redis: {result}")
#         result_unpickled = jsonpickle.decode(result)
#         log_info(f"Result decoded: {result_unpickled}")
#         identified_tracks.append(result_unpickled)
#         bytes = redisClient.lpop(request_id)
#         if (bytes):
#             result = redisClient.lpop(request_id).decode()
#         else:
#             break

#     log_info(f"Multipop loop done. Identified tracks: {identified_tracks}")        
        
#     if identified_tracks is not None and len(identified_tracks) > 0:
#         log_info("Tracks found")
#         return render_template(
#             'index.html',
#             url=input_val,
#             tracks=identified_tracks,
#             len=len(identified_tracks),
#             result_success=True
#         )
#     else:
#         log_info("No tracks found")
#         return render_template(
#             'index.html',
#             url=input_val,
#             tracks='NO TRACKS FOUND',
#             result_success=False
#         ) 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

