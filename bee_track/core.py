from flask import Flask, make_response, jsonify
from bee_track.trigger import Trigger
from bee_track.camera_aravis import Aravis_Camera as Camera
#from bee_track.tracking import Tracking
import multiprocessing
import numpy as np
import io
from flask_cors import CORS
import base64
import sys
import os
from mem_top import mem_top
from datetime import datetime as dt
import subprocess

app = Flask(__name__)
CORS(app)

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

camera = None
trigger = None
tracking_workers = []

@app.route('/')
def hello_world():
    return 'root node of bee track API.'
    
@app.route('/setdatetime/<string:timestring>')
def setdatetime(timestring):
    #NOTE: This requires:
    #        sudo visudo
    # then add:
    #        pi ALL=(ALL) NOPASSWD: /bin/date
    d = dt.strptime(timestring,"%Y-%m-%dT%H:%M:%S")
    os.system('sudo /bin/date -s %s' % d.strftime("%Y-%m-%dT%H:%M:%S"))
    return "system time set successfully"

@app.route('/startup')
def startup():
    global trigger
    if trigger is not None:
        return "startup already complete"
    trigger = Trigger()
    t = multiprocessing.Process(target=trigger.worker)
    t.start()
    trigger.run.set()
    global camera
    camera = Camera()
    t = multiprocessing.Process(target=camera.worker)
    t.start()
    return "startup successful"
    
@app.route('/start')
def start():
    global trigger
    trigger.run.set()
    return "Collection Started"
    
@app.route('/stop')
def stop():
    global trigger
    trigger.run.clear()
    return "Collection Stopped"     

startup()
if __name__ == "__main__":
    app.run(host="0.0.0.0")

