import time
import datetime
import RPi.GPIO as GPIO
from configurable import Configurable
import multiprocessing

class Trigger(Configurable):
    def __init__(self,message_queue,cam_trigger,t=2.0):
        super().__init__(message_queue)
        print("Initialising Trigger Control")  
        self.cam_trigger = cam_trigger
        self.manager = multiprocessing.Manager()
        self.flashselection = self.manager.list()
        self.index = 0
        self.record = self.manager.list()
        self.direction = 0
        self.flash_select_pins = [8,10,12,16]
        self.trigger_pin = 18
        self.flashselection.append(0)
        self.flashselection.append(1)
        self.flashselection.append(2)
        self.flashselection.append(3)
        self.t = multiprocessing.Value('d',t)
        self.flashseq = multiprocessing.Value('i',0) #0 = flash all, 1 = flash in sequence
        self.preptime = 0.05
        self.triggertime = 0.5 #this will end up at least 200us
        self.seqn = 0
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        for pin in self.flash_select_pins:
            GPIO.setup(pin, GPIO.OUT)
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
        if fireflash:
            print("Photo:    Flash")
        else:
            print("Photo: No Flash")
        
        if fireflash:
            if self.flashseq.value==0:
                for flash in self.flashselection:
                    GPIO.output(self.flash_select_pins[flash],True)
            else:
                GPIO.output(self.flash_select_pins[self.flashselection[self.seqn]],True)
                self.seqn+=1
                if self.seqn>=len(self.flashselection):
                    self.seqn = 0
        else:
            for pin in self.flash_select_pins:
                GPIO.output(pin, False)
        time.sleep(self.preptime)
        triggertime = time.time() #TODO Why are these two different?
        triggertimestring = datetime.datetime.now() #need to convert to string later
        

        
        
        triggertimestring = triggertimestring.strftime("%Y%m%d_%H:%M:%S.%f")
        self.record.append({'index':self.index,'endofset':endofset,'direction':self.direction,'flash':fireflash,'flashselection':list(self.flashselection),'triggertime':triggertime,'triggertimestring':triggertimestring})
        self.index+=1

        #Software trigger...
        #self.cam_trigger.set()
        
        
        #Trigger via pin...
        GPIO.output(self.trigger_pin,True)

        time.sleep(self.triggertime)
        for pin in self.flash_select_pins:
            GPIO.output(pin, False)
            
        #(trigger via pin)...
        GPIO.output(self.trigger_pin,False)

        


    def worker(self):   
        while (True):
            self.run.wait()

            self.trigger_camera(True,False)
            self.trigger_camera(False,True)

            time.sleep(self.t.value-self.triggertime*2-self.preptime*2)
