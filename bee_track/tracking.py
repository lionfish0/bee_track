import numpy as np
#from QueueBuffer import QueueBuffer
from configurable import Configurable
#import threading
from retrodetect import detectcontact
from multiprocessing import Process, Queue
import pickle

class Tracking(Configurable):
    def __init__(self,message_queue,photo_queue):
        super().__init__(message_queue)
        self.photo_queue = photo_queue
        self.tracking_queue = Queue()         

    def worker(self):
        self.index = 0
        while True:
            index,photoitem = self.photo_queue.pop()
            print("Got photo %d" % index)
            if photoitem[2]['endofset']:
                contact, found = detectcontact(self.photo_queue,index)#,thresholds=[10,3,7])
                photoitem.append(contact)
                self.photo_queue.put(photoitem,index)
                

                #TODO loop backwards until we reach earlier endofset
                oldphotoitem = self.photo_queue.read(index-1)
                oldphotoitem.append(contact)
                self.photo_queue.put(oldphotoitem,index-1)
                
                triggertime_string = oldphotoitem[2]['triggertimestring']
                filename = 'tracking_photo_object_%s_%04i.np' % (triggertime_string,index-1)
                self.message_queue.put("Saved Tracking Photo: %s" % filename)
                pickle.dump(oldphotoitem,open(filename,'wb'))
                
                
                print("Contact status")
                print(contact,found)
                if contact is not None:
                    self.tracking_queue.put(photoitem)
