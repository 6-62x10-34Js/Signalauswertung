from __future__ import print_function
import httplib2
import os, io
import sys
from time import sleep
import socket
from datetime import datetime
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient.http import MediaFileUpload, MediaIoBaseDownload
import auth
os.chdir(os.path.dirname(sys.argv[0]))
import argparse


try:
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'credentials.json'
APPLICATION_NAME = 'Drive API Python Quickstart'
authInst = auth.auth(SCOPES,CLIENT_SECRET_FILE,APPLICATION_NAME)
credentials = authInst.getCredentials()

http = credentials.authorize(httplib2.Http())
drive_service = discovery.build('drive', 'v3', http=http)


# Ist der PC zur Drive verbunden

def is_connected(host='8.8.8.8',port=53, timeout = 3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect((host,port))
        return True
    except socket.error as ex:
        print(ex)
        return False

# Überprüft ob neue Dateien am Google Drive Server liegen, und deren Name und ID. 

def listFiles(size):
    results = drive_service.files().list(
        pageSize=size,fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    namen = ([d['name'] for d in items])
    result = ([d['id'] for d in items])
    namen = namen [:4]
    result = result[:4]
    return result, namen

# Läd die Inhalte der Drive herrunter basierend auf deren ID

def downloadFile(file_id,filename):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download in progress.")
    with open(filename,'wb') as f:
        fh.seek(0)
        f.write(fh.read())

# Filtert die herruntergeladenen Inhalte nach Dateinamen und somit auch nach Sensor

def filter(indexes, names):
    temprh_index = []
    temprh_names = []
    dust_index = []
    dust_names =[]
    for i,j in zip(indexes, names):
        if 'temprh' in j:
            temprh_index.append(i)
            temprh_names.append(j)
        if 'dust' in j:
            dust_index.append(i)
            dust_names.append(j)
    return temprh_index, temprh_names, dust_index, dust_names

# Läd die Dateien mit den Messwerten von der Google Drive, speichert und ordnet sie

def run(t_goal):    
    t_now = datetime.now()
    sleep(15)
    while True: 
        if is_connected() == False:
            sleep(2)
            continue
        sleep(10)
        result, namen = listFiles("10")
        if result: 
            try:
                temprh_index, temprh_names, dust_index, dust_names = filter (result, namen)
                filepath = 'C:/Users/lukas/OneDrive - Universität Graz/Dokumente/Studium/USW-NAWI-TECH/6. Semester/Signalauswertung/coding/Code_neu/data/temprh/' + temprh_names[0]
                downloadFile(temprh_index[0], filepath)
                filepath2 = 'C:/Users/lukas/OneDrive - Universität Graz/Dokumente/Studium/USW-NAWI-TECH/6. Semester/Signalauswertung/coding/Code_neu/data/dust/' + dust_names[0]
                downloadFile(dust_index[0], filepath2)
            except:
                pass
        if t_now > t_goal:
            sys.exit()
