import serial
import threading
import csv
from serial.tools import list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

helpdialog ="csv:write data to csv file\r\nexit:close this app\r\ndict:output data to console\r\nread:output raw serial input"

CSV_PATH='./out.csv'
BUFSIZE = 256
DEV_NAME = ''
BAUD_RATE = 115200
parameters = ['id', 'an0', 'an0_min', 'an0_max', 'an1', 'an1_min', 'an1_max']
WATCH_SER_PORT = False
STREAM_ON = True

def wavePlotter(bufsize, x, y0, y1):
    fig = plt.figure()
    ax=fig.add_subplot(111)
    #ax.cla()
    ax.plot(x,y0,marker = '.', linestyle = '-', color = '#fa4b00', label = 'an0')
    ax.plot(x, y1, marker='.', linestyle='-', color='#0b225d', label='an1')

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

    plt.show()




class serThread(threading.Thread):
    def __init__(self,valdict,phase_t,toPLT,updated):
        super(serThread, self).__init__()
        self.input_line = ''
        self.dict = valdict
        self.comms = ''
        self.ph_t = phase_t
        self.toPLT = toPLT
        self.updated = updated
    def run(self):
        tmpdict=self.dict.copy()
        count = 0
        while 1:
            if(STREAM_ON):
                try:
                    self.input_line = ser.readline().decode().replace('\r\n', '')
                    if WATCH_SER_PORT:
                        print(self.input_line)
                    if self.input_line[0] != '#':
                        self.updated = False
                        input_vals = self.input_line.split(',')
                        input_vals = [float(i) for i in input_vals]
                        count=int(input_vals[6])
                        ToDict = {'an0': input_vals[0], 'an0_min': input_vals[1], 'an0_max': input_vals[2], 'an1': input_vals[3], 'an1_min': input_vals[4], 'an1_max': input_vals[5]}
                        toPLT[0][count] = input_vals[0]
                        toPLT[1][count] = input_vals[3]
                        tmpdict[count].update(ToDict)
                        if count == int(BUFSIZE - 1):
                            self.dict = tmpdict.copy()
                            self.updated = True
                    elif self.input_line[1] == 'p':
                        t_vals = self.input_line[3:].split(',')
                        for i in range(3):
                            self.ph_t[i] = t_vals[i]
                except:
                    pass

def findPort():
    try:
        uno = next(list_ports.grep("Arduino Uno"))
        print('Device Found:'+ uno.device )
        DEV_NAME = uno.device
        return DEV_NAME
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

if __name__ == '__main__':
    DEV_NAME=findPort()
    print("all commands for type \"help\"")
    valdict = [{'id':i,} for i in range(BUFSIZE)]
    phase_t = [0.0 for i in range(3)]
    ser = serial.Serial(DEV_NAME, BAUD_RATE)
    #ser.dtr = False

    DRAW_REF = False
    toPLT = [[i for i in range(BUFSIZE)], [i for i in range(BUFSIZE)]]

    #ani = animation.FuncAnimation(fig, wavePlotter, interval=100,fargs=(ax,BUFSIZE,[i for i in range(BUFSIZE)], toPLT[0], toPLT[1]))



    #drawHandler = drawThread(BUFSIZE, toPLT[0], toPLT[1], DRAW_REF)
    #drawHandler.setDaemon(True)
    #drawHandler.start()

    serialListener = serThread(valdict,phase_t,toPLT,DRAW_REF)
    serialListener.setDaemon(True)
    serialListener.start()

    while 1:
        #Key input
        key = input()
        if key == 'csv':#write data to csv
            #print(valdict)
            outToCSV(serialListener.dict)
        elif key == 'exit':#exit app
            exit()
        elif key == 'dict':#output dictionary data
            print(serialListener.dict)
        elif key == 'read':#output raw serial port data
            WATCH_SER_PORT = not(WATCH_SER_PORT)
        elif key == 'help':
            print(helpdialog)
        elif key == 'speriod':
            ser.write('6'.encode('utf-8'))
            period = int(input())
            if period >= 50:
                ser.write(str(period).encode('utf-8'))
            else:
                period = 50
                print('50[mictosec]<period')
            print("sampling period set at" + str(period) + "[microsec]")
        elif key == 'ph':
            print(phase_t)
        elif key == 'reset':
            ser.write('1'.encode('utf-8'))
        elif key == 'stream':
            STREAM_ON = not(STREAM_ON)
            print('STREAMING:' + str(STREAM_ON))
        elif key == 'plot':
            print('notice:no commands while showing plot')
            wavePlotter(BUFSIZE,[i for i in range(BUFSIZE)], toPLT[0], toPLT[1])
        key = ''
