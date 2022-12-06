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
    print('in downloadFromYoutube')
    yt = YouTube(url_link)
    audioStream = yt.streams.filter(only_audio=True).first()
    out_file = audioStream.download(output_path=destination)
    your_path = Path(out_file)
    '''
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp4'
    os.rename(out_file, new_file)
    '''
    try:
        minioClient.put_object("mp4files", request_id, audioStream, -1, 1, "application/octet-stream")
    except Exception as e:
        log_debug(f"Exception interacting with minio: {str(e)}")

    redisClient.lpush("to-segmenter", request_id)
    return your_path.name

# Watch for jobs
while True:
    try:
        job = redisClient.blpop("to-downloader", timeout = 0)
        log_info(f"Found job {job}")
        [request_id, url] = job.split(':', 1)
        downloadAudio(url)
    except Exception as exp:
        log_debug(f"Exception raised in receive-job loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()