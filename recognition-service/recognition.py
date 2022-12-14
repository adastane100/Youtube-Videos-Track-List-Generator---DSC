#!/usr/bin/env python3

'''
https://github.com/dotX12/ShazamIO
'''

import os, sys, platform
import jsonpickle
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
infoKey = "{}.info".format(platform.node())
debugKey = "{}.debug".format(platform.node())
def log_debug(message, key=''):
    print("DEBUG:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{debugKey:50}:{key}:{message}")

def log_info(message, key=''):
    print("INFO:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{infoKey:50}:{key}:{message}")

def identify_track(request_id, segment_start, segment_end):
    log_info(f"Identify track, {segment_start}:{segment_end}", key=request_id)
    
    song_info = {}

    # Open segment 
    try:
        minioClient.fget_object(request_id, f"{segment_start}:{segment_end}", f"tmp/{segment_start}:{segment_end}")
        #log_info(f"Downloaded from minio to local file")
        minioClient.remove_object(request_id, f"{segment_start}:{segment_end}")
        #log_info(f"Deleted segment from minio")
    except Exception as exp:
        log_debug(f"Exception raised downloading from Minio: {str(exp)}", key=request_id)
    
    try:
        segment = open(f"tmp/{segment_start}:{segment_end}", 'rb').read()
        #log_info(f"Opened segment file for {segment_start} to {segment_end}")  
    except Exception as exp:
        log_debug(f"Exception raised opening segment from local: {str(exp)}", key=request_id)

    try:
        #log_info(f"Opening new Shazam object") 
        shazam = Shazam(segment)
        recognize_generator = shazam.recognizeSong()
    except Exception as exp:
        log_debug(f"Exception raised interacting with Shazam: {str(exp)}", key=request_id)
        return
    first_match = next(recognize_generator)[1]
    #log_info(f"Found one record: {first_match}")
    if len(first_match['matches']) == 0:
        log_info(f"Not recognized: Segment {segment_start}:{segment_end}", key=request_id)
        return
    if(not first_match['track']):
        log_info("First match has no track info", key=request_id)
    if(not first_match['track']['title']):
        log_info("First match has no title", key=request_id)
    if(not first_match['track']['subtitle']):
        log_info("First match has no subtitle", key=request_id)
    song_info['title'] = first_match['track']['title']
    song_info['id'] = first_match['track']['key']
    song_info['subtitle'] = first_match['track']['subtitle']
    log_info(f"Found record match: {song_info}", key=request_id)
    
    
    # Delete segment from local
    try:
        os.remove(f"tmp/{segment_start}:{segment_end}")
        #log_info("Removed segment from local storage")
    except Exception as exp:
        log_debug(f"Exception raised deleting local file: {str(exp)}", key=request_id)

    # Report tracks to Redis
    if(song_info["title"]):
        redisClient.rpush(f"{request_id}-unfiltered", jsonpickle.encode(song_info))

def signal_end(request_id):
    try:
        minioClient.remove_bucket(request_id)
    except Exception as exp:
        log_debug(f"Exception raised deleting segments bucket: {str(exp)}", key=request_id)
    redisClient.set(f'{request_id}-status', "uniqueness-check")
    redisClient.rpush(f"{request_id}-done", 1)
    log_info(f"Recognition complete", key=request_id)

# Watch for jobs
while True:
    try:
        request = redisClient.blpop("to-recognizer", timeout = 0)[1].decode()
        [request_id, segment_start, segment_end] = request.split(":")
        log_info(f"Starting recognizer for {segment_start}:{segment_end}", key=request_id)
        if(segment_start == "done"):
            signal_end(request_id)
        else:
            identify_track(request_id, segment_start, segment_end)
    except Exception as exp:
        log_debug(f"Exception raised in receive-job loop: {str(exp)}", key=request_id)
    sys.stdout.flush()
    sys.stderr.flush()