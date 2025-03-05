from machine import UART
import machine
import os
import sys
#import upip
uart = UART(0, baudrate=115200)
os.dupterm(uart)

machine.main('main.py')