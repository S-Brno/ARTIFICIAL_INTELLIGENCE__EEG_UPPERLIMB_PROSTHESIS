from PyQt5 import QtWidgets
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.dockarea import *
import sys, time, pyqtgraph as pg, numpy as np

class Window_Insight(QtWidgets.QMainWindow):
    
    def __init__(self, opc, filename, save, start, channel, mathplot, range, sensors, tempo, *args, **kwargs):
        
        self.app = QtGui.QApplication(sys.argv)                       # Application Object (pass arguments) 
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)  # Inherit Qt parent funciton (init)
        
        self.count     = 0
        self.delimiter = ";"
        self.filename  = filename
        self.opc       = opc
        self.save      = save
        self.start     = start
        self.channel   = channel
        self.mathplot  = mathplot
        self.range     = range
        self.sensors   = sensors
        self.tmp       = tempo
        self.fft_abs   = { "AF3":[], "T7":[], "Pz":[], "T8":[], "AF4":[] }
        
        self.area     = DockArea()
        self.docks = {}
        self.line = {}

        for sensor_name in self.sensors:
            self.docks["dock_" + sensor_name] = Dock(sensor_name) 
            self.area.addDock(self.docks["dock_" + sensor_name], 'bottom')

        
        self.pen      = { "AF3":pg.mkPen(color=(255, 0, 0)),  \
                          "T7" :pg.mkPen(color=(0, 0, 255)),  \
                          "Pz" :pg.mkPen(color=(0,128, 0)),   \
                          "T8" :pg.mkPen(color=(128, 0,128)), \
                          "AF4":pg.mkPen(color=(255,125, 0)) 
                          }
        self.widget   = { "AF3": pg.PlotWidget(), "T7": pg.PlotWidget(), "Pz": pg.PlotWidget(), "T8": pg.PlotWidget(), "AF4": pg.PlotWidget() }
        
        if self.opc == 2:
            self.read_file()
        
        for sensor_name in self.sensors:
            self.line[sensor_name] = self.widget[sensor_name].plot(x=self.tmp, y=self.channel[sensor_name], pen=self.pen[sensor_name])
            self.widget[sensor_name].plotItem.showGrid(x=True, y=True)
            self.widget[sensor_name].setBackground('w')
            self.widget[sensor_name].setScale(1)
            self.widget[sensor_name].setMouseEnabled(x=False, y=False)
            self.docks["dock_" + sensor_name].addWidget(self.widget[sensor_name])

            if self.opc == 2:
                
                if self.mathplot == 1:

                    self.widget[sensor_name].setYRange(2000, 2400, padding=0.2)

                elif self.mathplot == 2:
                    
                    self.widget[sensor_name].setYRange(min(self.channel[sensor_name]), max(self.channel[sensor_name]), padding=0.2)
            
                    #Ajustar escala do eixo Y manualmente
                    """self.widget['AF3'].setYRange(min(self.channel["AF3"]) , max(self.channel["AF3"]))
                    self.widget['T7'].setYRange(min(self.channel["T7"]) , max(self.channel["T7"]))
                    self.widget['Pz'].setYRange(min(self.channel["Pz"]), max(self.channel["Pz"]))
                    self.widget['T8'].setYRange(min(self.channel["T8"]), max(self.channel["T8"]))
                    self.widget['AF4'].setYRange(min(self.channel["AF4"]), max(self.channel["AF4"]))"""

                else:
                    break
            
        self.setCentralWidget(self.area)
        self.resize(900, 900)
        self.setWindowTitle('EEG data')
        self.graph_timer()
        self.show()
        
    def graph_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(8)
        self.timer.setInterval(8)

    def update_graph(self):

        for sensor_name in self.sensors:

            if self.mathplot == 1:
                self.line[sensor_name].setData(self.tmp[0:self.range], self.math_plot(self.channel[sensor_name][0:self.range]))
            
            elif self.mathplot == 2:
                self.line[sensor_name].setData(self.tmp[0:self.range], self.channel[sensor_name][0:self.range])
        
        if len(self.channel["AF3"]) > self.range or self.opc == 2:

            '''if len(self.channel["AF3"]) < 1:
                return 
           
            if len(self.channel["AF3"]) < 750:
                return'''
                
            self.channel["AF3"].pop(0)
            self.channel["T7"].pop(0)
            self.channel["Pz"].pop(0)
            self.channel["T8"].pop(0)
            self.channel["AF4"].pop(0)
            self.tmp.pop(0)      

    def m_plot(self, m):
        
        #print(str(len(m)))
        z = []
        for i,x in enumerate(m):
            z.append(x* .512)
        return z
        
    def math_plot(self, data_unit):
        return self.m_plot(data_unit)
        return list(map(lambda x: self.m_plot(data_unit), data_unit))
            
    def execute_graph(self):
        #sys.exit(self.show())
        sys.exit(self.app.exec_())
        
    def close_graph(self):
        self.app.closeAllWindows()
    
    def do_fft(self):
        L = len(self.cAF3)
        fft_sensor = { "AF3":[], "T7":[], "Pz":[], "T8":[], "AF4":[] }
        for sensor_name in self.sensors:
            fft_sensor[sensor_name] = np.array([]).astype(np.double)           # Create numpy array for double-precision.
            fft_sensor[sensor_name] = np.fft.fft(fft_sensor[sensor_name]) / L  # Divide FFT by Sample.
            self.fft_abs[sensor_name].append(abs(fft_sensor[sensor_name]))     # Append absolute of sensors FFT/L.
      
    def read_file(self):
        
        if ".csv" not in self.filename:           
            self.filename += ".csv"
        
        with open("datasets/" + self.filename, 'r') as f:
            data_csv = f.readlines() 
            data_csv.pop(0)  

            for linha in data_csv:
                e = linha.split(';')
                self.count += 1
      
                self.channel["AF3"].append(float(e[0]))
                self.channel["T7"].append( float(e[1]))
                self.channel["Pz"].append( float(e[2]))
                self.channel["T8"].append( float(e[3]))
                self.channel["AF4"].append(float(e[4]))
                self.tmp.append(float(e[5]))