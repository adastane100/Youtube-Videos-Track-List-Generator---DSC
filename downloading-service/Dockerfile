FROM python:3.8

COPY download.py /srv
COPY requirements.txt /srv

RUN /usr/local/bin/python -m pip install --upgrade pip
RUN python -m pip install -r /srv/requirements.txt

WORKDIR /srv

CMD	["python3", "download.py"]
