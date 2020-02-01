import numpy as np
from multiprocessing import Queue
import threading

class Camera():
    def setup_camera(self):
        """To implement for specific cameras"""
        pass
        
    def __init__(self):
        self.photo_queue = Queue()
        self.camera_config_queue = Queue()
        self.setup_camera()
    
    def config_camera(self,command):
        """To implement"""
        pass
        
    def camera_config_worker(self):
        """this method is a worker that waits for the config queue"""
        while True:
            command = self.camera_config_queue.get()
            self.config_camera(command)

    def get_photo(self):
        """Blocking, returns a photo numpy array"""
        pass
        
    def worker(self):
        t = threading.Thread(target=self.camera_config_worker)
        t.start()
        self.index = 0
        while True:
            photo = self.get_photo()
            self.index+=1
            if photo is None:
                print("Photo failed")
            self.photo_queue.put([self.index,photo])
                
    def close(self):
        """
        shutdown camera, etc
        """
        pass    
