import time
import datetime
import RPi.GPIO as GPIO
from configurable import Configurable
import multiprocessing

class Trigger(Configurable):
    def __init__(self,message_queue,t=2.0):
        super().__init__(message_queue)
        print("Initialising Trigger Control")
        self.manager = multiprocessing.Manager()
        self.flashselection = self.manager.list()
        self.index = 0
        self.record = self.manager.list()
        self.direction = 0
        self.flash_select_pins = [5]
        self.trigger_pin = 3
        self.flashselection.append(0)
        self.t = multiprocessing.Value('d',t)
        self.preptime = 0.33e-4
        self.triggertime = 0.33e-4 #this will end up at least 200us
        GPIO.setmode(GPIO.BOARD)
        for pin in self.flash_select_pins:
            GPIO.setup(pin, GPIO.OUT)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        time.sleep(0.5)
        for pin in self.flash_select_pins:
            GPIO.output(pin, False)
        GPIO.output(self.trigger_pin, False)
        print("Running")
        self.run = multiprocessing.Event()
    
    def trigger_camera(self,fireflash,endofset):
        """
            Send trigger to camera (and flash)
            fireflash = boolean: true=fire flash
            endofset = boolean: whether this is the last photo of a set (this will then tell the tracking system to look for the bee).
        """
        #if fireflash:
        #    print("Photo:    FLASH")
        #else:
        #    print("Photo: No Flash")
        
        if fireflash:
            for flash in self.flashselection:
                GPIO.output(self.flash_select_pins[flash],True)
        else:
            for pin in self.flash_select_pins:
                GPIO.output(pin, False)
        time.sleep(self.preptime)
        triggertime = time.time() #TODO Why are these two different?
        triggertimestring = datetime.datetime.now() #need to convert to string later
        GPIO.output(self.trigger_pin,True)
        time.sleep(self.triggertime)
        for pin in self.flash_select_pins:
            GPIO.output(pin, False)
        GPIO.output(self.trigger_pin, False)
        triggertimestring = triggertimestring.strftime("%Y%m%d_%H:%M:%S.%f")
        
        self.record.append({'index':self.index,'endofset':endofset,'direction':self.direction,'flash':fireflash,'flashselection':self.flashselection,'triggertime':triggertime,'triggertimestring':triggertimestring})
        self.index+=1


    def trigger_camera_flashnoflash(self):
        """
            Send trigger to camera (and flash)
        """
        print("Takaing photos")
        for pin in self.flash_select_pins:
            GPIO.output(pin, False)
        #time.sleep(self.preptime)
        triggertime1 = time.time()
        triggertimestring1 = datetime.datetime.now() #need to convert to string later
        GPIO.output(self.trigger_pin,True)
        time.sleep(0.0001) ##self.triggertime)
        #for pin in self.flash_select_pins:
        #    GPIO.output(pin, False)
        GPIO.output(self.trigger_pin, False)


        for flash in self.flashselection:
            GPIO.output(self.flash_select_pins[flash],True)
        #time.sleep(self.preptime)
        triggertimestring2 = datetime.datetime.now() #need to convert to string later
        GPIO.output(self.trigger_pin,True)
        time.sleep(0.0001) #self.triggertime)
        for pin in self.flash_select_pins:
            GPIO.output(pin, False)
        GPIO.output(self.trigger_pin, False)
        triggertime2 = time.time()

        triggertimestring1 = triggertimestring1.strftime("%Y%m%d_%H:%M:%S.%f")
        triggertimestring2 = triggertimestring2.strftime("%Y%m%d_%H:%M:%S.%f")
        
        self.record.append({'index':self.index,'endofset':False,'direction':self.direction,'flash':True,'flashselection':self.flashselection,'triggertime':triggertime1,'triggertimestring':triggertimestring1})
        self.index+=1
        self.record.append({'index':self.index,'endofset':True,'direction':self.direction,'flash':False,'flashselection':self.flashselection,'triggertime':triggertime2,'triggertimestring':triggertimestring2})
        self.index+=1
        print("trigger complete")
           
        
    def worker(self):   
        while (True):
            self.run.wait()
            #self.trigger_camera(False,False)

            self.trigger_camera(True,False)
            self.trigger_camera(False,True)

            #self.trigger_camera(False,False)
            #self.trigger_camera(True,True)
            #self.trigger_camera_flashnoflash()
            time.sleep(self.t.value-self.triggertime*3-self.preptime*3)
