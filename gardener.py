#!/usr/bin/python
import threading
import atexit
from datetime import datetime, timedelta
import time

import RPi.GPIO as GPIO
import busio
import digitalio
import board
import time
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

from flask import Flask, Response
import json

from utils import WindowedLinkedList 

# Env Variables
FIRST_WATERING = (3,26)
DAYLY_WATERING = (8,30)

PUMP_LPH = 400
PUMP_PRESSURIZE_S = 1

PUMP_CHANNEL = 21
SENSOR_MCP3008_PIN = MCP.P0

# Setup Prog GPIO Addressing
GPIO.setmode(GPIO.BCM)

# Creatig Gardener App responsible for maintaining a single plant box
class Gardener(threading.Thread):
    def __init__(self, sensor_pin, pump_channel, hour=8, minute=00, 
            pump_lph=400, pump_pressurize_s=1, first_watering=None):
        threading.Thread.__init__(self)
        
        # Plant attribs
        self.plant_lpd = 0.2

        # Sensor Spi Setup
        self.sensor_spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        self.sensor_cs = digitalio.DigitalInOut(board.CE0)
        self.sensor_mcp = MCP.MCP3008(self.sensor_spi, self.sensor_cs)
        self.sensor_channel = AnalogIn(self.sensor_mcp, sensor_pin)

        # Pump GPIO Setup
        self.pump_channel = pump_channel
        GPIO.setup(self.pump_channel, GPIO.OUT)
        self.pump_lph = pump_lph
        self.pump_lps = (float(self.pump_lph) / 60.0 / 60.0)
        self.pump_pressure_s = pump_pressurize_s
        self.pump_speed_s = self.pump_pressure_s + self.plant_lpd / self.pump_lps

        # Waterning Clock Setup
        self.watering_hour = hour
        self.watering_minute = minute
        self.last_watering = datetime.now()
        self.next_watering = first_watering if first_watering else (
                self.last_watering + timedelta(days=1)).replace(
                    hour=self.watering_hour, minute=self.watering_minute)

        # Data Clock Cycle Setup (Sampling)
        self.clock_speed_s = 10                                                                 # Slow gardener clock keep large
        self.soil_conductivity_plot = WindowedLinkedList(8640 * 7 * 3)
        self.water_detected_last = None # Date Object
        self.soil_conductivity = float("NaN")

    def sample_soil(self):
        voltage = self.sensor_channel.voltage
        sensor_current = 0.015 # Sensor amps (~Arb closer to 0.0005 amps)
        resistance = voltage / sensor_current
        self.soil_conductivity_plot.push(resistance)
        self.soil_conductivity = 1.0 / resistance

    def run_pump(self):
        GPIO.output(self.pump_channel, GPIO.HIGH)
        time.sleep(self.pump_speed_s)
        GPIO.output(self.pump_channel, GPIO.LOW)

        self.last_watering = datetime.now()
        self.next_watering = (self.last_watering + timedelta(days=1)).replace(
                hour=self.watering_hour, minute=self.watering_minute)
    
    def run(self):
        # Gardener main loop
        while True:
            # Data Cycle
            self.water_detected_live = False
            self.sample_soil()

            # Watering Clock
            if (0 <= (datetime.now() - self.next_watering).total_seconds()):
                self.run_pump()
                print("Ran pump at", datetime.now())
            
            time.sleep(self.clock_speed_s)

# Setup Apps
first_watering = datetime.now().replace(
        hour=FIRST_WATERING[0], minute=FIRST_WATERING[1])
gardener_app = Gardener(
        sensor_pin=SENSOR_MCP3008_PIN,
        pump_channel=PUMP_CHANNEL,
        hour=DAYLY_WATERING[0], minute=DAYLY_WATERING[1],
        pump_lph=PUMP_LPH, pump_pressurize_s=PUMP_PRESSURIZE_S,
        first_watering=first_watering)

flask_app = Flask(__name__)

@flask_app.route("/", methods = ['GET'])
def data():
    data = {"curr_soil_conductivity": gardener_app.soil_conductivity,
            'last_watering': gardener_app.last_watering.strftime("%m/%d/%Y, %H:%M:%S"),
            'next_watering': gardener_app.next_watering.strftime("%m/%d/%Y, %H:%M:%S")}

    data_as_str = json.dumps(data)
    return Response(response=data_as_str, status=200, mimetype="application/json")

# Cleanup Procedures
def cleanup():
   GPIO.cleanup()

atexit.register(cleanup)
if __name__ == '__main__':
    gardener_app.start()
    flask_app.run(host='0.0.0.0')
