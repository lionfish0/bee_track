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

def getcameraids():
    Aravis.update_device_list()
    n_cams = Aravis.get_n_devices()
    print("%d cameras found" % n_cams)
    ids = []
    for i in range(n_cams):
        dev_id = Aravis.get_device_id(i)
        print("Found: %s" % dev_id)
        ids.append(dev_id)
    return ids
    
class Aravis_Camera(Camera):
    def setup_camera(self):
        print("PROCESS ID: ", os.getpid())
        os.system("sudo chrt -f -p 1 %d" % os.getpid())
        Aravis.enable_interface ("Fake")
        self.aravis_camera = Aravis.Camera.new (self.cam_id)
        self.aravis_camera.set_region(0,0,2048,1536) #2064x1544        
        self.aravis_camera.gv_set_packet_size(8000)
        self.aravis_camera.gv_set_packet_delay(40000) #np.random.randint(10000))
        print("!!!!")
        print(self.aravis_camera.gv_get_packet_delay())
        
        #self.aravis_camera.gv_set_stream_options(Aravis.GvStreamOption.NONE)
        
        aravis_device = self.aravis_camera.get_device();
        ####print(aravis_device.get_string_feature_value('MaxImageSize'))
        
        if self.aravis_camera.get_pixel_format_as_string()=='Mono8':
            self.colour_camera = False
            pass
        else:
            self.colour_camera = True
            aravis_device.set_string_feature_value("PixelFormat", "RGB8Packed")
            
        #Triggering the camera:
        #  Software trigger...    
        #aravis_device.set_string_feature_value("TriggerMode", "On")
        #aravis_device.set_string_feature_value("TriggerSource", "Software")
        #  Hardware trigger...
        ##print(aravis_device.get_available_trigger_sources())
        ##self.aravis_camera.set_trigger("Line1")
        aravis_device.set_string_feature_value("TriggerMode", "On")
        aravis_device.set_string_feature_value("TriggerSource", "Line0")
        
        #Triggering the flash...
        #if triggerflash: #this camera might not be the one doing the triggering
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
        
        ###
        
        #self.stream.set_property('packet-timeout',5000)
        #self.stream.set_property('frame-retention',250000)
        #self.stream.set_property('packet-request-ratio',0.1)        
        #self.stream.set_property('socket-buffer',Aravis.GvStreamSocketBuffer.FIXED)
        #self.stream.set_property('socket-buffer-size',5000000)
        #self.stream.set_property('packet-resend',Aravis.GvStreamPacketResend.ALWAYS)
        
        ###
        
        
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
        print(self.cam_id,self.stream.get_n_buffers())
        print(self.cam_id,"waiting for photo...")
        buffer = self.stream.pop_buffer()
        
        #buffer = None
        #while buffer is None:
        #    print("...")
        #    time.sleep(np.random.rand()*1) #wait between 0 and 1 second
        #    buffer = self.stream.timeout_pop_buffer(1000) #blocking for 1ms
           
        print(self.cam_id,"got buffer...")
        if buffer is None:
            self.message_queue.put(self.cam_id+" Buffer read failed")
            print(self.cam_id,"buffer read failed")
            gc.collect()            
            return None
        status = buffer.get_status()
        if status!=0:
            print(self.cam_id,"Status Error")
            print(self.cam_id,status)
            self.message_queue.put(self.cam_id+" Buffer Error: "+str(status))            
            self.stream.push_buffer(buffer) #return it to the buffer
            gc.collect()
            return None
        print(self.cam_id,"buffer ok")
        raw = np.frombuffer(buffer.get_data(),dtype=np.uint8).astype(float)
        self.stream.push_buffer(buffer)
        if self.colour_camera:
            return np.reshape(raw,[1536,2048,3])
        else:
            return np.reshape(raw,[1536,2048])
        
    def close(self):
        """
        shutdown camera, etc
        TODO!
        """
        pass    

