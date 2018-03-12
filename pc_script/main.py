import serial
import threading
import csv

CSV_PATH='./out.csv'
BUFSIZE = 256
DEV_NAME = '/dev/tty.usbmodem1411'
BAUD_RATE = 115200
parameters = ['id', 'an0', 'an0_min', 'an0_max', 'an1', 'an1_min', 'an1_max']

class serThread(threading.Thread):
    def __init__(self,input_line,valdict):
        super(serThread, self).__init__()
        self.input_line = ''
        self.input_now = False
        self.dict = valdict
        self.tmpdict = self.dict
    def run(self):
        count=0
        while 1:
            input_line = ser.readline().decode().replace('\r\n', '')
            if input_line[0] != '#':
                try:
                    input_vals = input_line.split(',')
                    input_vals = [float(i) for i in input_vals]
                    count=int(input_vals[6])
                    ToDict = {'an0': input_vals[0], 'an0_min': input_vals[1], 'an0_max': input_vals[2], 'an1': input_vals[3], 'an1_min': input_vals[4], 'an1_max': input_vals[5]}
                    self.tmpdict[count].update(ToDict)
                    if count == int(BUFSIZE - 1):
                        #print(self.tmpdict)
                        self.dict = self.tmpdict
                except:
                    pass


def outToCSV(rows):
    with open(CSV_PATH, 'w', newline='') as csvfile:
        fieldnames = parameters
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for d in rows:
            writer.writerow(d)



if __name__ == '__main__':
    valdict = [{'id':i,} for i in range(BUFSIZE)]
    ser = serial.Serial(DEV_NAME, BAUD_RATE)
    ser.dtr = False
    readLine = ser.readline()
    serialListener = serThread(readLine, valdict)
    serialListener.setDaemon(True)
    serialListener.start()
    ser.write(bytes('5', 'utf-8'))

    while 1:
        key = input()
        if key == 'csv':
            outToCSV(valdict)
        elif key == 'exit':
            exit()
        elif key == 'dict':
            print(valdict)
        key = ''
