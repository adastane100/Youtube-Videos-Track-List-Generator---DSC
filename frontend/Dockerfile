FROM python:3.8

RUN mkdir /app
COPY app /app

RUN /usr/local/bin/python -m pip install --upgrade pip
RUN python -m pip install -r /app/requirements.txt

ENV	FLASK_PORT 5000
ENV PYTHONPATH /app
EXPOSE 5000
WORKDIR /

CMD	FLASK_APP=app flask run -h 0.0.0.0
