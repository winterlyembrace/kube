#!/usr/bin/python3

import logging
import os
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

string = 0

@app.route('/pingpong')
def index():
    string = 0 + 1 
    return f"Responded with {string}"


port = int(os.environ.get("PORT", 5050))
app.run(host='0.0.0.0', port=port)
