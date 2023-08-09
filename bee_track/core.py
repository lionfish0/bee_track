from flask import Flask, make_response, jsonify
from bee_track.trigger import Trigger
from bee_track.rotate import Rotate
from bee_track.camera_aravis import Aravis_Camera as Camera
from bee_track.camera_aravis import getcameraids
from bee_track.tracking import Tracking
from bee_track.file_manager import File_Manager
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
import multiprocessing
from battery import read_batteries
from flask_compress import Compress
app = Flask(__name__)
Compress(app)
CORS(app)
from glob import glob
import pickle

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

message_queue = None
cameras = [] #None
trigger = None
rotate = None
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

def addtoconfigvals(component,field,value):
    try:
        configvals = pickle.load(open('configvals.pkl','rb'))
        if component not in configvals: configvals[component] = {}
        #if field not in configvals[component]:
        configvals[component][field] = value
    except: # FileNotFoundError:
        configvals = {}
    pickle.dump(configvals,open('configvals.pkl','wb'))
    
@app.route('/set/<string:component>/<string:field>/<string:value>')
def set(component,field,value):
    print(component,field,value)
    """TO DO: Secure?"""
    addtoconfigvals(component,field,value)
    
    comp = None
    if component=='camera': comp = cameras
    if component=='trigger': comp = [trigger]
    if component=='rotate': comp = rotate
    if component=='tracking': comp = [tracking]
    if comp is None: 
        return "%s component not available" % component
    for c in comp:
        c.config_queue.put(['set',field,value])
    return "..."


def setfromconfigvals():
    try:
        configvals = pickle.load(open('configvals.pkl','rb'))
        for component,fields in configvals.items():
            for field,value in fields.items():
                set(component,field,value)
    except: # FileNotFoundError:
        pass

@app.route('/get/<string:component>/<string:field>')
def get(component,field):
    print(component,field)
    """TO DO: Secure?"""
    comp = None
    if component=='camera': comp = cameras[0]
    if component=='trigger': comp = trigger
    if component=='rotate': comp = rotate
    if comp is None: 
        return "%s component not available" % component
    comp.config_queue.put(['get',field])
    return "..."    

@app.route('/getdiskfree')
def getdiskfree():
    return str(disk_usage('/').free)

@app.route('/getbattery')
def getbattery():
    batstr = read_batteries()
    with open("battery_status.txt", "a") as battery:
        battery.write(batstr)
    return batstr
    
@app.route('/config/<string:instruction>/<int:value>')
def configcam(instruction,value):
    for cam in cameras:
        cam.config_camera_queue.put([instruction,value])
    return "Done"
    
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

import socket
def get_ip():
    #From https://stackoverflow.com/a/28950776
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def share_ip():
    import requests as req
    ipaddr = get_ip()
    try:
        print("Trying to get our ID")
        devid = open('device_id.txt','r').read()
    except FileNotFoundError:
        print("Failed to find ID")
        devid = '9999'
    print("Using ID: %s" % devid)
    try:
        print("Trying to access remote server")
        url = 'http://michaeltsmith.org.uk:5000/set/%s/%s' % (devid.strip(),ipaddr)
        print(url)
        req.get(url,timeout=10) #tries to share IP address on server
        #
        ##temporary test...
        #import time
        #time.sleep(10) #simulate delay...
    except:
        print("FAILED")
        pass


@app.route('/setid/<int:id>')
def setid(id):
    print("Updating device ID: %s" % str(id))
    open('device_id.txt','w').write(str(id))
    print("Updated")
    return "Done"

@app.route('/startup')
def startup():
    global message_queue
    global trigger
    global rotate
    global cameras
    global tracking
    global cam_trigger
    global rotate
    global file_manager
    
    if trigger is not None:
        return "startup already complete"
    message_queue = Queue()
    
    file_manager = File_Manager(message_queue)
    
    cam_trigger = multiprocessing.Event()

    trigger = Trigger(message_queue,cam_trigger)
    t = Process(target=trigger.worker)
    t.start()
    
    cam_ids = getcameraids()
    
    for cam_id in cam_ids:
        camera = Camera(message_queue,trigger.record,cam_trigger,cam_id=cam_id)
        cameras.append(camera)
        t = Process(target=camera.worker)
        t.start()
        import time
        time.sleep(1)
    assert len(cameras)>0
    #we'll make the tracking camera the first greyscale one if there is one, otherwise the 0th one.
    usecam=cameras[0]
    print("looking for camera to use for tracking...")
    for cam in cameras:
        print("Cam...")
        print(cam.colour_camera.value)
        if cam.colour_camera.value==0:
            print("Not colour cam")
            usecam = cam
            #break
    tracking = Tracking(message_queue,cam.photo_queue)
    t = Process(target=tracking.worker)
    t.start()
    
    rotate = Rotate(message_queue)
    t = Process(target=rotate.worker)
    t.start()
    
    share_ip()
    setfromconfigvals()
    return "startup successful"
    
@app.route('/start')
def start():
    #global trigger
    nextindex = max([camera.index.value for camera in cameras]+[trigger.index.value])
        
    #reset indicies
    for camera in cameras:
        camera.index.value = nextindex
    trigger.index.value = nextindex

    #for camera in cameras:
    #    print(camera.index.value)
    #print(trigger.index.value)

    trigger.run.set()
    return "Collection Started"
    
