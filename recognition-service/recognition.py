#!/usr/bin/env python3
## https://github.com/dotX12/ShazamIO

import asyncio
import os
from shazamio import Shazam, Serialize

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

shazam = Shazam()

# async def main():
#     shazam = Shazam()
#     out = await shazam.recognize_song("rickroll.mp4")
#     #print(out)
#     serialized = Serialize.full_track(out)
#     print(serialized)
#     print('--------------------------')
#     song_info = {}
#     song_info['title'] = serialized.track.title
#     song_info['Track ID'] = serialized.track.key
#     #309528203
#     song_info['Sub title'] = serialized.track.subtitle
#     '''lyrics_sections = serialized.sections
#     for section in lyrics_sections:
#         if section['type'] == 'LYRICS':
#             song_info['lyrics'] = section['text']'''
#     print(song_info)
    
# asyncio.run(main())

async def recognize(song):
    out = await shazam.recognize_song("rickroll.mp4")

def check_for_data():
    minioClient.fget_object('queue', f"{hash}.mp3", f"/data/input/{hash}.mp3")

if __name__ == "__main__":
    while(1):
        next_sample = check_for_data()
        asyncio.run(recognize(next_sample))
