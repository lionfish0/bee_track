import numpy as np
import time
import datetime
import RPi.GPIO as GPIO
from configurable import Configurable
import multiprocessing
from RpiMotorLib import RpiMotorLib
from time import sleep

class Rotate(Configurable):
    def __init__(self,message_queue):
        super().__init__(message_queue)
        print("Initialising Rotate Control")  
        self.manager = multiprocessing.Manager()
        self.targetangle = multiprocessing.Value('d',0)
        self.rotation = multiprocessing.Event()


        self.direction= 20 # Direction (DIR) GPIO Pin
        self.step =  21 # Step GPIO Pin
        self.EN_pin =  16 # enable pin (LOW to enable)

        # Declare a instance of class pass GPIO pins numbers and the motor type
        self.motorcontrol = RpiMotorLib.A4988Nema(self.direction, self.step, (1,1,1), "DRV8825")
        print("Setting pin En_pin as output")
        sleep(0.1)
        GPIO.setup(self.EN_pin,GPIO.OUT) # set enable pin as output


    def worker(self):   
        self.currentangle = 0
        self.stepcounter = 0
        
        #print("TESTING")
        #for i in range(25):        
        #    GPIO.output(self.EN_pin,GPIO.HIGH)
        #    self.motorcontrol.motor_go(0,"1/32",256,0.005,False,0.05)
        #    GPIO.output(self.EN_pin,GPIO.LOW)
        #    sleep(2.0)
        #print("DONE")
        
        while (True):
            print("Ready for next rotate command.")
            self.rotation.wait()
            GPIO.output(self.EN_pin,GPIO.HIGH)
            
            
            if self.currentangle>180: self.currentangle = self.currentangle - 360
            if self.currentangle<-180: self.currentangle = self.currentangle + 360
            angletorotate = (self.targetangle.value - self.currentangle) 
            if angletorotate>180: angletorotate = angletorotate - 360
            if angletorotate<-180: angletorotate = angletorotate + 360            
            
            #e.g.
            #target - current = 
            #320    -   30    =  290 -> -70
            #  0    -  350    = -350 -> -10
            #200    -  180    =   20 ->  20
            #150    -  200    =  -50 -> -50
            
            #ramp up
            #initialdelay = 0.05
            #rampdelay = 0.001
            #ramplength = 10
            #stepsperloop = 30
            totalsteps = int(abs(angletorotate)*(32.0*200/360))  # number of steps 200=complete turn in full mode, so at 1/32 -> 6400
            #totalsteps = int(32*np.round(abs(angletorotate)*(200/360)))  # to nearest whole step.
            #totalstepsleft = totalsteps
            self.motorcontrol.motor_go(angletorotate>0,"1/32",totalsteps,0.005,False,0.05)
            self.stepcounter+=totalsteps
            
            
            #rampsteps = int(totalsteps/stepsperloop)+1
            #if (totalsteps>0):
            #    for ramp in range(rampsteps):
            #        if ramp<min(ramplength,rampsteps/2):
            #            rampdelay = 0.005*((ramplength-ramp)/ramplength)+0.0005*((ramp)/ramplength) #(100+np.exp(-(ramp-(ramplength/2))))/300000
            #        if ramp>max(rampsteps-ramplength,rampsteps/2):
            #            rampdelay = 0.005*(((ramp+ramplength)-rampsteps)/ramplength)+0.0005*((rampsteps-ramp)/ramplength) 
            #            #rampdelay = #(100+np.exp(-((rampsteps-ramp)-(ramplength/2))))/300000      
            #        num_steps = min(stepsperloop,int(totalstepsleft))
            #        totalstepsleft-=stepsperloop
            #        #print("%0.2f (%d)" % ((rampdelay*1000),num_steps))
            #        self.motorcontrol.motor_go(angletorotate>0,"1/32",num_steps,rampdelay,False,initialdelay)
            #        self.stepcounter+=num_steps
            #        initialdelay = 0.01
                
            actualchange = float(totalsteps * np.sign(angletorotate)*360.0/(200*32))
            #actualchange = float(np.trunc(totalsteps/32) * np.sign(angletorotate)*360/(200))
            print("Actual rotation %0.3f" % actualchange)
            print("Total Steps: %d" % totalsteps)
            print("Total Step Counter: %d" % self.stepcounter)
            self.currentangle = self.currentangle + actualchange  #self.targetangle.value
            print("Done rotation.")
            GPIO.output(self.EN_pin,GPIO.LOW) 
            self.rotation.clear()
            
