## https://github.com/dotX12/ShazamIO

import asyncio
from shazamio import Shazam, Serialize
destination = './mp4Files/'


async def identify_track():
    print('in recognize_song')
    #print(track_name)
    shazam = Shazam()

    seg = './segmentedTracks/Charlie Puth - Attention [Official Video]/'
    ntrack = 'segment0.mp4'
    #track_path = destination+track_name+'.mp4'
    out = await shazam.recognize_song(seg+ntrack)
    print(out)
    serialized = Serialize.full_track(out)
    song_info = {}
    song_info['title'] = serialized.track.title
    song_info['Track ID'] = serialized.track.key
    song_info['Sub title'] = serialized.track.subtitle
    '''lyrics_sections = serialized.sections
    for section in lyrics_sections:
        if section['type'] == 'LYRICS':
            song_info['lyrics'] = section['text']'''
    #print(song_info)
    print(song_info['title'])
    #return song_info['title']
    


loop = asyncio.get_event_loop()
loop.run_until_complete(identify_track())

