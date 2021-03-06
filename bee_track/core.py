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
from psutil import disk_usage
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

@app.route('/getdiskfree')
def getdiskfree():
    return str(disk_usage('/').free)
    
@app.route('/getmessage')
def getmessage():
    msgs = ""
    try:
        
        while (True):
            msg = message_queue.get_nowait()
            msgs = msgs + str(msg) +"\n"
        #return msgs
    except Empty:
        return msgs

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
    
    global tracking
    tracking = Tracking(message_queue,camera.photo_queue)
    t = Process(target=tracking.worker)
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
    
    
@app.route('/reboot')
def reboot():
    os.system('sudo reboot')
    
@app.route('/test/<int:enable>')
def test(enable):
    global camera
    camera.test.value = bool(enable)
    if camera.test.value: return "Testing Enabled"
    else: return "Testing Disabled"
    
    
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

@app.route('/getimagecount')
def getimagecount():
    try:
        return str(camera.index.value) #camera.photo_queue.len())
    except Empty:
        return "No items"

@app.route('/getimage/<int:number>')
def getimage(number):
    global camera
    photoitem = camera.photo_queue.read(number)
    if photoitem is None:
        global message_queue
        message_queue.put("Photo %d doesn't exist" % number)
        return "Failed"
    if photoitem['img'] is None:
        global message_queue
        message_queue.put("Photo %d failed" % number)
        return "Failed"
    img = lowresmaximg(photoitem['img'],blocksize=5).astype(int)
    if (len(photoitem)>3) and (photoitem['track'] is not None):
        newtracklist = []
        for track in photoitem['track']:
            track['patch']=track['patch'].tolist() #makes it jsonable
            track['searchpatch']=track['searchpatch'].tolist() #makes it jsonable
            track['mean']=float(track['mean'])
            track['searchmax']=float(track['searchmax'])
            track['centremax']=float(track['centremax'])
            track['x']=int(track['x'])
            track['y']=int(track['y'])
            newtracklist.append(track)
    else:
        newtracklist = []
    return jsonify({'index':photoitem['index'],'photo':img.tolist(),'record':photoitem['record'],'track':newtracklist})

@app.route('/getcontact')
def getcontact(): #TODO this is mostly done by getimage, maybe just return an index?
    global tracking
    try:
        photoitem = tracking.tracking_queue.get_nowait()
        if photoitem['img'] is not None:
            img = lowresmaximg(photoitem['img'],blocksize=5).astype(int).tolist()
        else:
            img = None
        newtracklist = []
        for trackoriginal in photoitem['track']:
            track = trackoriginal.copy()
            track['patch']=track['patch'].tolist() #makes it jsonable
            track['searchpatch']=track['searchpatch'].tolist() #makes it jsonable
            track['mean']=float(track['mean'])
            track['searchmax']=float(track['searchmax'])
            track['centremax']=float(track['centremax'])            
            track['x']=int(track['x'])
            track['y']=int(track['y']) 
            newtracklist.append(track)       
        return jsonify({'index':photoitem['index'],'photo':img,'record':photoitem['record'],'track':newtracklist})
    except Empty:
        return jsonify(None)
        

@app.route('/getimagecentre/<int:number>')
def getimagecentre(number):
    global camera
    photoitem = camera.photo_queue.read(number)
    if photoitem is None:
        global message_queue
        message_queue.put("Photo %d doesn't exist" % number)
        return "Failed"
    if photoitem['img'] is None:
        global message_queue
        message_queue.put("Photo %d failed" % number)
        return "Failed"
    middle = [int(photoitem['img'].shape[0]/2),int(photoitem['img'].shape[1]/2)]
    img = (photoitem['img'][middle[0]-150:middle[0]+150,middle[1]-150:middle[1]+150]).astype(int)
    return jsonify({'index':photoitem['index'],'photo':img.tolist(),'record':photoitem['record']})


startup()
if __name__ == "__main__":
    app.run(host="0.0.0.0")

