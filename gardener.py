#!/usr/bin/python
import threading
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import time

from flask import Flask, Response
import json

# Creatig Gardener App responsible for maintaining a single plant box
class Gardener(threading.Thread):
    def __init__(self, sensor_channel, pump_channel, hour=8, minute=00):
        threading.Thread.__init__(self)
        
        # Sensor GPIO Setup
        self.sensor_channel = sensor_channel
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.sensor_channel, GPIO.IN)

        # Pump GPIO Setup
        self.pump_channel = pump_channel
        #TODO: Set up pump GPIO

        # Waterning Clock Setup
        self.watering_hour = hour
        self.watering_minute = minute
        self.last_watering = datetime.now()
        self.next_watering = (self.last_watering + timedelta(days=1)).replace(
                hour=self.watering_hour, minute=self.watering_minute, second=0)
        
        # Data Clock Cycle Setu
        self.clock_speed_s = 10                                                                 # Slow gardener clock keep large
        self.water_detected_live = False
        self.water_detected = True                                                              # When hooked to the pump you want the default value to be True
    
    # Sensor callback
    def callback(self, channel):
        if (GPIO.input(channel)):
            # print("Water Detected!")
            water_detected_live = True
        else:
            # print("Water Detected!")
            self.water_detected_live = True

    def run_pump(self):
        #TODO run pump

        self.last_watering = datetime.now()
        self.next_watering = (self.last_watering + timedelta(days=1)).replace(
                hour=self.watering_hour, minute=self.watering_minute)
    
    def run(self):
        GPIO.add_event_detect(self.sensor_channel, GPIO.BOTH, bouncetime=400)
        GPIO.add_event_callback(self.sensor_channel, self.callback)
        
        # Gardener main loop
        while True:
            # Data Cycle
            self.water_detected_live = False
            time.sleep(self.clock_speed_s)
            self.water_detected = self.water_detected_live
            print("Water detected clock cycle:", self.water_detected)                           # Debug print cycle (Sensors are finicky)

            # Watering Clock
            if (0 > (datetime.now() - self.next_watering).total_seconds()):
                self.run_pump()

# Setup Apps
gardener_app = Gardener(
        sensor_channel=21,
        pump_channel=0, 
        hour=9, minute=30)
flask_app = Flask(__name__)

@flask_app.route("/", methods = ['GET'])
def data():
    data = {"water_detected": gardener_app.water_detected, 
            'last_watering': gardener_app.last_watering.strftime("%m/%d/%Y, %H:%M:%S"),
            'next_watering': gardener_app.next_watering.strftime("%m/%d/%Y, %H:%M:%S")}

    data_as_str = json.dumps(data)
    return Response(response=data_as_str, status=200, mimetype="application/json")

if __name__ == '__main__':
    gardener_app.start()
    flask_app.run(host='0.0.0.0')

