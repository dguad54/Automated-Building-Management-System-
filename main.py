import sys
import os
import time
import threading
import RPi.GPIO as GPIO
sys.path.append(os.path.expanduser("~/lcd"))
import drivers
import dht11
import CIMISRequest
from CIMISRequest import fetchWeatherDataForHour
from CIMISRequest import WeatherData

myDHT=dht11.DHT11(pin=26)
display = drivers.Lcd()

# Pin declarations for ambient lighting when PIR is activated
PIRpin = 18
#dht = DHT.DHT(DHTpin)
GREEN_LED = 22
GREEN_BTN = 20
#AC and Heater buttons:
BTN_AC = 25
BTN_HEATER = 21
#AC and HEater LEDS
BLUE_LED =13
RED_LED = 5
greenLight = 0
doorStatus = 0
timer_thread = None
mutex = threading.Lock() #use mutext in senarios where staying in one state is needed
event = threading.Event()
HVACStatus=0
#temperture global variables:
averagetemp=0
feelsLikeTemp=0
targetTemp = 72
#CISMIS variables
startingHour = -1

FIRE_LED = 12
alarmStatus = 0

def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIRpin, GPIO.IN)
    #GPIO.setup(DHTpin, GPIO.IN)
    GPIO.setup(GREEN_LED, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(GREEN_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #inputs and ouputs for AC and Heater
    GPIO.setup(BTN_AC, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BTN_HEATER, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(RED_LED, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(BLUE_LED, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(FIRE_LED, GPIO.OUT, initial=GPIO.LOW)
def pirLight(channel):
    global greenLight
    global timer_thread
   
    status = GPIO.input(PIRpin)
    if status == 1:
        #print("Motion detected. Turning on green LED.")
        event.clear()  # Clear the event to stop the timer
        GPIO.output(GREEN_LED, 1)  # Turn on the green LED
        greenLight = 1
       
        if timer_thread and timer_thread.is_alive():
            return
       
    else:
       # print("No motion detected. Starting 10-second timer.")
        event.set()
        timer_thread = threading.Thread(target=timer, daemon=True)
        timer_thread.start()

def timer():
    startTime = time.time()
    #print("Timer started.")
    while event.is_set():
        elapsed_time = time.time() - startTime
        #print(f"Elapsed time: {elapsed_time:.2f} seconds.")
        if elapsed_time > 10:
          #  print("10 seconds elapsed. Turning off green LED.")
            GPIO.output(GREEN_LED, 0)  # Turn off the green LED
            greenLight = 0
            event.clear()  # Clear the event to stop the timer
            break
        time.sleep(0.1)  # Small sleep to prevent busy-waiting

def doorSecurity(channel):
    global mutex
    global doorStatus
    if doorStatus == 0:
        doorStatus = 1
        mutex.acquire()
        display.lcd_clear()
        display.lcd_display_string("DOOR/WINDOW OPEN",1)
        display.lcd_display_string("  HVAC HALTED  ",2)
        time.sleep(3)
        mutex.release()
    elif doorStatus == 1:
        doorStatus = 0
        mutex.acquire()
        display.lcd_clear()
        display.lcd_display_string("   DOOR CLOSED  ",1)
        display.lcd_display_string("   HVAC START  ",2)
        time.sleep(3)
        mutex.release()
       
def calcTemp():
    global mutex
    tempEvent.wait()
    global averagetemp
    global averagehum
    global feelsLikeTemp
    global HVACStatus
    global alarmStatus
    currentHour = startingHour
    print("Current hour = ",currentHour)
    while tempEvent.is_set():
        mutex.acquire()
        #get first temperture
        if doorStatus == 0:
            while True:
                result = myDHT.read()
                if result.temperature > 0:
                    break
        temp1 = (result.temperature * 9/5) + 32
        #print("Temp 1: ,",temp1)
        time.sleep(0.3)
        #get second temp to average out
        while True:
                result = myDHT.read()
                if result.temperature > 0:
                    break
        temp2 = (result.temperature * 9/5) + 32
        #print("Temp 1: ,",temp2)
        time.sleep(0.3)
        #get third temperature
        while True:
                result = myDHT.read()
                if result.temperature > 0:
                    break
        temp3 = (result.temperature * 9/5) + 32
        #print("Temp 1: ,",temp3)
        time.sleep(0.3)
       
        data = fetchWeatherDataForHour(currentHour)
        while(data is None or data.getRelativeHumidity() is None):
            if data is None:
                print("Failed Request")
            time.sleep(60*60)
            data = fetchWeatherDataForHour(currentHour)
        if data.getRelativeHumidity() is not None:
            averagehum = float(data.getRelativeHumidity())
        averagetemp = round((temp1+temp2+temp3)/3)
        feelsLikeTemp = round(averagetemp + 0.05*averagehum)
        LCDOutput()
        print("Feels like temp: ", feelsLikeTemp)
        if feelsLikeTemp >= 95:
           if alarmStatus == 0:
               alarmStatus = 1
               activateFireAlarm()
        else:
           if alarmStatus == 1:
               alarmStatus = 0
               deactivateFireAlarm()
           
       
        mutex.release()
        time.sleep(0.1)
       
def activateFireAlarm():
    global HVACStatus
    HVACStatus = 0  # Turn off HVAC
    GPIO.output(BLUE_LED, 0)  # Turn off AC
    GPIO.output(RED_LED, 0)  # Turn off Heater
    fireAlarmThread = threading.Thread(target=fireAlarm, daemon=True)
    fireAlarmThread.start()

def deactivateFireAlarm():
    global HVACStatus
    GPIO.output(FIRE_LED, 0)  # Turn off the flashing LED
    mutex.acquire()
    display.lcd_clear()
    display.lcd_display_string("Temperture in safe range", 1)
    display.lcd_display_string("Resuming Operation", 2)
    time.sleep(3)
    mutex.release()
    # Optionally reset HVAC status or leave it off until user interaction
    HVACStatus = 0

def fireAlarm():
    while alarmStatus:
        GPIO.output(FIRE_LED, 1)  # Turn on the flashing LED
        mutex.acquire()
        display.lcd_clear()
        display.lcd_display_string("FIRE ALARM!", 1)
        display.lcd_display_string("  EVACUATE  ", 2)
        mutex.release()
        time.sleep(0.5)
        GPIO.output(FIRE_LED, 0)  # Turn off the flashing LED
        time.sleep(0.5)
                           
def AC_control(channel):
    global averagetemp
    global feelsLikeTemp
    global HVACStatus
    global averagetemp
    global targetTemp
    global doorStatus
    currentState = HVACStatus
   
    if doorStatus == 0:
        if feelsLikeTemp >= targetTemp - 3:
            GPIO.output(BLUE_LED,1)
            HVACStatus = 1 # 1 means AC on status
            if currentState != HVACStatus:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("AC is on",1)
                time.sleep(3)
                mutex.release()
        elif feelsLikeTemp <= targetTemp - 3:
            GPIO.output(RED_LED,1)
            HVACStatus = 2 # 2 means heater on status
            if currentState != HVACStatus:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("Heater is on",1)
                time.sleep(3)
                mutex.release()
        else:
            HVACStatus = 0
            GPIO.output(RED_LED,0)
            GPIO.output(BLUE_LED,0)
            if currentState == 1:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("  HVAC AC ",1)
                display.lcd_display_string("  OFF  ",2)
                time.sleep(3)
                mutex.release()
            elif currentState == 2:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("  HVAC HEATER ",1)
                display.lcd_display_string("  OFF  ",2)
                time.sleep(3)
                mutex.release()

def Heater_control(channel):
    global averagetemp
    global feelsLikeTemp
    global HVACStatus
    global averagetemp
    global targetTemp
    global doorStatus
    currentState = HVACStatus
   
    if doorStatus == 0:
        if feelsLikeTemp >= targetTemp - 3:
            GPIO.output(BLUE_LED,1)
            HVACStatus = 1 # 1 means AC on status
            if currentState != HVACStatus:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("AC is on",1)
                time.sleep(3)
                mutex.release()
        elif feelsLikeTemp <= targetTemp - 3:
            GPIO.output(RED_LED,1)
            HVACStatus = 2 # 2 means heater on status
            if currentState != HVACStatus:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("Heater is on",1)
                time.sleep(3)
                mutex.release()
        else:
            HVACStatus = 0
            GPIO.output(RED_LED,0)
            GPIO.output(BLUE_LED,0)
            if currentState == 1:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("  HVAC AC ",1)
                display.lcd_display_string("  OFF  ",2)
                time.sleep(3)
                mutex.release()
            elif currentState == 2:
                mutex.acquire()
                display.lcd_clear()
                display.lcd_display_string("  HVAC HEATER ",1)
                display.lcd_display_string("  OFF  ",2)
                time.sleep(3)
                mutex.release()
               
def LCDOutput():
    global doorStatus
    global HVACStatus
    global targetTemp
    global feelsLikeTemp
    global greenLight
    currentTemperature_str = str(feelsLikeTemp)
    targetTemperature_str = str(targetTemp)
    if greenLight == 0:
        lightOut = "OFF"
    else:
        lightOut = "ON"
   
    if doorStatus == 0:
        doorOut = "C"
    else:
        doorOut = "O"
       
    if HVACStatus == 0:
        hvacOut = "OFF"
    elif HVACStatus == 1:
        hvacOut = "AC"
    else:
        hvacOut = "HEAT"
   
    display.lcd_clear()
    display.lcd_display_string(currentTemperature_str + "/" +targetTemperature_str +"     " + "  Dr:" + doorOut,1)
    display.lcd_display_string("H:" + hvacOut + "      " + "L:" + lightOut,2)
       
               
if __name__ == "__main__":
    try:
        setup()
        GPIO.add_event_detect(PIRpin, GPIO.BOTH, callback=pirLight, bouncetime=150)
        GPIO.add_event_detect(GREEN_BTN, GPIO.RISING, callback=doorSecurity, bouncetime=150)
        #Temperture contol buttons:
        GPIO.add_event_detect(BTN_AC, GPIO.RISING, callback=AC_control, bouncetime=150)
        GPIO.add_event_detect(BTN_HEATER, GPIO.RISING, callback=Heater_control, bouncetime=150)
        tempThread = threading.Thread(target = calcTemp)
        event = threading.Event()
        tempEvent = threading.Event()
        startingHour = time.localtime(time.time()).tm_hour - 2
        tempThread.daemon = True
        tempThread.start()
        tempEvent.set()
        while True:
            time.sleep(1e6)  # Keep the main thread alive
       
    except KeyboardInterrupt:
        display.lcd_clear()
        GPIO.output(GREEN_LED, GPIO.LOW)
   
    finally:
        print("Cleaning up GPIO and exiting.")
        GPIO.cleanup()