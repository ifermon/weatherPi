#!/usr/bin/env python

# 2014-09-12 spi-DHT22.py
# Public Domain

import time
import pigpio
import logging

_3W=(1<<9)
_3WN=(15<<10)

SPEED=200000
BYTES=130

pi = pigpio.pi() # Connect to local Pi.

dht22 = pi.spi_open(0, SPEED, _3W|_3WN)

# Intervals of about 2 seconds or less will eventually hang the DHT22.
INTERVAL=6

logging.basicConfig(filename="temp.out", format="%(message)s",
                level=logging.DEBUG)

r = 0

next_reading = time.time()
last_reading = next_reading + 300

def getBit(in_bit, in_byte, buf):
   global BYTES
   v = not (buf[in_byte] & (1<<(7-in_bit))) # Force logical result.
   numbit = 1

   while in_byte < BYTES:
      in_bit += 1
      if in_bit > 7:
         in_bit = 0
         in_byte += 1
      nv = not (buf[in_byte] & (1<<(7-in_bit))) # Force logical result.
      if nv == v:
         numbit += 1
      else:
         if not v: # Return high edge.
            return (numbit, in_bit, in_byte)
         else: # Skip low edge.
            v = nv
            numbit = 1
   return (0, 0, 0)

while True:

   r += 1

   (c, buf) = pi.spi_read(dht22, BYTES+1)

   numbit = 1
   in_bit = 0
   in_byte = 0
   (numbit, in_bit, in_byte) = getBit(in_bit, in_byte, buf)
   (numbit, in_bit, in_byte) = getBit(in_bit, in_byte, buf)
   bit = 0
   byte = 0
   val = [0]*5
   while numbit:
      (numbit, in_bit, in_byte) = getBit(in_bit, in_byte, buf)
      if numbit:
         if numbit > 9:
            val[byte] |= (1<<(7-bit))
         bit += 1
         if bit > 7:
            bit = 0
            byte += 1

   checksum = 0
   for i in range(4):
      checksum += val[i]
   if val[4] == (checksum&255):
      humidity = ((val[0]*256)+val[1]) / 10.0
      sign = val[2]&128
      val[2] &= 0x127
      temperature = ((val[2]*256)+val[3]) / 10.0
      print("temp {0}".format(temperature))
      if sign:
         temperature = -temperature
      temperature = (temperature * (9.0/5.0)) + 32.0
      t = time.time()
      localtime = time.asctime( time.localtime(t))
      log_msg = "{0} | {1} | {2} | {3}".format(humidity, temperature, 
                localtime, t)
      print ("{0}".format(log_msg))
      logging.debug(log_msg)

   next_reading += INTERVAL

   time.sleep(next_reading-time.time()) # Overall INTERVAL second polling.

pi.spi_close(dht22)

pi.stop()

