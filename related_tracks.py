import asyncio
from shazamio import Shazam, Serialize


async def main():
    shazam = Shazam()
    track_id = 546891609
    related = await shazam.related_tracks(track_id=track_id, limit=2, start_from=2)
    # ONLY №3, №4 SONG
    for track in related['tracks']:
        song_info = {}
        song_info['title'] = track['title']
        song_info['Track ID'] = track['key']
        #309528203
        song_info['Sub title'] = track['subtitle']
        print(song_info)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
