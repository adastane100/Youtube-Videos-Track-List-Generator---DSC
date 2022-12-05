#!/usr/bin/env python3

##
## Flask REST server for tracklist generator homepage
##
from flask import Flask, render_template, request
import json
import os, sys
from redis import Redis
from minio import Minio
from ShazamAPI import Shazam
import DownloadFromYoutube, AudioSegmenting, RecognizeTrack

# Initialize the Flask application
app = Flask(__name__)
app.logger.info("instance created")
destination = './mp4Files/'

# Redis
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379
redisClient = Redis(host=redisHost, port=redisPort, db=0)

debugKey = "frontend"
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
    return render_template('index.html',result_success=False)


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return json.dumps({"Healthcheck": "Healthy"})


@app.route('/track_list', methods=['POST'])
def generate_tracks():
    print('in main')
    input_link = request.form.get("url_link")
    input_val = input_link.strip()
    identified_tracks = []

    # download mp4 file from youtube link
    video_title = DownloadFromYoutube.downloadAudio(input_val)
    print('video_title :::: '+video_title)
    # TODO: Store in minio

    # TODO: Send message to segmenter
    # segmenting the downloaded file
    segmented_tracks = AudioSegmenting.segmentAudio(video_title[:-4])

    # TODO: Watch for recognized tracks and display them
    all_track_titles = []
    if len(segmented_tracks) > 0:
        print('in for loop of tracks')
        for track in segmented_tracks:
            track_info = {}
            # identify tracks from mp4 segment file
            track_info = RecognizeTrack.identify_track(video_title[:-4],track)
            if track_info is not None and len(track_info) > 0 and track_info['title'] not in all_track_titles:
                all_track_titles.append(track_info['title'])
                identified_tracks.append(track_info)
    
        print('Total identified tracks :::'+str(len(identified_tracks)))
        for single_track in identified_tracks:
            print(single_track)
        
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

