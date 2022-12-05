# pip install Shazamio ShazamAPI flask pydub pathlib pytube ffmpeg
from ShazamAPI import Shazam
import asyncio
from shazamio import Shazam, Serialize
import RelatedTracks

destination = './segmentedTracks/'

shazam = Shazam()

async def identify_track(video_title, track):
    print('in recognize_song')
    #print(track_name)
    
    out = await shazam.recognize_song(destination+video_title+'/'+track)
    serialized = Serialize.full_track(out)
    #print(serialized)
    song_info = {}

    if serialized is not None and serialized.track is not None:
        song_info['title'] = serialized.track.title
        song_info['Track ID'] = serialized.track.key
        song_info['Sub title'] = serialized.track.subtitle
    return song_info


'''
def identify_track(video_title, track):
    song_info = {}
    try:
        mp3_file_content_to_recognize = open(destination+video_title+'/'+track, 'rb').read()
        shazam = Shazam(mp3_file_content_to_recognize)
        recognize_generator = shazam.recognizeSong()
        while True:
            one_record = next(recognize_generator)
            break
        
        song_info['title'] = one_record[1]['track']['title']
        song_info['Track ID'] = one_record[1]['track']['key']
        song_info['Sub title'] = one_record[1]['track']['subtitle']
    except:
        song_info = {}
    return song_info
'''
