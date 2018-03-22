#include <TimerOne.h>
#include <stdlib.h>
#define MAX_V 5.0 //Arduino UNO MAX input Voltage
#define BUFSIZE 256 //BufferSize
#define TRIG_Volt 2.5 //Trigger Voltage
#define TRIG_LV (int)((float)1023*(float)((float)TRIG_Volt/(float)5.0)) //Trigger Level 0-1023
#define BAUD 115200//Baudrate

long period = 50;//sampling period [micro sec]
int an0 = 0; //an0 value 0-1023
int an1 = 0; //an1 value 0-1023

int val0[BUFSIZE]; //sample data from an0
int val1[BUFSIZE]; //sample date from an1

int count = 0; //index counter
bool Lv_Shifted = false;//Enable/Disable LevelShift for Negative Voltage(True:Need a Additional Circuit)

bool finished = false;//Flag:if sample count == 256 ->true
bool showScope = true;//true:send all waves to serial

void sendWave(int* d, int* d1, int n) {//send A/D data to serial 'an0[V],an1[V],index number(0-255)'
  for (int i = 0; i < n; i++) {
    //A0
    Serial.print(idx2Volt(d[i]));
    Serial.print(",");

    //A2
    Serial.print(idx2Volt(d1[i]));
    Serial.print(",");
    
    //id
    Serial.println(i);
    
  }
}


void timerFire() {//sampling Interrupt every Timer1 period
  digitalWrite(13, HIGH);//Debug Pin (Sampling Frequency) when arduino is sampling,13 pin turns ON.
  an0 = analogRead(A0);//Reads the analog value on pin A0 into an0
  an1 = analogRead(A2);//Reads the analog value on pin A2 into an1

  if (count < BUFSIZE) {
    val0[count] = an0;//collect data
    val1[count] = an1;
    count++;
  } else {//if counter reached to BUFSIZE
    finished = true;
  }
  digitalWrite(13, LOW);//Debug Pin
}

float idx2Volt(int d) {//index data(0-1023) to volt([V])
  float measuredVal = ((float)d / (float)1023) * (float)MAX_V;//idx To Voltage
  if (Lv_Shifted == true) {//LevelShift Enabled?
    measuredVal = 2.0 * measuredVal - MAX_V;//LevelShift
  }
  return measuredVal;
}

void resetDev() {//reset all settings
  count = 0;
  Timer1.setPeriod(50);
  return;
}

void setSampRate() {//variable sampling rate

  String in;
  //Timer1.stop();
  //Serial.println("#Stopped");
  Serial.println("#SamplingPeriod?");
  while (Serial.available() == 0);//wait for input
  in = Serial.readString();//input to string
  period = in.toInt();//string to long(int)
  Serial.print("#Started@");
  Serial.print(period);
  Serial.print("[microsec]/");
  Serial.print(((float)1 / (float)period) * 1000000);
  Serial.println("[Hz]");
  count = 0;
  //Timer1.initialize(period);//microseconds
  Timer1.setPeriod(period);//set Timer1 Period
  //Timer1.start();
  return;
}

void setup() {

  //Fast ADC Register settings
  ADCSRA = ADCSRA & 0xf8;
  ADCSRA = ADCSRA | 0x04;

  //put your setup code here, to run once:

  //ADC Specifications---
  //0-1023 int
  //Min 0V-Max 5V
  //so 0 means 0V,1023 means 5V
  //---------------------

  Serial.begin(BAUD); //baud rate is 115200 baud(USB Serial)
  pinMode(A0, INPUT); //A0 Port(Analog 0) is INPUT
  pinMode(A2, INPUT); //A2 Port(Analog 2) is INPUT
  pinMode(13, OUTPUT);//pin 13 is Digital OUT
  digitalWrite(13, LOW); //set Digital pin 13 LOW

  Timer1.initialize(period);//50 microseconds period(20kHz)
  Timer1.setPeriod(period);
  Timer1.attachInterrupt(timerFire);//Timer Triggers Function(timerFire)
  Timer1.start();//Timer1 start
  Serial.print("#BUFSIZE");
  Serial.println(BUFSIZE);
}

void loop() {
  //put your main code here, to run repeatedly:

  int inputchar;//serial input (1character)

  inputchar = Serial.read();//Read from SerialPort (1character)

  if (inputchar != -1 ) { //something received

    switch (inputchar) {
      case '1'://reset
        //received "1"
        resetDev();
        Serial.println("#Reset");
        break;
      case '2'://toggle lvshift
        //received "2"
        Lv_Shifted = !Lv_Shifted;
        if (Lv_Shifted == true) {
          Serial.println("#LvShift:ON");
        } else {
          Serial.println("#LvShift:OFF");
        }
        break;
      case '5':
        //received "5"
        showScope = !showScope;
        if (showScope == true) {
          Serial.println("#Wave:ON");
        } else {
          Serial.println("#Wave:OFF");
        }
        break;
      case '6'://update sampling rate
        setSampRate();
    }
  }

  if (finished == true) {
    Timer1.stop();

    //Serial.print("Stopped");
    //Serial.println(count);

    if (showScope) {
      sendWave(val0, val1, BUFSIZE);
    }

    delay(1000);

    //Serial.println("Started");

    finished = false;
    count = 0;
    Timer1.start();
  }

  delay(1000);
}

