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
def downloadAudio(url_link):
    print('in downloadFromYoutube')
    yt = YouTube(url_link)
    video = yt.streams.filter(only_audio=True).first()
    #print("Enter the destination address (leave blank to save in current directory)")
    #destination = str(input(" ")) or '.'
    #destination = ""
    out_file = video.download(output_path=destination)
    '''
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp4'
    os.rename(out_file, new_file)
    '''
    your_path = Path(out_file)
    return your_path.name

# Watch for jobs
while True:
    try:
        job = redisClient.blpop("to-downloader", timeout = 0)
        log_info(f"Found job {job}")
    except Exception as exp:
        log_debug(f"Exception raised in receive-job loop: {str(exp)}")
    sys.stdout.flush()
    sys.stderr.flush()