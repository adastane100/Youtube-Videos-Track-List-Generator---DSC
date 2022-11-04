#pip install pytube ffmpeg pydub ShazamAPI shazamio playsound

from pytube import YouTube
import os

def dwnloadAudiofrmYtLink():
    yt = YouTube(str(input("Enter URL of youtube video: \n ")))
    #yt = YouTube('https://www.youtube.com/watch?v=8CifN2yqdg4')
    video = yt.streams.filter(only_audio=True).first()
    print("Enter the destination address (leave blank to save in current directory)")
    destination = str(input(" ")) or '.'
    #destination = ''
    out_file = video.download(output_path=destination)

    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)

    #print(yt.title + " has been successfully downloaded.")

    song_name = yt.title
    downloaded_song = new_file
    print(downloaded_song + " has been successfully downloaded.")


if __name__ == '__main__':
    dwnloadAudiofrmYtLink()