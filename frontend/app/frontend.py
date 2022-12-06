#!/usr/bin/env python3

##
## Flask REST server for tracklist generator homepage
##
from flask import Flask, render_template, request, session
import json
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
    return render_template('index.html', result_success=False)


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return json.dumps({"Healthcheck": "Healthy"})


@app.route('/track_list', methods=['POST'])
def generate_tracks():
    print('in main')
    input_link = request.form.get("url_link")
    input_val = input_link.strip()
    identified_tracks = []

    request_id = uuid.uuid4()
    redisClient.lpush('to-downloader', f"{request_id}:{input_val}")

    # Wait for done message
    # TODO: Dynamically update page as results are found
    redisClient.blpop(f"{request_id}-done") # Wait until results are done
    identified_tracks = redisClient.lmpop(request_id)[1] # Get results
        
    if identified_tracks is not None and len(identified_tracks) > 0:
        return render_template(
            'index.html',
            url=input_val,
            tracks=identified_tracks,
            len=len(identified_tracks),
            result_success=True
        )
    else:
       return render_template(
            'index.html',
            url=input_val,
            tracks='NO TRACKS FOUND',
            result_success=False
        ) 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

