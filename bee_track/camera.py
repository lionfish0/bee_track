import numpy as np
from QueueBuffer import QueueBuffer
from configurable import Configurable
from multiprocessing import Value, Queue
import threading

class Camera(Configurable):
    def setup_camera(self):
        """To implement for specific cameras"""
        pass
        
    def __init__(self,message_queue,record):
        """
        Pass record list from trigger
        """
        super().__init__(message_queue)
        self.photo_queue = QueueBuffer(20) 
        self.record = record  
        self.index = Value('i',0)
    def get_photo(self):
        """Blocking, returns a photo numpy array"""
        pass
        
    def worker(self):
        print("Camera worker started")
        self.setup_camera()
        print("Camera setup complete")
        while True:
            print("waiting for photo")
            photo = self.get_photo()
            print("...")
            if photo is None:
                print("Photo failed")
            print("Waiting for index to appear in record...")
            rec = None
            for r in self.record:
                if r['index'] == self.index.value:
                    rec = r
                    break
            print("found")
            self.photo_queue.put([self.index.value,photo,rec])
            self.index.value = self.index.value + 1
            
                
    def close(self):
        """
        shutdown camera, etc
        """
        pass    
