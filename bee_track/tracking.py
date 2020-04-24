import numpy as np
#from QueueBuffer import QueueBuffer
from configurable import Configurable
#import threading
from retrodetect import detectcontact
from multiprocessing import Process, Queue
import pickle
from time import time
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
            starttime = time()        
            if photoitem is not None:
                if photoitem['img'] is not None:
                    photoitem['img'] = photoitem['img'].astype(np.float16)
            
            print("Got photo %d" % index)
            print('mainloop A',time()-starttime)
            starttime = time()
            self.photolist.append(photoitem)
            print('mainloop B',time()-starttime)
            starttime = time()
            if len(self.photolist)>10:
                self.photolist.pop(0)
            if photoitem['record']['endofset']:
                
                #contact, found = detectcontact(self.photo_queue,index)#,thresholds=[10,3,7])
                contact, found = detectcontact(self.photolist,len(self.photolist)-1)#,thresholds=[10,3,7])
                print('mainloop C',time()-starttime)
                starttime = time()
                print("===================================LENGTH:%d====================" % len(self.photolist))
                photoitem['track']=contact
                self.photo_queue.put(photoitem,index)
                print('mainloop D',time()-starttime)
                starttime = time()

                #TODO loop backwards until we reach earlier endofset
                oldphotoitem = self.photo_queue.read(index-1)
                oldphotoitem['track']=contact
                self.photo_queue.put(oldphotoitem,index-1)
                print('mainloop E',time()-starttime)
                starttime = time()
                triggertime_string = oldphotoitem['record']['triggertimestring']
                filename = 'tracking_photo_object_%s_%04i.np' % (triggertime_string,index-1)
                print('mainloop F',time()-starttime)
                starttime = time()
                self.message_queue.put("Saved Tracking Photo: %s" % filename)
                pickle.dump(oldphotoitem,open(filename,'wb'))
                print('mainloop G',time()-starttime)
                starttime = time()
                print("Contact status")
                #print(contact,found)
                if contact is not None:
                    self.tracking_queue.put(photoitem)
            print('mainloop H',time()-starttime)
            starttime = time()
