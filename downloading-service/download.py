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
infoKey = "{}.rest.info".format(platform.node())
debugKey = "{}.rest.debug".format(platform.node())
def log_debug(message, key=debugKey):
    print("DEBUG:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{debugKey}:{message}")

def log_info(message, key=infoKey):
    print("INFO:", message, file=sys.stdout)
    redisClient.lpush('logging', f"{infoKey}:{message}")

# Function
def downloadAudio(url_link, request_id):
    log_info('in downloadFromYoutube')
    yt = YouTube(url_link)
    audioStream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
    log_info(f'All audioStreams: {yt.streams.filter(only_audio=True)}')
    out_file = audioStream.download(output_path=destination)
    your_path = Path(out_file)
    try:
        minioClient.fput_object("mp4files", request_id, your_path)
        log_info(f"Stored full mp4 file for {request_id} in minio")
    except Exception as e:
        log_debug(f"Exception interacting with minio: {str(e)}")

    redisClient.rpush("to-segmenter", request_id)
    log_info(f"Sent job to segmenter")
    return your_path.name

if not minioClient.bucket_exists("mp4files"):
    minioClient.make_bucket("mp4files")

# Watch for jobs
while True:
    try:
        job = redisClient.blpop("to-downloader", timeout = 0)[1]
        [request_id, url] = job.decode().split(':', 1)
        log_info(f"Request ID: {request_id}, url: {url}")
        downloadAudio(url, request_id)
        redisClient.set(f'{request_id}-status', "segmenting")
        redisClient.rpush("check-uniqueness", request_id)
    except Exception as exp:
        log_debug(f"Exception raised in receive-job loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()