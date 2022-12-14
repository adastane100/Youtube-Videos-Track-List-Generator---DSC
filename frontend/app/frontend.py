#!/usr/bin/env python3

##
## Flask REST server for tracklist generator homepage
##
from flask import Flask, render_template, request, Response, jsonify, redirect, url_for, session
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
infoKey = "{}.info".format(platform.node())
debugKey = "{}.debug".format(platform.node())
def log_debug(message, key=''):
    print("DEBUG:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{infoKey:50}:{key}:{message}")
def log_info(message, key=''):
    print("INFO:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{debugKey:50}:{key}:{message}")

# Minio
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

minioClient = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)

#app.secret_key = os.getenv("FLASK_SECRET") or os.urandom(12).hex()
app.secret_key = "secret123"

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
    log_info(f"Input: {input_val}", key=request_id)
    redisClient.rpush('to-downloader', f"{request_id}:{input_val}")
    redisClient.set(f'{request_id}-status', "downloading")
    session[request_id] = []
    #return redirect(url_for("check_status", id=request_id))
    return redirect(url_for("track_list", id=request_id))

@app.route('/track_list', methods=['GET'])
def track_list():
    request_id = request.args['id']
    identified_tracks = session[request_id]
    status = ''
    try:
        status = redisClient.get(f"{request_id}-status").decode()
    except Exception as exp:
        log_debug(f"Error getting request status: {str(exp)}", key=request_id)

    raw_pop = redisClient.lpop(f"{request_id}-filtered")
    if not raw_pop:
        result = None
    else:
        result = raw_pop.decode()
    while(result):
        result_unpickled = jsonpickle.decode(result)
        log_info(f"Result popped from redis: {result_unpickled}", key=request_id)
        identified_tracks.append(result_unpickled)
        bytes = redisClient.lpop(f"{request_id}-filtered")
        if (bytes):
            result = bytes.decode()
        else:
            break

    log_info(f"Multipop loop done. Identified tracks: {identified_tracks}", key=request_id)
    session[request_id] = identified_tracks        
        
    if identified_tracks is not None and len(identified_tracks) > 0:
        log_info("Tracks found", key=request_id)
        return render_template(
            'index.html',
            tracks=identified_tracks,
            len=len(identified_tracks),
            result_success=True,
            status=status
        )
    else:
        log_info("No tracks found", key=request_id)
        return render_template(
            'index.html',
            tracks='No tracks yet',
            result_success=False,
            status=status
        ) 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

