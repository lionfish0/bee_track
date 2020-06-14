import numpy as np
from QueueBuffer import QueueBuffer
from configurable import Configurable
from multiprocessing import Value, Queue
import threading
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
        
    def __init__(self,message_queue,record):
        """
        Pass record list from trigger
        """
        super().__init__(message_queue)
        self.photo_queue = QueueBuffer(10) 
        self.record = record  
        self.index = Value('i',0)
        self.savephotos = True
        self.test = Value('b',False)
    def get_photo(self):
        """Blocking, returns a photo numpy array"""
        pass
        
    def worker(self):
        print("Camera worker started")
        self.setup_camera()
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
            #print("found")
            #print(self.photo_queue.len())
            #if (photo is not None) and (last_photo_object is not None) and (last_photo_object['img'] is not None):
                #print(rec['flash'])
                #print(last_photo_object['record']['direction'],rec['direction'])
                #print(last_photo_object['record']['triggertime'],rec['triggertime'])
                #if (last_photo_object['record']['direction']==rec['direction']) and (last_photo_object['record']['triggertime']>rec['triggertime']-0.1):
                #    rec['photoaverages'] = {'this':np.mean(photo['img'].flatten()),'last':np.mean(last_photo_object['img'].flatten())} #TODO I'm not sure this is used. delete?

            if photo is not None:
                #print(ascii_draw(photo[::10,::10]))
                photo = photo.astype(np.ubyte)
            photo_object = {'index':self.index.value,'img':photo,'record':rec}
            
            if self.test.value:
                if photo_object['img'] is not None:
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
            if self.savephotos:
                triggertime_string = photo_object['record']['triggertimestring']
                filename = 'photo_object_%s_%04i.np' % (triggertime_string,self.index.value)
                self.message_queue.put("Saved Photo: %s" % filename)
                pickle.dump(photo_object,open(filename,'wb'))
                #np.save(open('photo_%04i.np' % self.index.value,'wb'),photo.astype(np.ubyte))                
            self.index.value = self.index.value + 1
                
    def close(self):
        """
        shutdown camera, etc
        """
        pass    
