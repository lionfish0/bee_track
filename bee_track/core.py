from flask import Flask, make_response, jsonify
from bee_track.trigger import Trigger
from bee_track.camera_aravis import Aravis_Camera as Camera
from bee_track.tracking import Tracking
from multiprocessing import Process, Queue
import numpy as np
import io
from flask_cors import CORS
import base64
import sys
import os
from mem_top import mem_top
from datetime import datetime as dt
import subprocess
from queue import Empty
import retrodetect as rd

from flask_compress import Compress
app = Flask(__name__)
Compress(app)
CORS(app)

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

message_queue = None
camera = None
trigger = None
tracking = None

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

@app.route('/set/<string:component>/<string:field>/<string:value>')
def set(component,field,value):
    print(component,field,value)
    """TO DO: Secure?"""
    comp = None
    if component=='camera': comp = camera
    if component=='trigger': comp = trigger
    if comp is None: 
        return "%s component not available" % component
    comp.config_queue.put(['set',field,value])
    return "..."
    
@app.route('/get/<string:component>/<string:field>')
def get(component,field):
    print(component,field)
    """TO DO: Secure?"""
    comp = None
    if component=='camera': comp = camera
    if component=='trigger': comp = trigger
    if comp is None: 
        return "%s component not available" % component
    comp.config_queue.put(['get',field])
    return "..."    

@app.route('/getmessage')
def getmessage():
    try:
        msg = message_queue.get_nowait()
        return str(msg) +"\n"
    except Empty:
        return ""

@app.route('/startup')
def startup():
    global message_queue
    global trigger
    if trigger is not None:
        return "startup already complete"
    message_queue = Queue()
    trigger = Trigger(message_queue)
    t = Process(target=trigger.worker)
    t.start()
    #trigger.run.set()

    global camera
    camera = Camera(message_queue,trigger.record)

    t = Process(target=camera.worker)
    t.start()
    #global tracking
    #tracking = Tracking(message_queue,camera.photo_queue,trigger.record)
    #t = Process(target=tracking.worker)
    #t.start()
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
    
def lowresmaximg(img,blocksize=10):
    """
    Downsample image, using maximum from each block
    #from https://stackoverflow.com/questions/18645013/windowed-maximum-in-numpy
    """
    k = int(img.shape[0] / blocksize)
    l = int(img.shape[1] / blocksize)
    if blocksize==1:
        maxes = img
    else:
        maxes = img[:k*blocksize,:l*blocksize].reshape(k,blocksize,l,blocksize).max(axis=(-1,-3))
    return maxes
    
@app.route('/getrawtrackingimage/<int:number>')
def getrawtrackingimage(number):
    global camera
    try:
        print(camera.photo_queue.index)
    except Empty:
        return "No items"
    photoitem = camera.photo_queue.read(number)
    if photoitem is None:
        return "Failed"
    import time

    img = lowresmaximg(photoitem[1],blocksize=10).astype(int)
    return jsonify({'index':photoitem[0],'photo':img.tolist(),'record':photoitem[2]})

startup()
if __name__ == "__main__":
    app.run(host="0.0.0.0")

