import numpy as np
#from QueueBuffer import QueueBuffer
from configurable import Configurable
#import threading
import retrodetect
from multiprocessing import Process, Queue
import pickle
import os
from time import time
import datetime

def recordtime(photoitem,msg):
    """Debug function to add time of an event to the photoitem"""
    if photoitem is None: return
    if 'record' not in photoitem: return
    if photoitem['record'] is None: return
    if 'times' not in photoitem['record']: photoitem['record']['times'] = []
    timestring = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f")
    photoitem['record']['times'].append([msg,timestring])

def prettyprinttimes(timemsgs):
    for msg,ts in timemsgs:
        print("%30s: %15s" % (msg,ts))    
class Tracking(Configurable):
    def __init__(self,message_queue,photo_queue):
        super().__init__(message_queue)
        self.photo_queue = photo_queue
        self.tracking_queue = Queue()         
        self.photolist = [] #multiprocessing lists are really slow
    def worker(self):
        self.index = 0
        while True:
            index,photoitem = self.photo_queue.pop()
            recordtime(photoitem,'photo off queue') 
            if photoitem is not None:
                if photoitem['img'] is not None:
                    photoitem['img'] = photoitem['img'].astype(np.float16)
            recordtime(photoitem,'photo converted to float16')
            self.photolist.append(photoitem)


            if len(self.photolist)>10:
                self.photolist.pop(0)
            if photoitem['record'] is None: 
                print("WARNING: Record None")
                continue
            if photoitem['record']['endofset']:
                print("Starting Tracking...")
                
                contact, found, _ = retrodetect.detectcontact(self.photolist,len(self.photolist)-1)#,thresholds=[10,3,7])
                recordtime(photoitem,'retrodetect algorithm complete')
                print(contact)
                
                
                photoitem['track']=contact
                self.photo_queue.put(photoitem,index)

                #TODO loop backwards until we reach earlier endofset
                oldphotoitem = self.photo_queue.read(index-1)
                oldphotoitem['track']=contact
                self.photo_queue.put(oldphotoitem,index-1)
                if oldphotoitem['record'] is not None:
                    triggertime_string = oldphotoitem['record']['triggertimestring']
                else:
                    triggertime_string = 'unknown'
                filename = 'tracking_photo_object_%s_%04i.np' % (triggertime_string,index-1)

                #self.message_queue.put("Saved Tracking Photo: %s" % filename)
                #pickle.dump(oldphotoitem,open(filename,'wb'))

                print("Contact status")
                print(contact,found)
                if contact is not None:
                    print("Found potential target?")
                    self.tracking_queue.put(photoitem)
            recordtime(photoitem,'tracking complete')
            if photoitem is not None:
                if 'record' in photoitem:
                    if 'triggertimestring' in photoitem['record']:
                        print(photoitem['record']['triggertimestring'])
                    if 'times' in photoitem['record']:
                        prettyprinttimes(photoitem['record']['times'])
