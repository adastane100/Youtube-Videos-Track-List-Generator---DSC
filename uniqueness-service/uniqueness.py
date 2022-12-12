#!/usr/bin/env python3

import os, sys, platform
import threading
import redis
import jsonpickle
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

def forward_if_unique(request_id, song, unique_songs):
    song_dict = jsonpickle.decode(song)
    id = song_dict['id']
    if not id:
        return
    if(id not in unique_songs):
        log_info(f"Song {song_dict['title']} is unique")
        redisClient.rpush(f"{request_id}-filtered", song.encode())
        unique_songs.add(id)

def finish_check(request_id, unique_songs):
    log_info("Finish checking uniqueness")
    popped = redisClient.lpop(f'{request_id}-unfiltered')
    while popped:
        song = popped[1].decode()
        log_info(song)
        forward_if_unique(request_id, song, unique_songs)
        popped = redisClient.lpop(f"{request_id}-unfiltered")
    redisClient.set(f'{request_id}-status', "done")
    log_info(f"Thread for {request_id} is done.")
    return

def uniqueness_check(request_id):
    log_info(f"Started new thread for {request_id}")
    unique_songs = set()
    while True:
        job_status = redisClient.get(f'{request_id}-status').decode()
        log_info(f"{request_id} status: {job_status}")
        if job_status == 'uniqueness-check':
            finish_check(request_id, unique_songs)
            break
        popped = redisClient.blpop(f'{request_id}-unfiltered', timeout = 15)
        if popped:
            song = popped[1].decode()
            log_info(f"Checking uniqueness on {song}")
            forward_if_unique(request_id, song, unique_songs)


# Watch for jobs
while True:
    try:
        job = redisClient.blpop("check-uniqueness", timeout = 0)
        #log_info(f"Found job {job}")
        request_id = job[1].decode()
        log_info(f"Request ID: {request_id}")
        thread = threading.Thread(target=uniqueness_check, args=[request_id])
        thread.start()
    except Exception as exp:
        log_debug(f"Exception raised in receive-job loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()