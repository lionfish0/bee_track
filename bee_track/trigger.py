import time
import RPi.GPIO as GPIO
import multiprocessing

class Trigger:
    def __init__(self,t=2.0):
        print("Initialising Trigger Control")
        self.manager = multiprocessing.Manager()
        self.flashselection = self.manager.list()
        self.index = 0
        self.record = []
        self.direction = 0
        self.flash_select_pins = [5]
        self.trigger_pin = 3
        self.flashselection.append(0)
        self.t = multiprocessing.Value('d',t)
        self.preptime = 0.05
        self.triggertime = 0.07
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
    
    def trigger_camera(self,fireflash):
        if fireflash:
            print("Photo:    FLASH")
        else:
            print("Photo: No Flash")
        self.record.append({'index':self.index,'direction':self.direction,'flash':fireflash,'flashselection':self.flashselection})
        if fireflash:
            for flash in self.flashselection:
                GPIO.output(self.flash_select_pins[flash],True)
        else:
            for pin in self.flash_select_pins:
                GPIO.output(pin, False)
        time.sleep(self.preptime)
        GPIO.output(self.trigger_pin,True)
        time.sleep(self.triggertime)
        for pin in self.flash_select_pins:
            GPIO.output(pin, False)
        GPIO.output(self.trigger_pin, False)
           
        
    def worker(self):   
        while (True):
            self.run.wait()
            self.trigger_camera(True)
            self.trigger_camera(False)
            time.sleep(self.t.value-self.triggertime-self.preptime)
