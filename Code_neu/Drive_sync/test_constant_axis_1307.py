from PyQt5.QtGui import*
from PyQt5.QtWidgets import*
from PyQt5.QtCore import*
import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import time
import os
import glob
from datetime import datetime
from datetime import timedelta
import random 



from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
import matplotlib.dates as mdates

''' hier den Pfad zum Ordner Code einfügen:'''
path = 'c:/Users/lukas/OneDrive - Universität Graz/Dokumente/Studium/USW-NAWI-TECH/6. Semester/Signalauswertung/coding/Code_neu/'


sys.path.insert(1, path + 'mail')
import sendEmail
sys.path.insert(1, path + 'Drive_sync')
import main

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd
from glob import iglob
from os.path import join


path_temprh = path + 'data/temprh'
def read_df_rec_temprh(path, fn_regex=r'*.csv'):
    return pd.concat((pd.read_csv(f,header=None,decimal='.',sep=",") for f in iglob(
        join(path, '**', fn_regex), recursive=True)), ignore_index=True)

path_dust = path + 'data/dust'
def read_df_rec_dust(path, fn_regex=r'*.csv'):
    return pd.concat((pd.read_csv(f,header=None,decimal='.',sep=",") for f in iglob(
        join(path, '**', fn_regex), recursive=True)), ignore_index=True)



