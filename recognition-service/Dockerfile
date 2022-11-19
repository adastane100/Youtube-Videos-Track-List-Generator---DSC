FROM python:3.8

COPY recognition-service /srv

RUN /usr/local/bin/python -m pip install --upgrade pip
RUN python -m pip install -r /app/requirements.txt

WORKDIR /srv

CMD	["python3" "recognition.py"]
