# pip install Shazamio ShazamAPI flask pydub pathlib pytube ffmpeg
from ShazamAPI import Shazam
destination = './segmentedTracks/'


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
