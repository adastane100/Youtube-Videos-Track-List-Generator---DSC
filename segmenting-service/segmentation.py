#!/usr/bin/env python3

from pydub import AudioSegment
import os, sys, platform, io
from pathlib import Path
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


source = 'mp4files/'
destination = 'segmented/'
fifty_seconds = 50 * 1000

# Segmenting
def segmentAudio(request_id):
    log_info(f'Segmenting request', key=request_id)
    fullAudioName = source + request_id + '.mp4'

    # Move full audio from Minio to local disk
    try:
        minioClient.fget_object("mp4files", request_id, fullAudioName)
        #log_info(f"Downloaded full mp4 from minio")
    except Exception as exp:
        log_debug(f"Exception raised downloading from Minio: {str(exp)}", key=request_id)

    # Load audio object from file
    try:
        mp4_song = AudioSegment.from_file(fullAudioName, "mp4")
        #log_info(f"Created music file {mp4_song} with pydub")
    except Exception as exp:
        log_debug(f"Exception raised in AudioSegment: {str(exp)}", key=request_id)

    # Create segmentation bucket in Minio
    try:
        if not minioClient.bucket_exists(request_id):
            minioClient.make_bucket(request_id)
            #log_info(f"Created minio bucket {request_id} for audio segments")
    except Exception as exp:
        log_debug(f"Exception raised creating Minio bucket: {str(exp)}", key=request_id)

    # Process segments
    videofile_len = len(mp4_song)
    log_info('videofile_len :: '+ str(videofile_len), key=request_id)
    for i in range(0, videofile_len, fifty_seconds):
        if i+fifty_seconds < videofile_len:
            segment = mp4_song[i:i+fifty_seconds]
        else:
            segment = mp4_song[i:videofile_len]
        if len(segment) > 0 :
            # Save to local disk
            segmentName = f"{destination}{i}:{i+len(segment)}.mp4"
            try:
                segment.export(out_f=segmentName, format='mp4')
            except Exception as exp:
                log_debug(f"Exception raised storing segment locally: {str(exp)}", key=request_id)
            # Transfer to Minio
            try:
                minioClient.fput_object(request_id, str(f"{i}:{i+len(segment)}"), segmentName, content_type='audio/mp4')
                #log_info(f"Stored segment {i}:{i+len(segment)} in minio")
            except Exception as exp:
                log_debug(f"Exception raised putting object in Minio: {str(exp)}", key=request_id)
            # Send job to recognizer 
            redisClient.rpush("to-recognizer", f"{request_id}:{i}:{i+len(segment)}")
            #log_info(f"Sent job to Redis")
            # Delete from local disk
            try:
                os.remove(segmentName)
            except Exception as exp:
                log_debug(f"Exception raised deleting segment: {str(exp)}", key=request_id)
    
    # Finish and clean up
    log_info(f"Finished segmenting for job {request_id}")
    redisClient.set(f'{request_id}-status', "recognizing")
    redisClient.rpush('to-recognizer', f"{request_id}:done:")
    try:
        os.remove(fullAudioName)
        #log_info(f"Removed mp4 from local storage")
    except Exception as exp:
        log_debug(f"Exception raised deleting mp4file: {str(exp)}", key=request_id)
    try:
        minioClient.remove_object("mp4files", request_id)
        #log_info(f"Removed original mp4 from Minio")
    except Exception as exp:
        log_debug(f"Exception raised deleting mp4file from Minio: {str(exp)}", key=request_id)


# Watch for jobs
while True:
    try:
        request_id = redisClient.blpop("to-segmenter", timeout = 0)[1].decode()
        log_info(f"Starting segmenter", key=request_id)
        segmentAudio(request_id)
    except Exception as exp:
        log_debug(f"Exception raised in receive-job loop: {str(exp)}", key=request_id)
    sys.stdout.flush()
    sys.stderr.flush()