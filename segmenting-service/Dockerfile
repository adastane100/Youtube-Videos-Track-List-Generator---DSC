FROM python:3.8

#ENTRYPOINT ["/bin/bash"]

# RUN apt-get update && apt-get install -y jq

# RUN apt-get update
# RUN apt install -y software-properties-common gcc
# RUN add-apt-repository -y ppa:deadsnakes/ppa

# RUN apt-get update
# RUN apt install -y python3.9 python3-distutils-extra python3-pip python3-apt

# ENV PYTHONPATH=/usr/bin/python3
# RUN apt-get update
RUN apt-get update && apt-get install -y ffmpeg

COPY segmentation.py /srv
COPY requirements.txt /srv

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /srv/requirements.txt

WORKDIR /srv

#ENTRYPOINT ["/bin/bash", "-l", "-c"]
CMD	["python3", "segmentation.py"]