class Worker(QRunnable):
    '''
    Worker thread
    '''
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.fn(*self.args, **self.kwargs)
 

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = "Messung für Feinstaub PM2.5, PM10, Temperatur und Luftfeuchte"
        self.x = 0
        self.y = 0
        self.width = 1920
        self.height = 1080
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.x, self.y, self.width, self.height)
        self.MyUI()

        self.start.clicked.connect(self.exec_Start) 
        self.stop.clicked.connect(self.exec_Stop)
        
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())


    def MyUI(self):
        self.stop = QPushButton("Stop", self)
        self.stop.setGeometry(QRect(170, 100, 100, 28))
        self.stop.clicked.connect(self.exec_Stop)
        
        self.start = QPushButton("Start", self)
        self.start.setGeometry(QRect(40, 100, 100, 28))
        _translate = QCoreApplication.translate
        self.start.setShortcut(_translate("QMainWindow", "Return"))

        self.messdauer = QLineEdit(self)
        self.messdauer.setGeometry(QRect(120, 60, 31, 22))
        self.messdauer.setInputMask("999")
        self.messdauer.setText("")
        self.messdauer.setMaxLength(3)
        self.messdauer.setFrame(True)
        self.messdauer.setCursorPosition(0)

        self.description = QLineEdit("Messdauer:", self)
        self.description.setGeometry(QRect(40, 60, 80, 22))
        self.description.setReadOnly(True)
        self.description.setFrame(False)
        self.description.setStyleSheet("QLineEdit { background: rgb(240, 240, 240)}")
        
        self.description2 = QLabel(self)
        self.description2.setGeometry(QRect(170, 60, 300, 22))
        self.description2.setText("Minuten (mögliche Werte: 0-120 min)")
        
        self.label1 = QLabel(self)
        self.label1.setGeometry(QRect(40, 10, 800, 40))
        self.label1.setText("Die Messungen der Feinstaubwerte, der Temperatur und der Luftfeuchte werden hier live geplottet. \nBitte gewünschte Messdauer in Minuten eingeben.")
        

        self.graph_pm25 = Canvas_PM25(self)
        self.graph_pm25.setGeometry(QRect(10, 170, 550, 400))
    
        self.graph_pm10 = Canvas_PM10(self)
        self.graph_pm10.setGeometry(QRect(10, 570, 550, 400))

        self.graph_luftfeuchte = Canvas_luftfeuchte(self)
        self.graph_luftfeuchte.setGeometry(QRect(560, 170, 550, 400))

        self.graph_temperatur = Canvas_temperatur(self)
        self.graph_temperatur.setGeometry(QRect(560, 570, 550, 400))
        
        font = QFont("Arial", 14, QFont.Bold)

        self.output_luftfeuchte = QLineEdit(self)
        self.output_luftfeuchte.setFrame(False)
        self.output_luftfeuchte.setGeometry(QRect(900,195,100,50))
        self.output_luftfeuchte.setFont(font)

        self.output_temperatur = QLineEdit(self)
        self.output_temperatur.setFrame(False)
        self.output_temperatur.setGeometry(QRect(900,595,100,50))
        self.output_temperatur.setFont(font)

        self.output_pm25 = QLineEdit(self)
        self.output_pm25.setFrame(False)
        self.output_pm25.setGeometry(QRect(350,195,100,50))
        self.output_pm25.setFont(font)

        self.output_pm10 = QLineEdit(self)
        self.output_pm10.setFrame(False)
        self.output_pm10.setGeometry(QRect(350,595,100,50))
        self.output_pm10.setFont(font)
        
    def get_measuretime(self):
        return self.messdauer.text()

    def Start(self):
        measuretime = self.messdauer.text()
        t_goal = sendEmail.send('start',measuretime)
        for filename in os.listdir(path_temprh):
            os.remove(os.path.join(path_temprh, filename))
        for filename in os.listdir(path_dust):
            os.remove(os.path.join(path_dust, filename))
        main.run(t_goal)

    def exec_Start(self):
        worker1 = Worker(self.Start)
        worker2 = Worker(self.update_plot_temprh)
        worker3 = Worker(self.update_plot_dust)
        self.threadpool.start(worker1)
        print("worker1 active")
        self.threadpool.start(worker2)
        print("worker2 active")
        self.threadpool.start(worker3)
        print("worker3 active")

    def Stop(self):
        sendEmail.send('start','0')

    def exec_Stop(self):
        worker4 = Worker(self.Stop)
        self.threadpool.start(worker4)
        time.sleep(2)

  
    def update_plot_temprh(self):
        path1 = path + 'data/temprh/*'
        r = glob.glob(path1)
        for i in r:
            os.remove(i)
        time.sleep(30)
        now = datetime.now()
        print(now)
        upper=now + timedelta(minutes=int(self.messdauer.text()))
        minutes = mdates.MinuteLocator()   # every year
        seconds = mdates.SecondLocator(bysecond=range(0, 60, 1), interval=15)
        self.graph_luftfeuchte.axes.set_xlim(now,upper)
        self.graph_luftfeuchte.axes.set_ylim(0,100)
        self.graph_luftfeuchte.axes.xaxis.set_tick_params(rotation=45)
        self.graph_temperatur.axes.set_xlim(now,upper)
        self.graph_temperatur.axes.set_ylim(0,40)
        self.graph_temperatur.axes.xaxis.set_tick_params(rotation=45)
        while True:
            # Drop off the first y element, append a new one.
            path_temprh = path + 'data/temprh/'
            self.df1 = read_df_rec_temprh(path_temprh)
            self.df1.columns = ["Luftfeuchte","Temperatur","Zeit"]
            self.df1.Zeit = pd.to_datetime(self.df1.Zeit, format="%Y-%m-%d %H:%M:%S.%f") 
            self.df1 = self.df1[self.df1.Zeit >= now]
            self.xdata_df1 = self.df1.Zeit
            self.ydata_luftfeuchte = self.df1.Luftfeuchte
            self.ydata_temperatur = self.df1.Temperatur

            #self.graph_luftfeuchte.axes.cla()  # Clear the canvas.
            self.graph_luftfeuchte.axes.plot(self.xdata_df1, self.ydata_luftfeuchte, 'r')

            #self.graph_temperatur.axes.cla()  # Clear the canvas.
            self.graph_temperatur.axes.plot(self.xdata_df1, self.ydata_temperatur, 'r')
            
            # Trigger the canvas to update and redraw.
            self.graph_luftfeuchte.draw()
            self.graph_temperatur.draw()
            try:
                luftfeuchte_value = str(self.df1.Luftfeuchte.iloc[-1])
                temperatur_value = str(self.df1.Temperatur.iloc[-1])
                self.output_luftfeuchte.setText(luftfeuchte_value + "%")
                self.output_temperatur.setText(temperatur_value + "°C")
            except:
                pass
            time.sleep(4)

            print("drawing")

    def update_plot_dust(self):
        path2 = path + 'data/dust/*'
        r = glob.glob(path2)
        for i in r:
            os.remove(i)
        time.sleep(30)
        now = datetime.now()
        upper=now + timedelta(minutes=int(self.messdauer.text()))
        self.graph_pm25.axes.set_xlim(now,upper)
        self.graph_pm25.axes.set_ylim(0,10)
        self.graph_pm25.axes.xaxis.set_tick_params(rotation=45)
        self.graph_pm10.axes.set_xlim(now,upper)
        self.graph_pm10.axes.set_ylim(0,50)
        self.graph_pm10.axes.xaxis.set_tick_params(rotation=45)
        while True:
            # Drop off the first y element, append a new one.
            path_dust = path + 'data/dust/'
            self.df = read_df_rec_dust(path_dust)
            self.df.columns = ["PM25","PM10","Zeit"]
            self.df.Zeit = pd.to_datetime(self.df.Zeit, format="%Y-%m-%d %H:%M:%S.%f") 
            self.df = self.df[self.df.Zeit >= now]
            self.xdata = self.df.Zeit
            self.ydata_pm25 = self.df.PM25
            self.ydata_pm10 = self.df.PM10

            #self.graph_pm25.axes.cla()  # Clear the canvas.
            self.graph_pm25.axes.plot(self.xdata, self.ydata_pm25, 'r')

            #self.graph_pm10.axes.cla()  # Clear the canvas.
            self.graph_pm10.axes.plot(self.xdata, self.ydata_pm10, 'r')
            # Trigger the canvas to update and redraw.
            self.graph_pm25.draw()
            self.graph_pm10.draw()
            try:
                pm25_value = str(self.df.PM25.iloc[-1])
                pm10_value = str(self.df.PM10.iloc[-1])
                self.output_pm25.setText(pm25_value + "ppm")
                self.output_pm10.setText(pm10_value + "ppm")
            except:
                pass 
            time.sleep(4)
        
     
        
