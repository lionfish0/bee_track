import numpy as np
#from QueueBuffer import QueueBuffer
from configurable import Configurable
#import threading
from retrodetect import detectcontact


class Tracking(Configurable):
    def __init__(self,message_queue,photo_queue):
        super().__init__(message_queue)
        self.photo_queue = photo_queue

    def worker(self):
        self.index = 0
        while True:
            index,photoitem = self.photo_queue.pop()
            print("Got photo %d" % index)
            if photoitem[2]['endofset']:
                contact = detectcontact(self.photo_queue,index)
                photoitem.append(contact)
                print("Contact status")
                print(contact)
