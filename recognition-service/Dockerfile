FROM python:3.8

RUN apt-get update && apt-get install -y ffmpeg

COPY recognition.py /srv
COPY requirements.txt /srv

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /srv/requirements.txt

WORKDIR /srv

CMD	["python3", "recognition.py"]
