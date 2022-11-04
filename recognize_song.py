## https://github.com/dotX12/ShazamIO

import asyncio
from shazamio import Shazam, Serialize


async def main():
    shazam = Shazam()
    out = await shazam.recognize_song("data/abcde.mp3")
    #print(out)
    serialized = Serialize.full_track(out)
    print(serialized)
    print('--------------------------')
    song_info = {}
    song_info['title'] = serialized.title
    song_info['Track ID'] = serialized.key
    #309528203
    song_info['Sub title'] = serialized.subtitle
    '''lyrics_sections = serialized.sections
    for section in lyrics_sections:
        if section['type'] == 'LYRICS':
            song_info['lyrics'] = section['text']'''
    print(song_info)
    


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
