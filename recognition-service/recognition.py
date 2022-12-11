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
infoKey = "{}.rest.info".format(platform.node())
debugKey = "{}.rest.debug".format(platform.node())
def log_debug(message, key=debugKey):
    print("DEBUG:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{debugKey}:{message}")

def log_info(message, key=infoKey):
    print("INFO:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{infoKey}:{message}")

def identify_track(request_id, segment_start, segment_end):
    log_info(f"Identify track for {request_id}, {segment_start}:{segment_end}")
    
    song_info = {}

    # Open segment 
    try:
        #log_info("trying")
        response = minioClient.fget_object(request_id, f"{segment_start}:{segment_end}", f"tmp/{segment_start}:{segment_end}")
        #response = minioClient.get_object(request_id, f"{segment_start}:{segment_end}")
        #log_info(f"Minio response: {response}")
        log_info(f"Downloaded from minio to local file")
        minioClient.remove_object(request_id, f"{segment_start}:{segment_end}")
        log_info(f"Deleted segment from minio")
    except Exception as exp:
        log_debug(f"Exception raised downloading from Minio: {str(exp)}")
    # finally:
    #     response.close()
    #     response.release_conn()
    
    try:
        segment = open(f"tmp/{segment_start}:{segment_end}", 'rb').read()
        log_info(f"Opened segment file for {segment_start} to {segment_end}")  
    except Exception as exp:
        log_debug(f"Exception raised opening segment from local: {str(exp)}")

    try:
        log_info(f"Opening new Shazam object") 

        shazam = Shazam(segment)
        recognize_generator = shazam.recognizeSong()
        #while True:
        first_match = next(recognize_generator)[1]
        log_info(f"Found one record")
        #break
        if(not first_match['track']):
            log_info("First match has no track info")
        if(not first_match['track']['title']):
            log_info("First match has no title")
        if(not first_match['track']['subtitle']):
            log_info("First match has no subtitle")
        song_info['title'] = first_match['track']['title']
        #song_info['Track ID'] = one_record[1]['track']['key']
        song_info['subtitle'] = first_match['track']['subtitle']
        log_info(f"Found record match: {song_info}")
    except Exception as exp:
        log_debug(f"Exception raised interacting with Shazam: {str(exp)}")
    
    # segment.close()
    try:
        os.remove(f"tmp/{segment_start}:{segment_end}")
        log_info("Removed segment from local storage")
    except Exception as exp:
        log_debug(f"Exception raised deleting local file: {str(exp)}")

    #TODO: Print songs to Redis
    if(song_info["title"]):
        redisClient.rpush(request_id, jsonpickle.encode(song_info))
        log_info("Reported song info to Redis")
    #Frontend can provide request_id and encourage user to refresh the page

def signal_end(request_id):
    try:
        minioClient.remove_bucket(request_id)
    except Exception as exp:
        log_debug(f"Exception raised deleting segments bucket: {str(exp)}")
    redisClient.rpush(f"{request_id}-done", 1)

# Watch for jobs
while True:
    try:
        request = redisClient.blpop("to-recognizer", timeout = 0)[1].decode()
        [request_id, segment_start, segment_end] = request.split(":")
        log_info(f"Found job {request_id}, {segment_start}:{segment_end}")
        if(segment_start == "done"):
            signal_end(request_id)
        else:
            identify_track(request_id, segment_start, segment_end)
    except Exception as exp:
        log_debug(f"Exception raised in receive-job loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()