FROM python:3.8

RUN apt-get update && apt-get install -y ffmpeg

COPY segmentation.py /srv
COPY requirements.txt /srv

RUN mkdir /srv/mp4files
RUN mkdir /srv/segmented

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /srv/requirements.txt

WORKDIR /srv

CMD	["python3", "segmentation.py"]
