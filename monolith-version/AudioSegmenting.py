##https://github.com/jiaaro/pydub
# pip install Shazamio ShazamAPI flask pydub pathlib pytube ffmpeg

from pydub import AudioSegment
import os
from pydub import AudioSegment
from pathlib import Path

source = './mp4Files/'
destination = './segmentedTracks/'
fifty_seconds = 50 * 1000

def segmentAudio(video_title):
    print('in AudioSegmenting')
    # pydub does things in milliseconds
    segmented_tracks = []

    mp4_song = AudioSegment.from_file(source+video_title+'.mp4', "mp4")

    seg_path = Path(destination+video_title+'/')
    if not os.path.exists(seg_path):
        os.makedirs(seg_path)
    
    videofile_len = len(mp4_song)
    print('videofile_len :: '+ str(videofile_len))

    for i in range(0,videofile_len,fifty_seconds):
        
        if i+fifty_seconds < videofile_len:
            segment = mp4_song[i:i+fifty_seconds]
        else:
            segment = mp4_song[i:videofile_len]
        if len(segment) > 0 :
            segment.export(out_f=destination+video_title+'/'+'segment'+str(i)+'.mp4',format='mp4')
            segmented_tracks.append('segment'+str(i)+'.mp4') 
        
    return segmented_tracks

''' 
first_10_seconds = song[:ten_seconds]
last_5_seconds = song[-5000:]
segment = song[:ten_seconds]
segment.export(out_f='./segmentedTracks/'+video_title[:-4]+'/'+'segment0.mp4',format='mp4')
segmented_tracks.append('segment0.mp4') 
'''