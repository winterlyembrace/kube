#!/usr/bin/python3

import logging
import os
import uuid
import time
from datetime import datetime, timezone
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

main_string = str(uuid.uuid4())[-5:]
print(f"Started with {main_string}")

@app.route('/')
def index():
    new_string = str(uuid.uuid4())[-5:]
    print(f"Responded with {new_string}") 
    return f"<h1>{main_string} : {new_string}</h1>"


port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)
