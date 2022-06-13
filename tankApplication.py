#packages and libraries
import time
import board
import busio
import digitalio
import pyrebase

import adafruit_dht
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from gpiozero import LED
from datetime import datetime

#initiate sensors
    #initialize ADC chip
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)

    #initialize ADC channel inputs
ch0_ldr = AnalogIn(mcp, MCP.P0)
ch1_soilMoisture = AnalogIn(mcp, MCP.P1)
ch8_pot = AnalogIn(mcp, MCP.P7)

    # initialize dht sensor using raspberry pi GPIO21. if you don't specify use_pulseio=False, then the script will run successfully once and fail on subesequent runs until reboot.
dhtDevice = adafruit_dht.DHT11(board.D17, use_pulseio=False)

#initiate outputs with initial value = false (off)
fan_relay = LED(6, active_high = True, initial_value = False)
water_relay = LED(13, active_high = True, initial_value = False)
blue_relay = LED(19, active_high = True, initial_value = False)
red_relay = LED(26, active_high = True, initial_value = False)

#other variables
dhtSuccess = False

#connect to database
config = {
    "apiKey": "AIzaSyBMrIvuFyhpDja62FriCuBRkIjMGVV3GI8",
    "authDomain": "smart-mini-vivarium.firebaseapp.com",
    "databaseURL": "https://smart-mini-vivarium-default-rtdb.firebaseio.com/",
    "storageBucket": "smart-mini-vivarium.appspot.com"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

while True: 
    #get current time
    now = datetime.now()
    date_time = now.strftime("%Y/%m/%d %H:%M:%S")
    current_hour = now.hour
    
    #read sensors
    dhtReadSuccess = False
    while (dhtReadSuccess == False): 
        try: 
            temp_c = dhtDevice.temperature
            humidity = dhtDevice.humidity
            dhtReadSuccess = True
            
        except RuntimeError as error:
            print(error.args[0])
        
    light = 100*ch0_ldr.voltage/3.3
    soilMoisture = 100*ch1_soilMoisture.voltage/3.3
    pot = 100*ch8_pot.voltage/3.3
      
    print(f"Temp: {int(temp_c)} deg C")
    print(f"Humidity: {int(humidity)} %")
    print(f"Light: {int(light)} %")
    print(f"Soil Moisture: {int(soilMoisture)} %")
    print(f"Pot: {int(pot)} %")
    print("")
    
    #grab schedule from db
    print(f"current time: {current_hour} H")
    activateWater = db.child("schedule").child("pump").child(current_hour).get()
    activateFan = db.child("schedule").child("fan").child(current_hour).get()
    activateRLight = db.child("schedule").child("red led").child(current_hour).get()
    activateBLight = db.child("schedule").child("blue led").child(current_hour).get()
    
    print(f"water: {activateWater.val()}")
    print(f"fan: {activateFan.val()}")
    print(f"red light: {activateRLight.val()}")
    print(f"blue light: {activateBLight.val()}")
       
    #run water routine
    fan_relay.off()
    water_relay.off()
    red_relay.off()
    blue_relay.off()
    time.sleep(2)
    if (activateWater.val() == 1):
        if (soilMoisture < 35): 
            print(f"Activating water at {date_time}")
            water_relay.on()
            #db.child("current status").child("outputs").child("pump").set(water_relay.value)

            time.sleep(10)
            water_relay.off()
            #db.child("current status").child("outputs").child("pump").set(water_relay.value)
            print("water activation complete")
            time.sleep(5)
        else: print("water not needed")
    else: print("no water scheduled")
        
    #run fan routine
    fan_relay.off()
    water_relay.off()
    red_relay.off()
    blue_relay.off()
    time.sleep(2)
    if (activateFan.val() == 1):
        print(f"Activating fan at {date_time}")

        fan_relay.on()
        #db.child("current status").child("outputs").child("fan").set(fan_relay.value)
        time.sleep(5)
        fan_relay.off()
        print("fan activation complete")
        #db.child("current status").child("outputs").child("fan").set(fan_relay.value)
        time.sleep(5)
    else: print("no fan scheduled")
        
    
    #run light routine
    fan_relay.off()
    water_relay.off()
    red_relay.off()
    blue_relay.off()
    time.sleep(2)
    
    if (light < 75):
        if (activateRLight.val() == 1):
            print(f"Activating red light at {date_time}")
            red_relay.on()
            
        else:
            print("red light not scheduled")
            red_relay.off()
            
        if (activateBLight.val() == 1):
            print(f"Activating blue light at {date_time}")
            blue_relay.on()
            
        else:
            print("blue light not scheduled")
            blue_relay.off()

    
    else:
        print("light not needed")
        red_relay.off()
        blue_relay.off()
    
    time.sleep(5)
         
        
    #db.child("current status").child("outputs").child("blue led").set(blue_relay.value)    
    #db.child("current status").child("outputs").child("red led").set(red_relay.value)
  
    #read sensors/outputs and write to db
    now = datetime.now()
    date_time = now.strftime("%Y/%m/%d %H:%M:%S")
    dhtReadSuccess = False
    while (dhtReadSuccess == False): 
        try: 
            temp_c = dhtDevice.temperature
            humidity = dhtDevice.humidity
            dhtReadSuccess = True
            
        except RuntimeError as error:
            print(error.args[0])
        
    light = 100*ch0_ldr.voltage/3.3
    soilMoisture = 100*ch1_soilMoisture.voltage/3.3
    pot = 100*ch8_pot.voltage/3.3
    
    print("")
    print("preparing to transfer data to firebase")
    print("")
        
    sensor_data = {
        
        "temp": int(temp_c),
        "humidity": int(humidity),
        "light": int(light),
        "soil moisture": int(soilMoisture),
    }
    output_data = {
        
        "red led": int(activateRLight.val()),
        "blue led": int(activateBLight.val()),
        "fan": int(activateFan.val()),
        "pump": int(activateWater.val())
    }
    print("...")
    db.child("current status").set({"time": date_time})
    db.child("current status").child("sensors").set(sensor_data)
    db.child("current status").child("outputs").set(output_data)
    db.child("past data").child(date_time).set(sensor_data)
    db.child("history").child(now.year).child(now.month).child(now.day).child(now.hour).child("sensors").set(sensor_data)
    db.child("history").child(now.year).child(now.month).child(now.day).child(now.hour).child("outputs").set(output_data)
    db.child("history").child(now.year).child(now.month).child(now.day).child(now.hour).child("scan time").set(now.strftime("%Y-%m-%d %H:%M:%S"))
  
    print("transfer complete")
    print("")

    #determine how long to wait til next check
    now = datetime.now()
    date_time = now.strftime("%Y/%m/%d %H:%M:%S")
    current_minute = now.minute
    minutesToWait = 60 - current_minute
    secondsToWait = minutesToWait*60

    #wait
    print(f"wait {minutesToWait} mins til next check")
    print("")
    time.sleep(secondsToWait)
