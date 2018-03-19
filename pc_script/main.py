import serial
import threading
import csv
from serial.tools import list_ports
import matplotlib.pyplot as plt
import math
import numpy as np

pi=math.pi

helpdialog ="csv:write data to csv file\r\nexit:close this app\r\ndict:output data to console\r\nread:output raw serial input"

CSV_PATH='./out.csv'
BUFSIZE = 256
DEV_NAME = ''
BAUD_RATE = 115200
parameters = ['id', 'an0', 'an0_min', 'an0_max', 'an1', 'an1_min', 'an1_max']
WATCH_SER_PORT = False
STREAM_ON = True

def wavePlotter(ax,bufsize, x, y0, y1):

    #while 1:
    ax.cla()
    ax.plot(x,y0,marker = ',', linestyle = '-', color = '#fa4b00', label = 'an0')
    ax.plot(x, y1, marker=',', linestyle='-', color='#0b225d', label='an1')

    # x and y lables
    ax.set_title('Input Volt')
    ax.set_xlabel('Samples')
    ax.set_ylabel('[V]')
    ax.xaxis.label.set_color('#555555')
    ax.yaxis.label.set_color('#555555')

    # axis color
    ax.spines['top'].set_color('#555555')
    ax.spines['bottom'].set_color('#555555')
    ax.spines['left'].set_color('#555555')
    ax.spines['right'].set_color('#555555')
    ax.tick_params(axis = 'x', colors ='#555555')
    ax.tick_params(axis='y', colors='#555555')

    # legend color
    axlegend = ax.legend(loc = 2, frameon = True, fontsize = 'medium', fancybox = True, numpoints = 1)
    axlegend.get_frame().set_edgecolor('#CFCFCF')
    axlegend.get_frame().set_alpha(0.8)
    for axtext in axlegend.get_texts():
        axtext.set_color('#555555')

    # grid line
    ax.xaxis.grid(True, which = 'major', linestyle = ':', color = '#CFCFCF')
    ax.yaxis.grid(True, which = 'major', linestyle = '-', color = '#CFCFCF')
    ax.set_axisbelow(True)

    plt.pause(.01)

    #plt.show()

class serThread(threading.Thread):
    def __init__(self):
        super(serThread, self).__init__()
        self.input_line = ''
        self.dict = [[{'id':i,} for i in range(BUFSIZE)], [{'id':i,} for i in range(BUFSIZE)]] #Ping Pong Buffer
        self.pFlag = 0 #Ping Pong Buffer Flag
        self.ph_t = [0.0 for i in range(3)]
        self.watch_ser_port = False
        self.stream_on = True
    def run(self):
        count = 0
        while 1:
            if(self.stream_on):
                try:
                    self.input_line = ser.readline().decode().replace('\r\n', '')
                    if self.watch_ser_port:
                        print(self.input_line)
                    if self.input_line[0] != '#':
                        input_vals = self.input_line.split(',')
                        input_vals = [float(i) for i in input_vals]
                        count=int(input_vals[6])
                        ToDict = {'an0': input_vals[0], 'an0_min': input_vals[1], 'an0_max': input_vals[2], 'an1': input_vals[3], 'an1_min': input_vals[4], 'an1_max': input_vals[5]}
                        self.dict[self.pFlag][count].update(ToDict)
                        if count == int(BUFSIZE - 1):
                            if self.pFlag == 0:
                                self.pFlag = 1
                            elif self.pFlag == 1:
                                self.pFlag = 0
                    elif self.input_line[1] == 'p':
                        t_vals = self.input_line[3:].split(',')
                        for i in range(3):
                            self.ph_t[i] = t_vals[i]
                except:
                    pass

    def getData(self):#returns 256 sample data [{'id':0,'an0':0.1,'an1':0.4,...},{'id':1,...},{},...]
        if self.pFlag == 0:
            flag = 1
        elif self.pFlag == 1:
            flag = 0
        return self.dict[flag]
    
    def getPeakTime(self):#returns [an0 PeakTime[microsec],an1 PeakTime[mictosec],an0PeakT-an1PeakT[mictosec]]
        return self.ph_t

    def setWatchSerPort(self,flag):
        self.watch_ser_port = flag
    
    def setStreamFlag(self, flag):
        self.stream_on = flag
        

def findPort():
    try:
        uno = next(list_ports.grep("Arduino Uno"))
        print('Device Found:' + uno.device + ' ' + uno.product )
        dev_name = uno.device
        return dev_name
    except StopIteration:
        print('No device found')
        exit()

def outToCSV(rows):
    #print(rows)
    with open(CSV_PATH, 'w', newline='') as csvfile:
        fieldnames = parameters
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for d in rows:
            writer.writerow(d)

