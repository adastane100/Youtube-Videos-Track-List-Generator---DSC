#!/usr/bin/env python3

from pydub import AudioSegment
import os, sys, platform, io
from pathlib import Path
import redis
from minio import Minio

source = './mp4Files/'
destination = './segmentedTracks/'
fifty_seconds = 50 * 1000

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

# Function
def segmentAudio(request_id):
    log_info('in AudioSegmenting')
    # pydub does things in milliseconds
    segmented_tracks = []

    fullAudioName = source+request_id+'.mp4'

    # Move full audio from Minio to local disk
    try:
        fullAudio = minioClient.fget_object("mp4files", request_id, fullAudioName)
        log_info(f"Downloaded full mp4 from minio")
    except Exception as exp:
        log_debug(f"Exception raised downloading from Minio: {str(exp)}")

    try:
        mp4_song = AudioSegment.from_file(fullAudioName, "mp4")
        log_info(f"Created music file {mp4_song} with pydub")
    except Exception as exp:
        log_debug(f"Exception raised in AudioSegment: {str(exp)}")

    # Create segmentations folder on disk
    # seg_path = Path(destination+request_id+'/')
    # if not os.path.exists(seg_path):
    #     os.makedirs(seg_path)
    #     log_info(f"Created local storage for audio segments")

    # Create segmentations folder on Minio
    if not minioClient.bucket_exists(request_id):
        minioClient.make_bucket(request_id)
        log_info(f"Created minio bucket {request_id} for audio segments")
    
    videofile_len = len(mp4_song)
    log_info('videofile_len :: '+ str(videofile_len))
    for i in range(0,videofile_len,fifty_seconds):
        if i+fifty_seconds < videofile_len:
            segment = mp4_song[i:i+fifty_seconds]
        else:
            segment = mp4_song[i:videofile_len]
        if len(segment) > 0 :
            filename = f"/tmp/{i}:{i+len(segment)}.mp4"
            try:
                segment.export(out_f=filename,format='mp4')
            except Exception as exp:
                log_debug(f"Exception raised storing segment locally: {str(exp)}")
            try:
                #minioClient.put_object(request_id, str(f"{i}:{i+len(segment)}"), io.BytesIO(segment.raw_data), len(segment.raw_data), content_type='application/mp4')
                minioClient.fput_object(request_id, str(f"{i}:{i+len(segment)}"), filename, content_type='audio/mp4')
                log_info(f"Stored segment {i}:{i+len(segment)} in minio")
            except Exception as exp:
                log_debug(f"Exception raised putting object in Minio: {str(exp)}")
            redisClient.rpush("to-recognizer", f"{request_id}:{i}:{i+len(segment)}")
            log_info(f"Sent job to Redis")
            # Local
            #segment.export(out_f=destination+request_id+'/'+'segment'+str(i)+'.mp4',format='mp4')
            #segmented_tracks.append('segment'+str(i)+'.mp4') 
    
    log_info(f"Finished segmenting for job {request_id}")
    redisClient.rpush('to-recognizer', f"{request_id}:done:")
    try:
        minioClient.remove_object("mp4files", request_id)
        log_info(f"Removed original mp4 from Minio")
    except Exception as exp:
        log_debug(f"Exception raised deleting mp4file: {str(exp)}")


# Watch for jobs
while True:
    try:
        request_id = redisClient.blpop("to-segmenter", timeout = 0)[1].decode()
        log_info(f"Found job {request_id}")
        segmentAudio(request_id)
    except Exception as exp:
        log_debug(f"Exception raised in receive-job loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()