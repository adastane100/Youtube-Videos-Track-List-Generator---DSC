import asyncio
from shazamio import Shazam, Serialize

shazam = Shazam()
async def find_related_tracks(track_id):
    print('in RelatedTracks')
    related_tracks = await shazam.related_tracks(track_id=track_id, limit=2, start_from=2)
    # ONLY №3, №4 SONG
    final_tracks = []
    for track in related_tracks['tracks']:
        song_info = {}
        song_info['title'] = track['title']
        song_info['Sub title'] = track['subtitle']
        final_tracks.append(song_info)
    return final_tracks
'''
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
'''
