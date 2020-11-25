#!/usr/bin/env python3
# coding=utf-8
# "DATASHEET": http://cl.ly/ekot
# https://gist.github.com/kadamski/92653913a53baf9dd1a8
from __future__ import print_function
import serial, struct, sys, time, json, subprocess
import csv
from time import sleep
import datetime
import os

import sys
sys.path.append('/home/pi/Desktop/automation/')
import main

DEBUG = 0
CMD_MODE = 2
CMD_QUERY_DATA = 4
CMD_DEVICE_ID = 5
CMD_SLEEP = 6
CMD_FIRMWARE = 7
CMD_WORKING_PERIOD = 8
MODE_ACTIVE = 0
MODE_QUERY = 1
PERIOD_CONTINUOUS = 0

JSON_FILE = 'test.json'#'/var/www/html/aqi.json'

MQTT_HOST = ''
MQTT_TOPIC = '/weather/particulatematter'

ser = serial.Serial()
ser.port = "/dev/ttyUSB0"
ser.baudrate = 9600

ser.open()
ser.flushInput()

byte, data = 0, ""

def sleeper():
    global timex
    dec = timex % 1
    print(dec)
    if (-0.01) <= dec <= 0.01:
        try:
            cmd_set_sleep(0)
            for t in range(15):
                vals = cmd_query_data()
                sleep(2)
            timex = 0.025
            cmd_set_sleep(1)
        except:
            pass
    
def dump(d, prefix=''):
    print(prefix + ' '.join(x.encode('hex') for x in d))

def construct_command(cmd, data=[]):
    assert len(data) <= 12
    data += [0,]*(12-len(data))
    checksum = (sum(data)+cmd-2)%256
    ret = "\xaa\xb4" + chr(cmd)
    ret += ''.join(chr(x) for x in data)
    ret += "\xff\xff" + chr(checksum) + "\xab"

    if DEBUG:
        dump(ret, '> ')
    return ret

def process_data(d):
    r = struct.unpack('<HHxxBB', d[2:])
    pm25 = r[0]/10.0
    pm10 = r[1]/10.0
    checksum = sum(ord(v) for v in d[2:8])%256
    return [pm25, pm10]
    #print("PM 2.5: {} μg/m^3  PM 10: {} μg/m^3 CRC={}".format(pm25, pm10, "OK" if (checksum==r[2] and r[3]==0xab) else "NOK"))

def process_version(d):
    r = struct.unpack('<BBBHBB', d[3:])
    checksum = sum(ord(v) for v in d[2:8])%256
    print("Y: {}, M: {}, D: {}, ID: {}, CRC={}".format(r[0], r[1], r[2], hex(r[3]), "OK" if (checksum==r[4] and r[5]==0xab) else "NOK"))

def read_response():
    byte = 0
    while byte != "\xaa":
        byte = ser.read(size=1)

    d = ser.read(size=9)

    if DEBUG:
        dump(d, '< ')
    return byte + d

def cmd_set_mode(mode=MODE_QUERY):
    ser.write(construct_command(CMD_MODE, [0x1, mode]))
    read_response()

def cmd_query_data():
    ser.write(construct_command(CMD_QUERY_DATA))
    d = read_response()
    values = []
    if d[1] == "\xc0":
        values = process_data(d)
    return values

def cmd_set_sleep(sleep):
    mode = 0 if sleep else 1
    ser.write(construct_command(CMD_SLEEP, [0x1, mode]))
    read_response()

def cmd_set_working_period(period):
    ser.write(construct_command(CMD_WORKING_PERIOD, [0x1, period]))
    read_response()

def cmd_firmware_ver():
    ser.write(construct_command(CMD_FIRMWARE))
    d = read_response()
    process_version(d)

def cmd_set_id(id):
    id_h = (id>>8) % 256
    id_l = id % 256
    ser.write(construct_command(CMD_DEVICE_ID, [0]*10+[id_l, id_h]))
    read_response()

def pub_mqtt(jsonrow):
    cmd = ['mosquitto_pub', '-h', MQTT_HOST, '-t', MQTT_TOPIC, '-s']
    print('Publishing using:', cmd)
    with subprocess.Popen(cmd, shell=False, bufsize=0, stdin=subprocess.PIPE).stdin as f:
        json.dump(jsonrow, f)

def tryAgain(retries=0):
    if retries > 3:
        return
    try:
        main.uploadFile(filename,filepath,'text/csv')
    except:
        retries+=1
        tryAgain(retries)

# Liest die eben erstellte "start.txt" ein und speichert die Endzeit als Variable ab
# Die Erhebung läuft bis die momentane Zeit > der Endzeit ist. Die Daten des Sensors wird
# ein Zeitstempel gegeben und auf die Google Drive hochgeladen. Danach wird periodisch
# überprüft ob es eine neue "start.txt" Datei gibt.

if __name__ == "__main__":
    cmd_set_sleep(0)
    cmd_firmware_ver();
    cmd_set_working_period(PERIOD_CONTINUOUS);
    cmd_set_mode(MODE_QUERY);
    timex = 0 
    while True:
        if main.is_connected() == False:
            sleep(2)
            print('ex')
            continue
        with open('/home/pi/Desktop/start.txt') as f:
            cont = f.read()
        t_goal = cont.rsplit(",",1)[-1]
        t_goal = datetime.datetime.strptime(t_goal,"%Y-%m-%d %H:%M:%S.%f")
        t_now = datetime.datetime.now()
        if t_now > t_goal:
            if timex == 0:
                try:
                    cmd_set_sleep(1)
                except:
                    pass
            timex += 0.025
            print(timex)
            t_now = datetime.datetime.now()
            print(t_now)
            print(t_goal)
            print('waiting')
            with open('/home/pi/Desktop/start.txt') as f:
                cont = f.read()
            t_goal = cont.rsplit(",",1)[-1]
            t_goal = datetime.datetime.strptime(t_goal,"%Y-%m-%d %H:%M:%S.%f")
            sleep(10)
            continue
        
        if t_now < t_goal:
            
            timex = 0
            try:
                cmd_set_sleep(0)
            except:
                pass
            y=time.strftime("%Y%m%d-%H%M%S")
            filepath = '/home/pi/Desktop/data/' + str(y) + '_dust.csv'
            for t in range(7):
                x = datetime.datetime.now()
                values2=[]
                values = cmd_query_data();
                values2.append(values[0])
                values2.append(values[1])
                values2.append(x)
                with open(filepath, 'ab') as myfile:
                    wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
                    wr.writerow(values2)
                if values is not None and len(values) == 2:
                  print("PM2.5: ", values[0], ", PM10: ", values[1])
                  time.sleep(2)
            # open stored data
            try:
                with open(JSON_FILE) as json_data:
                    data = json.load(json_data)
            except IOError as e:
                data = []
            
            filename = str(y) + '_dust.csv'
            tryAgain()
            

            # check if length is more than 100 and delete first element
            if len(data) > 100:
                data.pop(0)

            # Hängt die Daten am ein json-file an
            jsonrow = {'pm25': values[0], 'pm10': values[1], 'time': time.strftime("%d.%m.%Y %H:%M:%S")}
            data.append(jsonrow)

            # speichert die Daten
            with open(JSON_FILE, 'w') as outfile:
                json.dump(data, outfile)

            if MQTT_HOST != '':
                pub_mqtt(jsonrow)
            t_now = datetime.datetime.now()
        



