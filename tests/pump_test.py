import RPi.GPIO as GPIO
import time

pump_channel = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(pump_channel, GPIO.OUT)

GPIO.output(pump_channel, 1)
time.sleep(2)
GPIO.cleanup()

