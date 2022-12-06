#pip install pytube ffmpeg pydub ShazamAPI shazamio playsound

from pydub import AudioSegment
from pytube import YouTube
import os, sys, platform
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
def segmentAudio(url_link, request_id):
    print('in AudioSegmenting')
    # pydub does things in milliseconds
    segmented_tracks = []

    fullAudioName = source+request_id+'.mp4'

    # Move full audio from Minio to local disk
    fullAudio = minioClient.fget_object("mp4files", request_id, fullAudioName)
    mp4_song = AudioSegment.from_file(fullAudioName, "mp4")

    # Create segmentations folder on disk
    seg_path = Path(destination+request_id+'/')
    if not os.path.exists(seg_path):
        os.makedirs(seg_path)

    # Create segmentations folder on Minio
    if not minioClient.bucket_exists(request_id):
        minioClient.make_bucket(request_id)
    
    videofile_len = len(mp4_song)
    print('videofile_len :: '+ str(videofile_len))
    for i in range(0,videofile_len,fifty_seconds):
        if i+fifty_seconds < videofile_len:
            segment = mp4_song[i:i+fifty_seconds]
        else:
            segment = mp4_song[i:videofile_len]
        if len(segment) > 0 :
            # Distributed
            minioClient.put_object(request_id, str(f"{i}:{i+len(segment)}"))
            redisClient.lpush("to-recognizer", f"{request_id}:{i}:{i+len(segment)}")
            # Local
            segment.export(out_f=destination+request_id+'/'+'segment'+str(i)+'.mp4',format='mp4')
            segmented_tracks.append('segment'+str(i)+'.mp4') 
        
    return segmented_tracks

# Watch for jobs
while True:
    try:
        request_id = redisClient.blpop("to-segmenter", timeout = 0)
        log_info(f"Found job {request_id}")
        segmentAudio(request_id)
    except Exception as exp:
        log_debug(f"Exception raised in receive-job loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()