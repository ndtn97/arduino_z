#include <TimerOne.h>
#define MAX_V 5.0 //Arduino UNO MAX input Voltage
#define TRIG_Volt 2.5 //Trigger Voltage
#define TRIG_LV (int)((float)1023*(float)((float)TRIG_Volt/(float)5.0)) //Trigger Level 0-1023
#define BAUD 9600//Baudrate
#define R_I 20000.0//20k[ohm]


int an0 = 0; //an0 value
int an1 = 0; //an1 value
int peak_an0[2];//peak of an0 value [0]:min [1]:max
int peak_an1[2];//peak of an1 value [0]:min [1]:max
bool Lv_Shifted = false;//Enable/Disable LevelShift for Negative Voltage(True:Need a Additional Circuit)
bool showPeak = true;//Show Peak Val every 1000ms

float calcZ() {//calculation of Z
  float V1 = 0.0; //an0:Function Gen
  float V2 = 0.0; //an0-an1:V_R
  V1 = idx2Volt(peak_an0[1]);
  V2 = idx2Volt(peak_an0[1] - peak_an1[1]);
  if (V2 == 0.0) {
    Serial.print("error(devide by zero) ");
    return 0.0;
  } else {
    return (float)((float)V1 / (float)V2) * (float)R_I;
  }
}

void timerFire() {//sampling
  digitalWrite(13, HIGH);//Debug Pin (Sampling Frequency) when arduino is sampling,13 pin turns ON.
  an0 = analogRead(A0);//Reads the analog value on pin A0 into an0
  an1 = analogRead(A2);//Reads the analog value on pin A2 into an1

  if (an0 < peak_an0[0]) {//an0:MIN
    peak_an0[0] = an0;
  } else if (an0 > peak_an0[1]) { //an0:MAX
    peak_an0[1] = an0;
  }
  if (an1 < peak_an1[0]) {//an1:MIN
    peak_an1[0] = an1;
  } else if (an1 > peak_an1[1]) {//an1:MAX
    peak_an1[1] = an1;
  }

  digitalWrite(13, LOW);//Debug Pin
}

float idx2Volt(int d) {//index data to volt
  float measuredVal = ((float)d / (float)1023) * (float)MAX_V;//idx To Voltage
  if (Lv_Shifted == true) {//LevelShift Enabled?
    measuredVal = 2.0 * measuredVal - MAX_V;//LevelShift
  }
  return measuredVal;
}

void resetPeak() {//reset arrays
  peak_an0[0] = 1023; //peak min reset
  peak_an0[1] = 0; //peak max reset
  peak_an1[0] = 1023; //peak min reset
  peak_an1[1] = 0; //peak max reset
  return;
}

void sendPeak() {
  //A0
  Serial.print(idx2Volt(peak_an0[0]));//an0:min
  Serial.print(",");
  Serial.print(idx2Volt(peak_an0[1]));//an0:max
  Serial.print(",");
  //A2
  Serial.print(idx2Volt(peak_an1[0]));//an0:min
  Serial.print(",");
  Serial.println(idx2Volt(peak_an1[1]));//an0:max

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
  //put your main code here, to run repeatedly:

  int inputchar;//serial input (1character)

  inputchar = Serial.read();//Read from SerialPort (1character)

  if (inputchar != -1 ) { //something received

    switch (inputchar) {
      case '1'://reset
        //received "1"
        resetPeak();
        Serial.println("Reset");
        break;
      case '2'://toggle lvshift
        //received "2"
        Lv_Shifted = !Lv_Shifted;
        if (Lv_Shifted == true) {
          Serial.println("LvShift:ON");
        } else {
          Serial.println("LvShift:OFF");
        }
        break;
      case '3'://calculate z
        //received "3"
        Serial.print(calcZ());
        Serial.println(" [ohm]");
        break;
      case '4'://show peak ON/OFF
        //reveived "4"
        showPeak = !showPeak;
        if (showPeak == true) {
          Serial.println("ShowPeakValue:ON");
        } else {
          Serial.println("ShowPeakValue:OFF");
        }
        break;
    }
  }
  if (showPeak) sendPeak();
  delay(1000);
}

