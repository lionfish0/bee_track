import numpy as np
from QueueBuffer import QueueBuffer
from configurable import Configurable
import threading

class Tracking(Configurable):
    def __init__(self,message_queue,photo_queue):
        super().__init__(message_queue)
        self.photo_queue = photo_queue

    def worker(self):
        self.index = 0
        while True:
            index,photo = self.photo_queue.get()
            print("Waiting for index to appear in record...")
            for r in self.record:
                if r['index'] == index:
                    photo.append(r)
                    
            print(index)
            print("---")
