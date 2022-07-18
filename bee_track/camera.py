import numpy as np
from QueueBuffer import QueueBuffer
from configurable import Configurable
from multiprocessing import Value, Queue
import threading
import multiprocessing
import pickle
import datetime

def ascii_draw(mat):
    symbols = np.array([s for s in ' .,:-=+*X#@@'])#[::-1]
    msg = ""
    mat = (11*mat/(np.max(mat)+1)).astype(int)
    mat[mat<0] = 0
    for i in range(0,len(mat),2):
        msg+=''.join(symbols[mat][i])+"\n"
    return msg

def downscale(img,blocksize):
    k = int(img.shape[0] / blocksize)
    l = int(img.shape[1] / blocksize)    
    maxes = img[:k*blocksize,:l*blocksize].reshape(k,blocksize,l,blocksize).max(axis=(-1,-3)) #from https://stackoverflow.com/questions
    return maxes


def downscalecolour(img,blocksize):
    k = int(img.shape[0] / blocksize)
    l = int(img.shape[1] / blocksize)    
    maxes = img[:k*blocksize,:l*blocksize,:].reshape(k,blocksize,l,blocksize,3).max(axis=(-2,-4)) #from https://stackoverflow.com/questions
    return maxes
    
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
        self.fastqueue = Value('b',False) ###THIS WILL STOP PROCESSING
        self.test = Value('b',False)
        self.cam_trigger = cam_trigger
        self.colour_camera = Value('b',False)
        self.return_full_colour = Value('b',False) #if it returns RGB or just raw data.
        self.cam_id = cam_id
        self.config_camera_queue = Queue()
        self.info = False
        self.debug = False

    def config_camera(self, param, value):
        """Implement for specific cameras
        param = 'exposure', 'delay' or 'predelay'
        """
        self.config_camera_queue.put([param,value])
        
        
    def camera_config_worker(self):
        """implements whatever configures the camera (E.g. setting the exposure)"""
        pass
        
    def camera_trigger(self):
        """implement whatever triggers the camera
        e.g. self.cam_trigger.wait()
        """
        pass
        
    #def trigger(self):
    #    print("Triggering Camera")
    #    self.cam_trigger.set()
        
    def get_photo(self,getraw=False):
        """Blocking, returns a photo numpy array"""
        pass
        
    def worker(self):
        print("Camera worker started")
        self.setup_camera()
        t = threading.Thread(target=self.camera_trigger)
        t.start()
        t = threading.Thread(target=self.camera_config_worker)
        t.start()
        print("Camera setup complete")
        last_photo_object = None
        while True:
            #print("waiting for photo")
            
            if self.debug: print('Blocking started for getting photo at %s' % (datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f")))
            photo = self.get_photo(getraw=self.fastqueue.value)
            print(".",end="",flush=True)
            if self.debug: print('Got photo at %s' % (datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f")))

            if photo is None:
                print("Photo failed")

            rec = None
            for r in self.record:
                if r['index'] == self.index.value:
                    rec = r
                    break
            if rec is None:
                print("WARNING: Failed to find associated photo record")
            
            
            photo_object = {'index':self.index.value,'record':rec}
            
            if bool(self.return_full_colour.value):
                if self.debug: print('generating greyscale copy at %s' % (datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f")))
                colorphoto = photo
                if photo is not None:
                    if self.fastqueue.value:         
                        #photo = downscale(np.mean(photo,2),10)
                        photo = np.mean(photo[::10,::10,:],2)
                    else:
                        photo = np.mean(photo,2)
                    
                    if self.debug: print('averaging completed at       %s' % (datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f")))
                    photo = photo.astype(np.ubyte)
                    if self.debug: print('type conversion completed at %s' % (datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f")))
                    if not self.fastqueue.value: colorphoto = colorphoto.astype(np.ubyte)
                    if self.debug: print('colour type conv completed at%s' % (datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f")))
                photo_object['colorimg'] = colorphoto
                if self.debug: print('greyscale copy completed at %s' % (datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f")))                
            else:
                if photo is not None:
                    photo = photo.astype(np.ubyte)
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
            
            
            if self.debug: print('starting to push photo to queue at %s' % (datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f")))
            if self.fastqueue.value: #note we don't even pass on a colour image!
                #lowres_photo_object = {item:photo_object[item] for item in ['index','record']} #just copy across minimal key items
                lowres_photo_object = {item:photo_object[item] for item in ['index','record','img']} #just copy across minimal key items
                #lowres_img = downscale(photo_object['img'],10)
                #lowres_photo_object['img'] = lowres_img
                self.photo_queue.put(lowres_photo_object)
            else:
                self.photo_queue.put(photo_object)
            if self.cam_id is not None:
                camidstr = self.cam_id[-11:]
            else:
                camidstr = ''
            if self.savephotos.value:
                if rec is not None:
                    triggertime_string = photo_object['record']['triggertimestring']
                    filename = 'photo_object_%s_%s_%s_%04i.np' % (camidstr,triggertime_string,self.label.value.decode('utf-8'),self.index.value)
                    photo_object['filename'] = filename
                    self.message_queue.put("Saved Photo: %s" % filename)
                    if self.debug: print('starting save at %s' % (datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f")))
                    pickle.dump(photo_object,open(filename,'wb'))
                    if self.debug: print('finished save at %s' % (datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f")))                    
                    if self.info: print("Saved photo as %s" % filename)
                else:
                    filename = 'photo_object_%s_%s.np' % (camidstr,datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S.%f"))                   
                    self.message_queue.put("FAILED TO FIND ASSOCIATED RECORD! SAVED AS %s")
                    photo_object['filename'] = filename
                    pickle.dump(photo_object,open(filename,'wb'))
                    self.message_queue.put("Saved Photo: %s" % filename)                  
                #np.save(open('photo_%04i.np' % self.index.value,'wb'),photo.astype(np.ubyte))   
            print("Incrementing camera index, from %d" % self.index.value)             
            self.index.value = self.index.value + 1
                
    def close(self):
        """
        shutdown camera, etc
        """
        pass    
