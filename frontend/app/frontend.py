#!/usr/bin/env python3

##
## Flask REST server for music waveform analysis
##

from flask import Flask, render_template, request
import json, jsonpickle
from redis import Redis
import hashlib


# Initialize the Flask application
app = Flask(__name__)
r = Redis()

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return json.dumps({"Healthcheck": "Healthy"})


@app.route('/', methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        url = request.form['url']
        print(url)
    return render_template('input.html')

# start flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)