#pip install pytube ffmpeg pydub ShazamAPI shazamio playsound

from pytube import YouTube
import os, sys, platform
from pathlib import Path
import redis
from minio import Minio

destination = './mp4Files/'

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

# Function
def downloadAudio(url_link, request_id):
    log_info('in downloadFromYoutube')
    yt = YouTube(url_link)
    audioStream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
    log_info(f'All audioStreams: {yt.streams.filter(only_audio=True)}', key=request_id)
    out_file = audioStream.download(output_path=destination)
    your_path = Path(out_file)
    try:
        minioClient.fput_object("mp4files", request_id, your_path)
        #log_info(f"Stored full mp4 file for {request_id} in minio", key=request_id)
    except Exception as e:
        log_debug(f"Exception interacting with minio: {str(e)}", key=request_id)

    redisClient.rpush("to-segmenter", request_id)
    log_info(f"Sent job to segmenter", key=request_id)
    return your_path.name

if not minioClient.bucket_exists("mp4files"):
    minioClient.make_bucket("mp4files")

# Watch for jobs
while True:
    try:
        job = redisClient.blpop("to-downloader", timeout = 0)[1]
        [request_id, url] = job.decode().split(':', 1)
        log_info(f"Starting downloader", key=request_id)
        downloadAudio(url, request_id)
        redisClient.set(f'{request_id}-status', "segmenting")
        redisClient.rpush("check-uniqueness", request_id)
    except Exception as exp:
        log_debug(f"Exception raised in receive-job loop: {str(exp)}", key=request_id)
    sys.stdout.flush()
    sys.stderr.flush()