import smtplib
import yagmail
import keyring
import os 
import sys
from datetime import datetime, timedelta
os.chdir(os.path.dirname(sys.argv[0]))

# sendet Email mit dem Inhalt (start, startzeit) an unsere Gmail Email Adresse
# Simple Mail Transfer Protokoll 
def send(argument,t):
    yag = yagmail.SMTP('signalauswertung2020@gmail.com', oauth2_file="oauth2_creds.json")
    yag.send(subject="start", contents=argument + ',' + t)
    t_start = datetime.now()
    t_goal = t_start + timedelta(minutes = (int(t) + 2))
    return t_goal
