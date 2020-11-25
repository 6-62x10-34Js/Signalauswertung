from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from time import sleep
import socket
import os
import sys
from datetime import datetime, timedelta
os.chdir(os.path.dirname(sys.argv[0]))
SCOPES = 'https://mail.google.com/'

# Erlaubt dem raspberry eine Email zu empfangen und zu lesen

def main():
    global res
    id_msg = 0
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('gmail', 'v1', http=creds.authorize(Http()))
    # Call the Gmail API to fetch INBOX
    results = service.users().messages().list(userId='me',labelIds = ['INBOX'], maxResults = 1).execute()
    messages = results.get('messages', [])
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        res = str((msg['snippet']))
        id_msg = str((msg['id']))
        print(str((msg['snippet'])))
    return id_msg,service,messages



def DeleteMessage(service, user_id, msg_id):
    try:
        service.users().messages().delete(userId=user_id, id=msg_id).execute()
    except:
        pass
    
def is_connected(host='8.8.8.8',port=53, timeout = 3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect((host,port))
        return True
    except socket.error as ex:
        print(ex)
        return False
    
# Solange du mit dem Email Server verbunden bist, check alle 10 Sekunden
# ob neue Emails eingegangen sind.

res = 0
while True:
    if is_connected() == False:
        sleep(2)
        continue
    if __name__ == '__main__':
        retries = 0
        if retries < 3:
            try:
                id_msg,service,messages = main()
            except:
                retries+=1
                continue
        
    if not messages:
        sleep(10)
        continue

# Wenn in der Email "start" steht wird die Datei "start.txt" auf den Desktop
# geschrieben, mit der momentanen Zeit und der Zielzeit im Inhalt. 
# Nachdem die Email ausgelesen wurde, wird sie wieder aus dem Posteingang gelöscht. 

    try:
        arg = res.rsplit(",",1)[0]
        if arg == "start":
            y=datetime.now()
            tx = datetime.now() + timedelta(minutes = int(res.rsplit(",",1)[-1]))
            t_max = datetime.now() + timedelta(minutes = 120)
            if tx > t_max:
                tx = t_max
            f = open('/home/pi/Desktop/start.txt',"wb")
            print(tx)
            now=str(y)
            goal=str(tx)
            f.write(now + ',' + goal)
            print('s')
            f.close()
    except:
        pass

    DeleteMessage(service,'me',id_msg)
    sleep(15)   
    

    
    