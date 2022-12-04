#pip install pytube ffmpeg pydub ShazamAPI shazamio playsound

from pytube import YouTube
import os
from pathlib import Path

destination = './mp4Files/'

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
