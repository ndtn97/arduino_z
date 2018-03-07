#include <TimerOne.h>
#define MAX_V 5.0 //Arduino UNO MAX input Voltage
#define BUFSIZE 256 //BufferSize
#define TRIG_Volt 2.5 //Trigger Voltage
#define TRIG_LV (int)((float)1023*(float)((float)TRIG_Volt/(float)5.0)) //Trigger Level 0-1023


int an0 = 0; //an0 value
int an1 = 0; //an1 value
int peak_an0 = 0; //max of an0 value
int peak_an1 = 0; //max of an1 value
int val0[BUFSIZE];//sample data from an0
int val1[BUFSIZE];//sample data from an1
int count = 0;//index counter
bool finished = false;//Flag:if sample count == 256 ->true
bool triggerd = false;//Flag:if an0 == TRIG_LV ->true

void timerFire() {
  digitalWrite(13, HIGH);
  an0 = analogRead(A0);//Reads the analog value on pin A0 into an0
  an1 = analogRead(A2);

  if ((count == 0) && (an0 == TRIG_LV)) {
    triggerd = true;
    //Serial.println("Trigg");
  }

  if (count < BUFSIZE) {
    if (triggerd == true) {
      val0[count] = an0;
      val1[count] = an1;
      count++;
    }
  } else {
    triggerd = false;
    finished = true;
  }
  digitalWrite(13, LOW);
}

float idx2Volt(int d) {
  return ((float)d / (float)1023) * (float)MAX_V;
}

void sendWave(int* d, int* d1, int n) {
  for (int i = 0; i < n; i++) {
    Serial.print(idx2Volt(d[i]));
    Serial.print(",");
    Serial.println(idx2Volt(d1[i]));
  }
}

void setup() {

  //Fast ADC Register settings
  ADCSRA = ADCSRA & 0xf8;
  ADCSRA = ADCSRA | 0x04;

  // put your setup code here, to run once:

  //ADC Specifications---
  // 0-1023 int
  // Min 0V-Max 5V
  // so 0 means 0V,1023 means 5V
  //---------------------

  Serial.begin(9600); //baud rate is 115200 baud(USB Serial)
  pinMode(A0, INPUT); //A0 Port(Analog 0) is INPUT
  pinMode(A2, INPUT); //A2 Port(Analog 1) is INPUT
  pinMode(13, OUTPUT);//13 is Digital OUT
  digitalWrite(13, LOW); //set Digital pin 13 LOW
  Timer1.initialize(50);//50 microseconds period(20kHz)
  Timer1.attachInterrupt(timerFire);//Timer Triggers Function(timerFire)
  Timer1.start();//Timer1 start
  Serial.print("Started at TRIG_LV=");
  Serial.println(TRIG_LV);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (finished == true) {
    Timer1.stop();
    
    //Serial.print("Stopped");
    //Serial.println(count);
    
    sendWave(val0, val1, BUFSIZE);
    
    //Serial.println("Started");
    
    finished = false;
    count = 0;
    Timer1.start();
  }
  //Serial.println(idx2Volt(peak_an0));//Send a value to SerialMonitor
}
