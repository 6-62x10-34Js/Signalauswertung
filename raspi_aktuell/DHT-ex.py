#!/usr/bin/env python3
# coding=utf-8
import os
from time import sleep
import time
try:
    os.system ('sudo pigpiod')
except:
    pass
sleep (1)
import pigpio
import DHT
import sys
import csv
from datetime import datetime
sys.path.append('/home/pi/Desktop/automation/')
import main

# Initiate GPIO for pigpio
pi = pigpio.pi()
# Setup the Sensor
dht22 = DHT.sensor(pi, 4)
dht22.trigger()

asdasd
sleepTime = 3

def readDHT22():
    #Get a new reading
    dht22.trigger()
    #Save our values
    humidity = '%.2f' % (dht22.humidity() )
    temp = '%.2f' % (dht22.temperature() )
    return humidity, temp


# Liest die eben erstellte "start.txt" ein und speichert die Endzeit als Variable ab
# Die Erhebung läuft bis die momentane Zeit > der Endzeit ist. Die Daten des Sensors wird
# ein Zeitstempel gegeben und auf die Google Drive hochgeladen. Danach wird periodisch
# überprüft ob es eine neue "start.txt" Datei gibt.

def tryAgain(retries=0):
    if retries > 3:
        return
    try:
        main.uploadFile(filename,filepath,'text/csv')
    except:
        retries+=1
        tryAgain(retries)

while True:
    if main.is_connected() == False:
        sleep(2)
        print('ex')
        continue
    with open('/home/pi/Desktop/start.txt') as f:
        cont = f.read()
    t_goal = cont.rsplit(",",1)[-1]
    t_goal = datetime.strptime(t_goal,"%Y-%m-%d %H:%M:%S.%f")
    t_now = datetime.now()
        
        
    if t_now > t_goal:
        t_now = datetime.now()
        with open('/home/pi/Desktop/start.txt') as f:
            content = f.read()
        print(t_now)
        print('waiting')
        t_goal = content.rsplit(',',1)[-1]
        print(t_goal)
        t_goal = datetime.strptime(t_goal,"%Y-%m-%d %H:%M:%S.%f")
        sleep(10)
    
    
    if t_now < t_goal:
        y = time.strftime("%Y%m%d-%H%M%S")
        filepath = '/home/pi/Desktop/data/' + str(y) + '_temprh.csv'
        for t in range (5):
            x = datetime.now()
            humidity, temp = readDHT22()
            values = []
            values.append (humidity)
            values.append (temp)
            values.append(x)
            print ("Humidity is: " + humidity + "%")
            print ("Temperature is: " + temp + "C")
            with open(filepath,'ab') as f:
                wr = csv.writer(f, quoting=csv.QUOTE_ALL)
                wr.writerow(values)
            sleep (sleepTime)
        filename = str(y) + '_temprh.csv'
        tryAgain()
    