class Canvas_PM25(FigureCanvas):
    def __init__(self, parent = None, width = 5, height = 5, dpi = 100):
        self.fig = Figure(figsize=(width, height), dpi=dpi,tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_ylabel("gemessene PM25 Partikel in ppm", size = 8, style = 'italic')
        self.axes.set_xlabel("Zeit", size = 8, style = 'italic')
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
 
class Canvas_PM10(FigureCanvas):
    def __init__(self, parent = None, width = 5, height = 5, dpi = 100):
        self.fig = Figure(figsize=(width, height), dpi=dpi,tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_ylabel("gemessene PM10 Partikel in ppm", size = 8, style = 'italic')
        self.axes.set_xlabel("Zeit", size = 8, style = 'italic')

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
 
class Canvas_luftfeuchte(FigureCanvas):
    def __init__(self, parent = None, width = 5, height = 5, dpi = 100):
        self.fig = Figure(figsize=(width, height), dpi=dpi,tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_ylabel("gemessene Luftfeuchte in %", size = 8, style = 'italic')
        self.axes.set_xlabel("Zeit", size = 8, style = 'italic')

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

class Canvas_temperatur(FigureCanvas):
    def __init__(self, parent = None, width = 5, height = 5, dpi = 100):
        self.fig = Figure(figsize=(width, height), dpi=dpi,tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_ylabel("gemessene Temperatur in °C", size = 8, style = 'italic')
        self.axes.set_xlabel("Zeit", size = 8, style = 'italic')

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)


app = QApplication(sys.argv)
window = Window()
window.show()
#app.exec()
sys.exit(app.exec_())