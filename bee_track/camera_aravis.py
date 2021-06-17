import sys
import time
import numpy as np
from gi.repository import Aravis
import pickle
import ctypes
from multiprocessing import Queue
import threading
import gc
from datetime import datetime as dt
import os

from camera import Camera

class Aravis_Camera(Camera):
    def setup_camera(self):
        print("PROCESS ID: ", os.getpid())
        os.system("sudo chrt -f -p 1 %d" % os.getpid())
        Aravis.enable_interface ("Fake")
        self.aravis_camera = Aravis.Camera.new (None)
        self.aravis_camera.set_region(0,0,2048,1536) #2064x1544        
        self.aravis_camera.gv_set_packet_size(8000)
        
        ########## NEW CODE FOR 3D PRINTED BEE TRACKER WITH COLOUR CAM#######
        aravis_device = self.aravis_camera.get_device();
        aravis_device.set_string_feature_value("PixelFormat", "RGB8Packed")
        aravis_device.set_string_feature_value("TriggerMode", "On")
        aravis_device.set_string_feature_value("TriggerSource", "Software")
        aravis_device.set_string_feature_value("LineSelector", "Line2")
        aravis_device.set_boolean_feature_value("StrobeEnable", True)
        aravis_device.set_string_feature_value("LineMode", "Strobe")
        aravis_device.set_integer_feature_value("StrobeLineDelay", 100)
        aravis_device.set_integer_feature_value("StrobeLinePreDelay", 200)
        aravis_device.set_string_feature_value("LineSource", "ExposureStartActive")
        aravis_device.set_boolean_feature_value("LineInverter",True)
        #aravis_device.set_string_feature_value("ExposureTimeMode","UltraShort")   
        self.aravis_camera.set_exposure_time(140) #40
        self.aravis_camera.set_gain(1)
        ##########NEW CODE FOR SHORT EXPOSURE##########
        #aravis_device = self.aravis_camera.get_device();
        #aravis_device.set_string_feature_value("ExposureTimeMode","UltraShort")   
        #self.aravis_camera.set_exposure_time(7) #15 us
        #self.aravis_camera.set_gain(0)
        #self.aravis_camera.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_8)
        #self.aravis_camera.set_trigger("Line1")     
        #aravis_device.set_float_feature_value("LineDebouncerTime",5.0)
        
        ##########ORIGINAL CODE########################
        #self.aravis_camera.set_exposure_time(15) #1000000)#15 us
        #self.aravis_camera.set_gain(0)
        #self.aravis_camera.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_8)
        #self.aravis_camera.set_trigger("Line1")  
        
              
        self.payload = self.aravis_camera.get_payload()
        self.stream = self.aravis_camera.create_stream(None, None)
        if self.stream is None:
            print("Failed to construct stream")
            return
        self.aravis_camera.start_acquisition()
        for i in range(0,16):
            self.stream.push_buffer(Aravis.Buffer.new_allocate(self.payload))
        print("Ready")
    

    
    def camera_trigger(self):
        while True:
            print("WAITING FOR TRIGGER")
            self.cam_trigger.wait()
            print("Software Trigger...")
            self.aravis_camera.software_trigger()
            self.cam_trigger.clear()

    def get_photo(self):
        print(self.stream.get_n_buffers())
        print("waiting for photo...")
        #buffer = self.stream.timeout_pop_buffer(1000000) #blocking for one second
        buffer = self.stream.pop_buffer()
        print("got buffer...")
        if buffer is None:
            self.message_queue.put("Buffer read failed")
            print("buffer read failed")
            gc.collect()            
            return None
        status = buffer.get_status()
        if status!=0:
            print("Status Error")
            print(status)
            self.message_queue.put("Buffer Error: "+str(status))            
            self.stream.push_buffer(buffer) #return it to the buffer
            gc.collect()
            return None
        print("buffer ok")
        raw = np.frombuffer(buffer.get_data(),dtype=np.uint8).astype(float)
        self.stream.push_buffer(buffer)
        #return np.mean(np.reshape(raw,[1536,2048,3]),2) #turn to greyscale!
        return np.reshape(raw,[1536,2048,3])
        #return np.reshape(raw,[1536,2048])
        
    def close(self):
        """
        shutdown camera, etc
        TODO!
        """
        pass    

