import serial
import threading
import csv
from serial.tools import list_ports
import matplotlib.pyplot as plt
import math
import numpy as np

pi=math.pi

helpdialog ="csv:write data to csv file\nexit:close this app\ndict:output data to console\nread:output raw serial input\nplot:plot wave data with matplotlib"

CSV_PATH='./'
BUFSIZE = 256
DEV_NAME = ''
BAUD_RATE = 115200

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
    def __init__(self,serdev):
        super(serThread, self).__init__()
        self.ser = serdev
        self.input_line = ''

        #Ping Pong Buffer
        self.dict = [[{'id':i,} for i in range(BUFSIZE)], [{'id':i,} for i in range(BUFSIZE)]]
        self.pFlag = 0 #Ping Pong Buffer Flag

        self.watch_ser_port = False
        self.stream_on = True
    def run(self):
        count = 0
        while 1:
            if(self.stream_on):
                try:
                    self.input_line = self.ser.readline().decode().replace('\r\n', '')
                    if self.watch_ser_port:
                        print(self.input_line)
                    if self.input_line[0] != '#':#works only for data input
                        input_vals = self.input_line.split(',')
                        input_vals = [float(i) for i in input_vals]
                        count=int(input_vals[2])
                        ToDict = {'an0': input_vals[0],'an1': input_vals[1]}
                        self.dict[self.pFlag][count].update(ToDict)
                        if count == int(BUFSIZE - 1):#Ping Pong Buffer
                            if self.pFlag == 0:
                                self.pFlag = 1
                            elif self.pFlag == 1:
                                self.pFlag = 0
                except:
                    pass

    def getData(self):#returns 256 sample data [{'an0':0.1,'an1':0.4},{...},...]
        if self.pFlag == 0:
            flag = 1
        elif self.pFlag == 1:
            flag = 0
        return self.dict[flag]

    def setWatchSerPort(self,flag):#For Arduino Debug (Serial Monitor On/Off Flag)
        self.watch_ser_port = flag
    
    def setStreamFlag(self, flag):#Receive new data or not
        self.stream_on = flag

    def resetDict(self): #reset all data
        self.stream_on = False
        self.dict = [[{'id':i,} for i in range(BUFSIZE)], [{'id':i,} for i in range(BUFSIZE)]]
        self.stream_on = True 

def findPort():#Find Arduino UNO returns device path
    try:#Device Found
        uno = next(list_ports.grep("Arduino Uno"))
        print('Device Found:' + uno.device + ' ' + uno.product )
        dev_name = uno.device
        return dev_name
    except StopIteration:#Device Not Found
        print('No device found')
        exit()

def outToCSV(rows, parameters, filename): #List to CSV
    #rows:List data[{'an0':...,'an1':...},{},{},...] parameters:['an0','an1',...] filename:save filename

    #print(rows)
    with open(CSV_PATH + filename, 'w', newline='') as csvfile:
        fieldnames = parameters
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for d in rows:
            writer.writerow(d)
    print('Saved CSV as ' + filename)

def calcFreq(data, period): #calculate frequency and get Peak data
    #data=[1.2,1.3,...]<List> period:sampling period[micro sec]
    # This Function From
    # http://www.contec-kb.cpom/wp/wp-content/uploads/2013/08/1355_syuhasu_kensyutu.pdf

    thold = 2.5
    all_cnt = 0
    k_mode = 0
    up1_cnt = 0
    dw_cnt = 0
    up2_cnt = 0
    finished = False
    samptm = 0.000001*period #[microsec -> sec]
    freq = 0.0

    #Peak Values
    max_v=0.0
    max_idx=0

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

            #Peak(Max) detection
            if data[all_cnt] > max_v:
                max_v = data[all_cnt]
                max_idx = all_cnt

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

    return (freq,max_v,max_idx)#returns tupple (Frequency[Hz],Peak Volt[V],Peak Index(0-255))

def calcPhaseDiff(diff_t, w_freq): #calculate phase differential
    #diff_t:Time Differential of 2 waves w_freq:wave frequency
    w_period=float(1/w_freq)
    ph_diff_rad = float((diff_t / w_period) * 2 * pi)
    return ph_diff_rad #returns [rad]

def setPeriod(ser, period): #set sampling period of arduino
    ser.write('6'.encode('utf-8')) # '6' is setPeriod command for Arduino
    if period >= 50:
        ser.write(str(int(period)).encode('utf-8'))
        print("sampling period set at" + str(period) + "[microsec]")
    else:
        print('50[microsec] < period')

def setReset(ser):#Reset Arduino
    ser.write('1'.encode('utf-8')) # '1' is resetDev command for Arduino

def plot(data): #Plot Data with matplotlib
    #data=[{'an0':1.2,'an1':3.5},{...},...]
    try:#if data exists
        wavePlotter(ax, BUFSIZE, [i for i in range(BUFSIZE)], [data[i]['an0'] for i in range(BUFSIZE)], [data[i]['an1'] for i in range(BUFSIZE)])
        return 0
    except:#if data not exists
        #print("No data Wait a minute...")
        return(-1)

def calcZ(V_R, V_S, R):#calculate |Z|
    I = float(V_R / R)
    V_Z = float(V_S - V_R)
    Z = float(V_Z / I)
    return Z


