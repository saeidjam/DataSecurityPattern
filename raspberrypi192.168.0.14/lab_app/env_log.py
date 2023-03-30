#!/usr/bin/env python

'''
FILE NAME
env_log.py
1. WHAT IT DOES
Takes a reading from a DHT sensor and records the values in an SQLite3 database using a Raspberry Pi.
 
2. REQUIRES
* Any Raspberry Pi
* A DHT sensor
* A 10kOhm resistor
* Jumper wires
3. ORIGINAL WORK
Raspberry Full stack 2015, Peter Dalmaris
4. HARDWARE
D17: Data pin for sensor
5. SOFTWARE
Command line terminal
Simple text editor
Libraries:
pi	import sqlite3
import sys
import Adafruit_DHT
6. WARNING!
None
7. CREATED 
8. TYPICAL OUTPUT
No text output. Two new records are inserted in the database when the script is executed
 // 9. COMMENTS
--
 // 10. END
'''



import sqlite3
import socket
import ssl
import time

def log_values(sensor_id, temp, hum):
    # conn=sqlite3.connect('/var/www/lab_app/lab_app.db')  #It is important to provide an
                                 #absolute path to the database
                                 #file, otherwise Cron won't be
                                 #able to find it!
    conn = sqlite3.connect('lab_app.db')
    curs=conn.cursor()
    curs.execute("""INSERT INTO temperatures values(datetime(CURRENT_TIMESTAMP, 'localtime'),
         (?), (?))""", (sensor_id,temp))
    curs.execute("""INSERT INTO humidities values(datetime(CURRENT_TIMESTAMP, 'localtime'),
         (?), (?))""", (sensor_id,hum))
    conn.commit()
    conn.close()

HOST="192.168.0.14"
PORT=64320

sslcntxt = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
sslcntxt.load_verify_locations('public.pem')

while True:
    s = socket.socket()
    sslsocketwrapper = sslcntxt.wrap_socket(s, server_hostname=HOST)
    sslsocketwrapper.connect((HOST, PORT))
    data = sslsocketwrapper.recv(1024).decode('utf-8')
    sslsocketwrapper.close()
    temperature, humidity = data.split(',')
    if not temperature == 'sensor failure. check wire' or not humidity == 'sensor failure. check wire':
        temperature = float(temperature) * 9 / 5.0 + 32
        log_values("1", temperature, humidity)
        time.sleep(5)
    '''
    if humidity is not None and temperature is not None:
        else:
            log_values("1", -999, -999)
    '''




# humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 17)

# If you don't have a sensor but still wish to run this program, comment out all the 
# sensor related lines, and uncomment the following lines (these will produce random
# numbers for the temperature and humidity variables):
# import random
# humidity = random.randint(1,100)
# temperature = random.randint(10,30)
