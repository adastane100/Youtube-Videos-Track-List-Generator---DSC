#!/usr/bin/env python3
## https://github.com/dotX12/ShazamIO

import os, sys, platform
from ShazamAPI import Shazam
import redis
from minio import Minio

# Redis
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379
redisClient = redis.Redis(host=redisHost, port=redisPort, db=0)

# Minio
minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

minioClient = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)

# Logging
infoKey = "{}.rest.info".format(platform.node())
debugKey = "{}.rest.debug".format(platform.node())
def log_debug(message, key=debugKey):
    print("DEBUG:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{debugKey}:{message}")

def log_info(message, key=infoKey):
    print("INFO:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{infoKey}:{message}")

def identify_track(request_id, segment_start, segment_end):
    song_info = {}

    # Open segment 
    segmentAudio = minioClient.get_object(request_id, f"{segment_start}:{segment_end}")

    try:
        #mp3_file_content_to_recognize = open(destination+video_title+'/'+track, 'rb').read()
        shazam = Shazam(segmentAudio)
        recognize_generator = shazam.recognizeSong()
        while True:
            one_record = next(recognize_generator)
            break
        
        song_info['title'] = one_record[1]['track']['title']
        song_info['Track ID'] = one_record[1]['track']['key']
        song_info['Sub title'] = one_record[1]['track']['subtitle']
    except:
        song_info = {}
    return song_info


def recognizeSongs():
    segment = redisClient.blpop("to-recognizer", timeout=0)
    [request_id, segment_start, segment_end] = segment.split(":")
    identify_track(request_id, segment_start, segment_end)

# Watch for jobs
while True:
    try:
        request_id = redisClient.blpop("to-recognizer", timeout = 0)
        log_info(f"Found job {request_id}")
        recognizeSongs(request_id)
    except Exception as exp:
        log_debug(f"Exception raised in receive-job loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()