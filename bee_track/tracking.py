import numpy as np
#from QueueBuffer import QueueBuffer
from bee_track.configurable import Configurable
#import threading
import retrodetect
from multiprocessing import Process, Queue, Value
import pickle
import os
import time
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
        
        
        
import numpy.polynomial.polynomial as poly
    
class TagAnalysis():
    def __init__(self, track):
        """
        Pass the photo and the 'track' dictonary (containing an 'x' and 'y' element in the dictionary).
        
        TODO: Assume patch is 40x40
        """
        x = track['x']
        y = track['y']

        #round to even pixels to ensure Bayer structure remains intact
        #self.x = (x//2)*2
        #self.y = (y//2)*2
        #self.img = img
        
        #TODO Assert the x and y are all in the img
        #self.tagimg = img[y-self.tagbox:y+self.tagbox,x-self.tagbox:x+self.tagbox]
        self.tagimg = track['patch']#'img[y-self.tagbox:y+self.tagbox,x-self.tagbox:x+self.tagbox]
        self.tagimg = self.tagimg[14:-14,14:-14] #bit smaller.
        if y%2==1:
            self.tagimg = self.tagimg[1:,:]
        if x%2==1:
            self.tagimg = self.tagimg[:,1:]


    def computefast(self):
        rgb = []
        rgb.append(np.mean(self.tagimg[::2,::2]))
        rgb.append(np.mean(self.tagimg[1::2,::2])/2+np.mean(self.tagimg[::2,1::2])/2)
        rgb.append(np.mean(self.tagimg[1::2,1::2]))       
        return np.array(rgb),np.zeros(3)
        
    def fitfocus(self):
        temp = self.tagimg.copy() #background subtraction
        temp[temp>3]=3
        meanimg = np.mean(self.tagimg,0)
        meanimg = meanimg - np.mean(temp)
        
        xs = np.arange(len(meanimg))
        meanimg[meanimg<0.01]=np.NaN
        xs = xs[~np.isnan(meanimg)]
        meanimg = meanimg[~np.isnan(meanimg)]
        if len(xs)<2:
            self.focuscoefs = [0,0,0]
            return np.array([0,0,0]), 0
        
        logmeans = np.log(meanimg)
        coefs = poly.polyfit(xs, logmeans, 2)
        
        self.focuscoefs = coefs
        
        preds = poly.polyval(xs, coefs)
        err = np.sum((preds - logmeans)**2)/np.sum((np.mean(logmeans)-logmeans)**2)
        return coefs, err
             
class TagAnalysisFromImage(TagAnalysis):
    def __init__(self, img, tagloc):
        
        track = {}
        track['x'] = tagloc[0]
        track['y'] = tagloc[1]
        track['patch'] = img[tagloc[1]-20:tagloc[1]+20,tagloc[0]-20:tagloc[0]+20]
        super().__init__(track)
                  
class Tracking(Configurable):
    def __init__(self,message_queue,photo_queue):
        super().__init__(message_queue)
        self.photo_queue = photo_queue
        self.tracking_queue = Queue()         
        self.photolist = [] #multiprocessing lists are really slow
        self.track = Value('i',0)
        self.info = False
        self.debug = False
        
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
                if self.debug: print("Starting Tracking...")
                if self.track.value>0:
                    contact, found, _ = retrodetect.detectcontact(self.photolist,len(self.photolist)-1)#,thresholds=[10,3,7])
                    recordtime(photoitem,'retrodetect algorithm complete')
                else:
                    contact = None
                    found = False
                    recordtime(photoitem,'retrodetect algorithm skipped')
                
                if self.debug: print(contact)
                recordtime(photoitem,'adding contact to track')
                
                photoitem['track']=contact
                
                if contact is not None:
                    for t in photoitem['track']:
                        ta = TagAnalysis(t)
                        rgb,rgbsd = ta.computefast()
                        t['rgb'] = rgb.tolist()
                        t['rgbsd'] = rgbsd.tolist()
                        coefs,err = ta.fitfocus()
                        t['focus'] = coefs.tolist()
                        t['focusfiterr'] = err
                recordtime(photoitem,'storing photoitem on photo_queue')                
                self.photo_queue.put(photoitem,index)                
                #TODO loop backwards until we reach earlier endofset
                
                
                #This is really slow TODO we need shared memory I guess here, the
                #problem is that the read object is a copy, so to edit it we need to put it back
                #the reading & putting it back is really slow. Maybe just save the track info elsewhere?
                if self.track.value>0:                    
                    oldphotoitem = self.photo_queue.read(index-1)
                    
                    if oldphotoitem is not None:
                        oldphotoitem['track'] = contact

                    self.photo_queue.put(oldphotoitem,index-1)

                    
                    #if oldphotoitem['record'] is not None:
                    #    triggertime_string = oldphotoitem['record']['triggertimestring']
                    #else:
                    #    triggertime_string = 'unknown'
                    ##filename = 'tracking_photo_object_%s_%04i.np' % (triggertime_string,index-1)
                    
                    
                    trackfilename = 'track_'+oldphotoitem['filename']                    
                    self.message_queue.put("Saved Tracking Photo: %s" % trackfilename)
                    pickle.dump(oldphotoitem,open(trackfilename,'wb'))

                if self.debug: print("Contact status")
                if self.debug: print(contact,found)
                if contact is not None:
                    if self.debug: print("Found potential target?")
                    self.tracking_queue.put(photoitem)
            recordtime(photoitem,'tracking complete')
            if self.debug: 
                if photoitem is not None:
                    if 'record' in photoitem:
                        if 'triggertimestring' in photoitem['record']:
                            print(photoitem['record']['triggertimestring'])
                        if 'times' in photoitem['record']:
                            prettyprinttimes(photoitem['record']['times'])