if __name__ == '__main__':
    DEV_NAME = findPort() #find Arduino Device and Get Address
    
    ser = serial.Serial(DEV_NAME, BAUD_RATE) #Define Serial Connection
    #ser.dtr = False

    period = 50 #Sampling Period Default 50 [micro sec]

    #Matplotlib Initialize
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot([i for i in range(BUFSIZE)],[0 for i in range(BUFSIZE)])
    lines,=ax.plot(0,0)

    #Initialize SerialListener (another thread)
    serialListener = serThread(ser) #setThread <class>
    serialListener.setDaemon(True) #Kill thread if main exit()
    serialListener.start() #Start thread

    mode = 'normal'

    #Mode Select 'noramal' or 'impedance measurement'
    key = input('Mode \'1\':normal mode \t\'2\':Impedance Measure...')
    if(key == '2'):
        mode = 'imp'
    else:
        print("all commands for type \"help\"")

    #impedance measurement
    if mode == 'imp':
        try:
            print('Frequency Range ?')
            low_fq = float(input('From[Hz]...'))
            high_fq = float(input('End[Hz]...'))
            df = float(input('df[Hz]...'))
        except:
            print('Input number please')
            exit()
        
        list_Freq = np.arange(low_fq, high_fq, df, 'float32')
        list_Freq = np.append(list_Freq,high_fq)
        print(list_Freq)
        result = [{} for i in list_Freq]
        cnt = 0
        go_next = False

        for FREQ in list_Freq:
            go_next = False
            while go_next == False:
                #Set Function Generator
                #add code here to control function generator
                #

                #Plot
                data = serialListener.getData()
                while plot(data) == -1:
                    data = serialListener.getData()

                #GetFreq Phase
                #data=serialListener.getData()
                freq0 = calcFreq([data[i]['an0'] for i in range(BUFSIZE)], period)
                freq1 = calcFreq([data[i]['an1'] for i in range(BUFSIZE)], period)
                print('an0:' + format(freq0[0], '.2f') + '[Hz]' + format(1 / freq0[0]) + '[s]')
                print('an1:' + format(freq1[0], '.2f') + '[Hz]' + format(1 / freq1[0]) + '[s]')
                #t = serialListener.getPeakTime()
                t=[freq0[2]*(period*0.000001),freq1[2]*(period*0.000001),(freq0[2]-freq1[2])*(period*0.000001)]
                ph_d_rad = calcPhaseDiff(float(t[2]), freq0[0])
                print(format(ph_d_rad, '.2f') + '[rad]')
                
                #Adjust Sampling Freq
                key = input('Wrong ? y/n(Default is n)...')
                if key == 'y':
                    try:
                        freq = float(input('Sampling Freq'))
                        period = (float)(1 / freq)#[s]
                        period = period * 10 ** 6 #[micro sec]
                        setPeriod(ser, period)
                    except:
                        print('No change')
                    #setReset(ser)
                    serialListener.resetDict()
                else:
                    #Get max Val
                    #freq0[1]:an0 Peak Volt[V],freq1[1]:an1 Peak Volt[V]
                    #Calculate Impedance
                    Z = calcZ(freq0[1], freq1[1], 20000.0) #IF an0 is V_R , an1 is V_S and R = 20k
                    tores = {'source[Hz]': FREQ, 'an0_f[Hz]': freq0[0], 'an1_f[Hz]': freq1[0], '|Z|[ohm]': Z, 'phase_diff[rad]': ph_d_rad}
                    result[cnt].update(tores)
                    #setReset(ser)
                    cnt += 1
                    go_next = True
                    serialListener.resetDict()
        
        #Output CSV
        parameters = ['source[Hz]', 'an0_f[Hz]', 'an1_f[Hz]', '|Z|[ohm]', 'phase_diff[rad]']
        outToCSV(result, parameters, 'impedance.csv')
        print('measurement end')
        #print(result)

    #normal
    while mode == 'normal':
        
        #Key input
        key = input()
        if key == 'csv': #write data to csv
            data = serialListener.getData()
            parameters = ['id', 'an0', 'an1']
            outToCSV(data,parameters,'wave.csv')
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
            period = int(input())
            setPeriod(ser, period)
        elif key == 'shz':
            freq = float(input())
            period = (float)(1 / freq)#[s]
            period = period * 10 ** 6 #[micro sec]
            setPeriod(ser,period)
        elif key == 'reset':
            setReset(ser)
        elif key == 'stream':
            STREAM_ON = not(STREAM_ON)
            serialListener.setStreamFlag(STREAM_ON)
            print('STREAMING:' + str(STREAM_ON))
        elif key == 'plot':
            data = serialListener.getData()
            plot(data)
        elif key == 'freq':
            try:
                data = serialListener.getData() #get data
                #Calculate frequency and print
                freq0 = calcFreq([data[i]['an0'] for i in range(BUFSIZE)], period)
                freq1 = calcFreq([data[i]['an1'] for i in range(BUFSIZE)], period)
                print('an0:' + format(freq0[0], '.2f') + '[Hz]' + format(1 / freq0[0]) + '[s]')
                print('an1:' + format(freq1[0], '.2f') + '[Hz]' + format(1 / freq1[0]) + '[s]')
                #Caclulate Phase differential using frequency and PeakTime
                t=[freq0[2]*(period*0.000001),freq1[2]*(period*0.000001),(freq0[2]-freq1[2])*(period*0.000001)]#Peak Time Data
                ph_d_rad = calcPhaseDiff(float(t[2]), freq0[0])#phase diffrential [rad]
                print(format(ph_d_rad, '.2f') + '[rad]')
            except:
                print("No data Wait a minute...")
        key = ''
