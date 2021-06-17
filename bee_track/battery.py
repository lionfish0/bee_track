import spidev
import time
import os

def ReadChannel(spi,channel):
  adc = spi.xfer2([1,(8+channel)<<4,0])
  data = ((adc[1]&3) << 8) + adc[2]
  return data


def read_batteries():
    # Open SPI bus
    spi = spidev.SpiDev()
    spi.open(0,0)
    spi.max_speed_hz=1000000
     
    # Function to read SPI data from MCP3008 chip
    # Channel must be an integer 0-7

    ch6 = ReadChannel(spi,6)
    ch7 = ReadChannel(spi,7)
    return ch6, ch7, ch6*0.016, ch7*0.016
