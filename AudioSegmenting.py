##https://github.com/jiaaro/pydub

from pydub import AudioSegment


def SegmentAudio():
    song = AudioSegment.from_mp3("abcde.mp3")
    # pydub does things in milliseconds
    ten_seconds = 10 * 1000

    first_10_seconds = song[:ten_seconds]

    last_5_seconds = song[-5000:]


if __name__ == '__main__':
    SegmentAudio()