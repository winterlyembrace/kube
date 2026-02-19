#!/usr/bin/python3

import logging
import os
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def index():
    return "OK"

port = int(os.environ.get("PORT", 5000))
print(f"Server started in port {port}")
app.run(host='0.0.0.0', port=port)



