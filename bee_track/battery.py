import spidev
import time
import os

def ReadChannel(spi,channel):
  adc = spi.xfer2([1,(8+channel)<<4,0])
  data = ((adc[1]&3) << 8) + adc[2]
  return data

def scale(v):
    p = -100
    if v>11.25: p=-10
    if v>11.5: p=0
    if v>11.6: p=10
    if v>11.7: p=20
    if v>11.75: p=30
    if v>11.82: p=40 
    if v>11.92: p=50
    if v>12.0: p=60
    if v>12.1: p=70
    if v>12.1: p=80
    if v>12.25: p=90
    if v>12.75: p=100
    return p
    
def read_batteries():
    scaleval = 0.0164
    # Open SPI bus
    spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz=1000000
     
    # Function to read SPI data from MCP3008 chip
    # Channel must be an integer 0-7

    chB = ReadChannel(spi,6)
    chA = ReadChannel(spi,7)
    #return ch6, ch7, ch6*0.016, ch7*0.016
    if (scale(chA*scaleval)<0) or (scale(chB*scaleval)<0):
        alert = 'low! '
    else:
        alert = ''
    return "%sA:%0.2f (%d%%), B:%0.2f (%d%%)" % (alert,chA*scaleval,scale(chA*scaleval), chB*scaleval, scale(chB*scaleval)) #0.016*1.027322861
