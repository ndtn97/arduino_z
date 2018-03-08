#include <TimerOne.h>
#define MAX_V 5.0 //Arduino UNO MAX input Voltage
#define TRIG_Volt 2.5 //Trigger Voltage
#define TRIG_LV (int)((float)1023*(float)((float)TRIG_Volt/(float)5.0)) //Trigger Level 0-1023
#define BAUD 9600


int an0 = 0; //an0 value
int an1 = 0; //an1 value
int peak_an0[2];//peak of an0 value [0]:min [1]:max
int peak_an1[2];//peak of an1 value [0]:min [1]:max
bool Lv_Shifted = false;

void timerFire() {
  digitalWrite(13, HIGH);//Debug Pin (Sampling Frequency) when arduino is sampling,13 pin turns ON.
  an0 = analogRead(A0);//Reads the analog value on pin A0 into an0
  an1 = analogRead(A2);//Reads the analog value on pin A2 into an1

  if (an0 < peak_an0[0]) {
    peak_an0[0] = an0;
  } else if (an0 > peak_an0[1]) {
    peak_an0[1] = an0;
  }
  if (an1 < peak_an1[0]) {
    peak_an1[0] = an1;
  } else if (an1 > peak_an1[1]) {
    peak_an1[1] = an1;
  }

  digitalWrite(13, LOW);//Debug Pin
}

float idx2Volt(int d) {
  float measuredVal = ((float)d / (float)1023) * (float)MAX_V;
  if (Lv_Shifted == true) {
    measuredVal = 2.0 * measuredVal - MAX_V;
  }
  return measuredVal;
}
void resetPeak() {
  peak_an0[0] = 1023; //peak min reset
  peak_an0[1] = 0; //peak max reset
  peak_an1[0] = 1023; //peak min reset
  peak_an1[1] = 0; //peak max reset
  return;
}

void sendPeak() {
  //A0
  Serial.print(idx2Volt(peak_an0[0]));//min
  Serial.print(",");
  Serial.print(idx2Volt(peak_an0[1]));//max
  Serial.print(",");
  //A2
  Serial.print(idx2Volt(peak_an1[0]));//min
  Serial.print(",");
  Serial.println(idx2Volt(peak_an1[1]));//max

  return;
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

  Serial.begin(BAUD); //baud rate is 115200 baud(USB Serial)
  pinMode(A0, INPUT); //A0 Port(Analog 0) is INPUT
  pinMode(A2, INPUT); //A2 Port(Analog 1) is INPUT
  pinMode(13, OUTPUT);//13 is Digital OUT
  digitalWrite(13, LOW); //set Digital pin 13 LOW
  resetPeak();//Peak reset
  Timer1.initialize(50);//50 microseconds period(20kHz)
  Timer1.attachInterrupt(timerFire);//Timer Triggers Function(timerFire)
  Timer1.start();//Timer1 start
  Serial.print("Started at TRIG_LV=");
  Serial.println(TRIG_LV);
}

void loop() {
  // put your main code here, to run repeatedly:

  int inputchar;//serial input (1character)

  inputchar = Serial.read();//Read from SerialPort (1character)

  if (inputchar != -1 ) { //something received

    switch (inputchar) {
      case '1':
        // received "1"
        resetPeak();
        Serial.println("Reset");
        break;
      case '2':
        // received "2"
        Lv_Shifted = !Lv_Shifted;
        if (Lv_Shifted == true) {
          Serial.println("LvShift:ON");
        } else {
          Serial.println("LvShift:OFF");
        }
    }
  }
  sendPeak();
  delay(1000);
}