@app.route('/stop')
def stop():
    #global trigger
    trigger.run.clear()
    return "Collection Stopped"

@app.route('/compress') ##TODO ADDED ZIP AND COMPRESS!!
def compress():
    file_manager.compress_photos()
    return "In progress"

@app.route('/rotatetoangle/<float:targetangle>')
def rotatetoangle(targetangle):
    rotate.targetangle.value = targetangle
    rotate.rotation.set()
    return "Rotation Started"

@app.route('/setlabel/<string:label>')
def setlabel(label):
    for camera in cameras:
        camera.label.value = bytes(label[1:],'utf-8')
    return "Set to %s" % label[1:]
       
@app.route('/reboot')
def reboot():
    print("Reboot")
    os.system('sudo reboot')
    return "Reboot Initiated"

def runcommand(cmnd):
    #From https://stackoverflow.com/questions/16198546/get-exit-code-and-stderr-from-subprocess-call
    try:
        output = subprocess.check_output(
            cmnd, stderr=subprocess.STDOUT, shell=True, timeout=10,
            universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        return "Failed Update: "+str(exc.returncode)+str(exc.output)
    else:
        return "Updated: "+str(output)
        
def runcommandnowait(cmnd):
    try:
        subprocess.Popen(cmnd, shell=True)
    except subprocess.CalledProcessError as exc:        
        return "Failed: "+str(exc.returncode)+str(exc.output)
    else:
        return "Command Called"      
    

    
@app.route('/zip') ##TODO ADDED ZIP AND COMPRESS!!
def zip():
    import datetime
    now = datetime.datetime.now()

    filename = now.strftime("%Y%m%d%H%M%S.zip")
    print("Zip")
    import os
    try:
        os.mkdir('zips') #somewhere to store the zips.
    except FileExistsError:
        print("Woah")

    runcommandnowait('zip -mT zips/%s *.np' % filename)
    print("Started")
    return "Zipping Started"

from threading import Thread
from time import sleep

def threaded_function():
    while (True):
        print("running auto zip")
        #zip() #disabled
        sleep(600)

thread = Thread(target = threaded_function)
thread.start()

#import threading
#ticker = threading.Event()
#while not ticker.wait(600):
#    print("AUTO ZIP")
#    zip()

@app.route('/update')
def update():
    #res = ""
    #os.system('whoami'))
    #_,res += os.system('git pull')
    #res = subprocess.check_output(['git pull'])
    res = runcommand('git pull')
    return "Update Complete: \n"+res
    
@app.route('/test/<int:enable>')
def test(enable):
    #global camera
    for camera in cameras:
        camera.test.value = bool(enable)
    if cameras[0].test.value: return "Testing Enabled"
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
        return str(cameras[0].index.value-1) #gets index of current image...
        #return str(cameras[0].photo_queue.len())
    except Empty:
        return "No items"

def getimagewithindex(photo_queue,idx):
    for i in range(photo_queue.len()-1,-1,-1):
        item = photo_queue.read(i)
        if item is None: continue
        if item['index']==idx:
            return item
    return None
    
@app.route('/getimage/<int:number>/<int:camera_id>')
@app.route('/getimage/<int:number>')
def getimage(number,camera_id=0):
    #global camera
    #global message_queue
    #photoitem = cameras[camera_id].photo_queue.read(number)
    photoitem = getimagewithindex(cameras[camera_id].photo_queue,number)
    if photoitem is None:
        message_queue.put("Photo %d doesn't exist" % number)
        return "Failed"
    if photoitem['img'] is None:
        message_queue.put("Photo %d failed" % number)
        return "Failed"
    img = lowresmaximg(photoitem['img'],blocksize=5).astype(int)
    if (len(photoitem)>3) and ('track' in photoitem) and (photoitem['track'] is not None):
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
    #global tracking
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
        
@app.route('/addtest')
def addtestdata():
    for fn in sorted(glob('*.np')):
        print(fn)
        try:
            photo = np.load(fn,allow_pickle=True)
        except EOFError:
            print("file might be empty")
            continue
        except OSError:
            print("File might not be a pickle file")
            continue
        if 'img' not in photo: continue
        if photo['img'] is None: continue
        cameras[0].photo_queue.put(photo)
    return "Done"

@app.route('/getimagecentre/<int:number>/<int:camera_id>')
@app.route('/getimagecentre/<int:number>')
def getimagecentre(number,camera_id=0):
    #global camera
    #photoitem = cameras[camera_id].photo_queue.read(number)
    photoitem = getimagewithindex(cameras[camera_id].photo_queue,number)
    if photoitem is None:
        #global message_queue
        message_queue.put("Photo %d doesn't exist" % number)
        return "Failed"
    if photoitem['img'] is None:
        #global message_queue
        message_queue.put("Photo %d failed" % number)
        return "Failed"
    middle = [int(photoitem['img'].shape[0]/2),int(photoitem['img'].shape[1]/2)]
    img = (photoitem['img'][middle[0]-150:middle[0]+150,middle[1]-150:middle[1]+150]).astype(int)
    return jsonify({'index':photoitem['index'],'photo':img.tolist(),'record':photoitem['record']})


startup()
if __name__ == "__main__":
    app.run(host="0.0.0.0")

