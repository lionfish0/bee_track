import numpy as np
from QueueBuffer import QueueBuffer
from configurable import Configurable
from multiprocessing import Value, Queue
import threading
import multiprocessing
import pickle

def ascii_draw(mat):
    symbols = np.array([s for s in ' .,:-=+*X#@@'])#[::-1]
    msg = ""
    mat = (11*mat/(np.max(mat)+1)).astype(int)
    mat[mat<0] = 0
    for i in range(0,len(mat),2):
        msg+=''.join(symbols[mat][i])+"\n"
    return msg

class Camera(Configurable):
    def setup_camera(self):
        """To implement for specific cameras"""
        pass
        
    def __init__(self,message_queue,record,cam_trigger,cam_id=None):
        """
        Pass record list from trigger
        """
        super().__init__(message_queue)
        self.photo_queue = QueueBuffer(10) 
        self.record = record
        self.label = multiprocessing.Array('c',100)
        self.index = Value('i',0)
        self.savephotos = Value('b',True)
        self.test = Value('b',False)
        self.cam_trigger = cam_trigger
        self.colour_camera = False
        self.cam_id = cam_id
        
    def camera_trigger(self):
        """implement whatever triggers the camera
        e.g. self.cam_trigger.wait()
        """
        pass
        
    #def trigger(self):
    #    print("Triggering Camera")
    #    self.cam_trigger.set()
        
    def get_photo(self):
        """Blocking, returns a photo numpy array"""
        pass
        
    def worker(self):
        print("Camera worker started")
        self.setup_camera()
        t = threading.Thread(target=self.camera_trigger)
        t.start()
        print("Camera setup complete")
        last_photo_object = None
        while True:
            #print("waiting for photo")
            
            photo = self.get_photo()
            #print("...")
            if photo is None:
                print("Photo failed")
            #print("Waiting for index to appear in record...")
            rec = None
            for r in self.record:
                if r['index'] == self.index.value:
                    rec = r
                    break
            if rec is None:
                print("WARNING: Failed to find associated photo record")
            
            
            photo_object = {'index':self.index.value,'record':rec}
            
            if self.colour_camera:
                colorphoto = photo
                if photo is not None:
                    photo = np.mean(photo,2)
                    photo = photo.astype(np.ubyte)
                    colorphoto = colorphoto.astype(np.ubyte)
                photo_object['colorimg'] = colorphoto                    
            photo_object['img'] = photo
            
            if self.test.value:
                if (photo_object['img'] is not None) and (photo_object['record'] is not None):
                    print("Test Signal Added")                
                    photo_object['img'] = photo_object['img'] + np.random.randint(0,2,photo_object['img'].shape)
                    if photo_object['record']['flash']:
                        photo_object['img'] = photo_object['img'] + np.random.randint(0,2,photo_object['img'].shape)
                        
                        y,x = np.unravel_index((photo_object['img']+np.random.randn(photo_object['img'].shape[0],photo_object['img'].shape[1]))[100:-100,100:-100].argmin(), photo_object['img'][100:-100,100:-100].shape)
                        #print(y,x)
                        photo_object['img'][y+100,x+100] = 255 #put it at minimum!
                    #photo_object['img'][100+np.random.randint(photo_object['img'].shape[0]-200),100+np.random.randint(photo_object['img'].shape['img']-200)]=255 #bright spot!
            
            last_photo_object = photo_object
            self.photo_queue.put(photo_object)
            if self.cam_id is not None:
                camidstr = self.cam_id[-11:]
            else:
                camidstr = ''
            if self.savephotos.value:
                if rec is not None:
                    triggertime_string = photo_object['record']['triggertimestring']
                    filename = 'photo_object_%s_%s_%s_%04i.np' % (camidstr,triggertime_string,self.label.value.decode('utf-8'),self.index.value)
                    self.message_queue.put("Saved Photo: %s" % filename)
                    pickle.dump(photo_object,open(filename,'wb'))
                else:
                    self.message_queue.put("FAILED TO FIND ASSOCIATED RECORD! NOT SAVED PHOTO")                    
                #np.save(open('photo_%04i.np' % self.index.value,'wb'),photo.astype(np.ubyte))                
            self.index.value = self.index.value + 1
                
    def close(self):
        """
        shutdown camera, etc
        """
        pass    