def calcFreq(data, period):
    # This Function From
    # http://www.contec-kb.com/wp/wp-content/uploads/2013/08/1355_syuhasu_kensyutu.pdf

    thold = 2.5
    all_cnt = 0
    k_mode = 0
    up1_cnt = 0
    dw_cnt = 0
    up2_cnt = 0
    finished = False
    samptm = 0.000001*period
    freq = 0.0

    while finished == False:
        all_cnt += 1
        if k_mode == 0:
            if data[all_cnt] < thold:
                k_mode = 1
        elif k_mode == 1:
            if data[all_cnt] >= thold:
                k_mode = 2
                up1_cnt = all_cnt
        elif k_mode == 2:
            if data[all_cnt] < thold:
                k_mode = 3
                dw_cnt = all_cnt
        elif k_mode == 3:
            if data[all_cnt] >= thold:
                k_mode = 4
                up2_cnt = all_cnt
        
        if(all_cnt >= (BUFSIZE - 1)) or (k_mode == 4):
            finished = True
            
    freq = 1 / ((up2_cnt - up1_cnt) * samptm)

    return freq

def calcPhaseDiff(diff_t, w_freq):
    w_period=float(1/w_freq)
    ph_diff_rad = float((diff_t / w_period) * 2 * pi)
    return ph_diff_rad

def antiailiasing(bufsize, s_data, s_period):
    #s_data:waveformdata,s_period:sampring period[s],freq_c:cut-off frequency[hz]
    freq_c = (10 ** 6) / (2 * s_period)
    s_period *= 0.000001
    print(str(s_data)+' '+str(s_period)+' '+str(freq_c))
    t = np.arange(0, bufsize * s_period, s_period)
    freq = np.linspace(0, 1.0 / s_period, bufsize)
    
    F = np.fft.fft(s_data)
    F = F / (bufsize / 2)
    F[0] = F[0] / 2
    F2 = F.copy()
    print(F2)
    F2[(freq > freq_c)] = 0
    print(F2)
    f2 = np.fft.ifft(F2)
    f2 = np.real(f2 * bufsize)
    return f2

if __name__ == '__main__':
    DEV_NAME = findPort()
    print("all commands for type \"help\"")
    ser = serial.Serial(DEV_NAME, BAUD_RATE)
    #ser.dtr = False


    period = 50
    #Plot
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot([i for i in range(BUFSIZE)],[0 for i in range(BUFSIZE)])
    lines,=ax.plot(0,0)

    serialListener = serThread()
    serialListener.setDaemon(True)
    serialListener.start()

    while 1:
        #Key input
        key = input()
        if key == 'csv': #write data to csv
            data = serialListener.getData()
            outToCSV(data)
        elif key == 'exit':#exit app
            exit()
        elif key == 'dict':#output dictionary data
            print(serialListener.getData())
        elif key == 'read':#output raw serial port data
            WATCH_SER_PORT = not(WATCH_SER_PORT)
            serialListener.setWatchSerPort(WATCH_SER_PORT)
        elif key == 'help':
            print(helpdialog)
        elif key == 'speriod':
            ser.write('6'.encode('utf-8'))
            period = int(input())
            if period >= 50:
                ser.write(str(period).encode('utf-8'))
            else:
                period = 50
                print('50[microsec] < period')
            print("sampling period set at" + str(period) + "[microsec]")
        elif key == 'ph':
            print(serialListener.getPeakTime())
        elif key == 'reset':
            ser.write('1'.encode('utf-8'))
        elif key == 'stream':
            STREAM_ON = not(STREAM_ON)
            serialListener.setStreamFlag(STREAM_ON)
            print('STREAMING:' + str(STREAM_ON))
        elif key == 'plot':
            try:
                data = serialListener.getData()
                #filterd = antiailiasing(BUFSIZE,[data[i]['an0'] for i in range(BUFSIZE)], period)
                #wavePlotter(ax, BUFSIZE, [i for i in range(BUFSIZE)], filterd, [2.5 for i in range(BUFSIZE)])
                wavePlotter(ax,BUFSIZE, [i for i in range(BUFSIZE)], [data[i]['an0'] for i in range(BUFSIZE)], [data[i]['an1'] for i in range(BUFSIZE)])
            except:
                print("No data Wait a minute...")
        elif key == 'f':
            try:
                data=serialListener.getData()
                freq = calcFreq([data[i]['an0'] for i in range(BUFSIZE)], period)
                print(format(freq, '.2f') + '[Hz]' + format(1 / freq) + '[s]')
                t = serialListener.getPeakTime()
                ph_d_rad = calcPhaseDiff(float(t[2]), freq)
                print(format(ph_d_rad,'.2f')+'[rad]')
            except:
                print("No data Wait a minute...")
        key = ''
