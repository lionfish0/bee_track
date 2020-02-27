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
            print("Got photo %d" % index)

